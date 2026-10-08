#!/usr/bin/env python3
"""Read-only prerequisite checks. Never installs, repairs, or restarts anything."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys


class CheckFailure(Exception):
    def __init__(self, status, detail):
        self.status, self.detail = status, detail


def require(condition, status, detail):
    if not condition:
        raise CheckFailure(status, detail)


def path_value(value):
    require(isinstance(value, str) and bool(value), 'unverified', 'Missing path input')
    require(not re.search(r'\$|[<>]', value), 'unverified', 'Resolve path placeholders before checking')
    return Path(value).expanduser()


def execute(arguments, timeout):
    try:
        result = subprocess.run(arguments, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError as error:
        raise CheckFailure('missing', str(error))
    except (PermissionError, subprocess.TimeoutExpired, OSError) as error:
        raise CheckFailure('unverified', str(error))
    require(result.returncode == 0, 'unverified', (result.stdout+result.stderr)[-2000:] or f'Exit {result.returncode}')
    return result.stdout+result.stderr


def executable(value):
    require(isinstance(value, str) and bool(value), 'unverified', 'Missing executable name')
    require(not re.search(r'\$|[<>]', value), 'unverified', 'Resolve executable placeholders')
    found = shutil.which(value)
    require(found is not None, 'missing', f'Executable not found: {value}')
    return found


def remote(check, command, timeout):
    target = check.get('target')
    require(isinstance(target, str) and bool(target) and not re.search(r'\$|[<>]', target), 'unverified', 'Explicit current HDC target is required')
    hdc = executable(check.get('hdc', 'hdc'))
    # Sentinel checks the remote shell status as HDC exit status can be misleading.
    wrapped = '('+command+'); preflight_rc=$?; printf "\\nPREFLIGHT_REMOTE_EXIT:%s\\n" "$preflight_rc"'
    output = execute([hdc, '-t', target, 'shell', wrapped], timeout)
    match = re.search(r'\nPREFLIGHT_REMOTE_EXIT:(\d+)\s*$', output)
    require(match is not None, 'unverified', 'Missing remote exit marker: '+output[-1000:])
    require(match.group(1) == '0', 'missing' if match.group(1)=='44' else 'unverified', 'Remote probe failed: '+output[-1000:])
    return output[:match.start()].strip()


def check_one(check, timeout):
    kind = check.get('kind')
    if kind == 'tool':
        tool = executable(check.get('tool'))
        option = check.get('version_option')
        if option is None:
            return tool
        require(option in ['--version', '-v', '-h'], 'unverified', 'Only version/help options are allowed')
        output = execute([tool, option], timeout)
        if 'expect_contains' in check:
            require(check['expect_contains'] in output, 'mismatch', 'Unexpected tool version: '+output[:1000])
        return output[:1000]
    if kind in ['file', 'directory']:
        path = path_value(check.get('path'))
        require(path.is_file() if kind == 'file' else path.is_dir(), 'missing', f'{kind} not found: {path}')
        require(os.access(path, os.R_OK), 'unverified', f'Not readable: {path}')
        return str(path)
    if kind == 'json-values':
        path = path_value(check.get('path'))
        require(path.is_file(), 'missing', f'Metadata missing: {path}')
        content = json.loads(path.read_text())
        expected = check.get('expected', {})
        require(bool(expected), 'unverified', 'Specify expected metadata values')
        for key, value in expected.items():
            require(key in content, 'missing', f'Metadata key missing: {key}')
            require(content[key] == value, 'mismatch', f'{key}: expected {value!r}, observed {content[key]!r}')
        return {key: content[key] for key in expected}
    if kind == 'skill-files':
        name = check.get('skill')
        require(isinstance(name, str) and re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name), 'unverified', 'Invalid skill name')
        roots = check.get('roots', [str(Path.home()/'.codex/skills'), str(Path.home()/'.agents/skills')])
        candidates = [path_value(root)/name/'SKILL.md' for root in roots]
        matches = [p for p in candidates if p.is_file() and re.search(r'^name:\s*[\'"]?'+re.escape(name)+r'[\'"]?\s*$', p.read_text(), re.M)]
        require(bool(matches), 'missing', f'Skill files not found: {name}')
        return {'paths': [str(p) for p in matches], 'note': 'Files only; agent must also confirm skill is enabled in its available-skill catalog'}
    if kind == 'skill-available':
        name, catalog = check.get('skill'), check.get('available_skills')
        require(isinstance(name,str) and bool(name) and isinstance(catalog,list) and all(isinstance(v,str) for v in catalog), 'unverified', 'Supply the actual current agent skill catalog')
        require(name in catalog, 'missing', 'Required skill not available in current agent catalog: '+name)
        return {'skill': name, 'source': 'Current catalog supplied by the caller; not inferred from filesystem'}
    if kind == 'python-import':
        python = executable(check.get('python', sys.executable))
        module = check.get('module')
        require(isinstance(module, str) and re.fullmatch(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*', module), 'unverified', 'Invalid Python module name')
        # This check is for HOST build tools, never a target interpreter/extension.
        return execute([python, '-B', '-c', 'import importlib,sys; m=importlib.import_module(sys.argv[1]); print(getattr(m,"__file__","built-in"))', module], timeout).strip()
    if kind == 'elf':
        path = path_value(check.get('path'))
        require(path.is_file(), 'missing', f'ELF missing: {path}')
        arch = check.get('machine')
        require(bool(arch), 'unverified', 'Expected ELF machine is required')
        output = execute([executable(check.get('readelf', 'readelf')), '-h', '-l', '-d', str(path)], timeout)
        require(re.search(r'Machine:\s*'+re.escape(arch)+r'\s*$', output, re.M) is not None, 'mismatch', 'ELF machine differs from expected '+arch)
        if check.get('interpreter'):
            require(check['interpreter'] in output, 'mismatch', 'Expected target interpreter not found')
        return {'machine': arch, 'note': 'ELF header only; dependency closure and symbol ABI need separate verification'}
    if kind == 'hdc-identity':
        output = remote(check, 'uname -smr', timeout)
        if check.get('expect_contains'):
            require(check['expect_contains'] in output, 'mismatch', 'Unexpected target identity: '+output)
        return output
    if kind in ['remote-file', 'remote-directory']:
        path = str(path_value(check.get('path')))
        require(path.startswith('/'), 'unverified', 'Remote path must be absolute')
        quoted = shlex.quote(path)
        command = 'if ! test '+('-f' if kind == 'remote-file' else '-d')+' '+quoted+'; then exit 44; fi; test -r '+quoted
        remote(check, command, timeout)
        return path
    if kind == 'remote-python-import':
        python = str(path_value(check.get('python')))
        require(python.startswith('/'), 'unverified', 'Explicit absolute TARGET Python path required')
        module = check.get('module')
        require(isinstance(module, str) and re.fullmatch(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*', module), 'unverified', 'Invalid target module')
        environment = check.get('env', {})
        require(isinstance(environment, dict) and all(k in ['PATH','LD_LIBRARY_PATH','PYTHONPATH','AMENT_PREFIX_PATH'] and isinstance(v,str) for k,v in environment.items()), 'unverified', 'Invalid target environment')
        prefix = 'PYTHONDONTWRITEBYTECODE=1 '+ ' '.join(k+'='+shlex.quote(v) for k,v in environment.items())
        code = 'import importlib,json,sys,sysconfig; m=importlib.import_module(sys.argv[1]); print(json.dumps({"SOABI":sysconfig.get_config_var("SOABI"),"version":getattr(m,"__version__",None),"file":getattr(m,"__file__",None)}))'
        output = remote(check, prefix+' '+shlex.quote(python)+' -B -c '+shlex.quote(code)+' '+shlex.quote(module), timeout)
        metadata = json.loads(output)
        for key,value in check.get('expected',{}).items():
            require(metadata.get(key)==value, 'mismatch', 'Target Python/module metadata differs: '+key)
        return metadata
    if kind == 'module-vermagic':
        path = path_value(check.get('path'))
        require(path.is_file(), 'missing', 'Kernel module missing: '+str(path))
        expected = check.get('expected')
        require(isinstance(expected,str) and bool(expected), 'unverified', 'Expected complete vermagic required')
        output = execute([executable(check.get('modinfo','modinfo')), '-F', 'vermagic', str(path)], timeout).strip()
        require(' '.join(output.split())==' '.join(expected.split()), 'mismatch', 'Module vermagic differs: '+output)
        return output
    if kind == 'remote-kernel':
        expected = check.get('expected')
        require(isinstance(expected, str) and bool(expected), 'unverified', 'Expected kernel release is required')
        output = remote(check, 'uname -r', timeout)
        require(output == expected, 'mismatch', f'Kernel expected {expected!r}, observed {output!r}')
        return output
    if kind == 'remote-pci':
        address = check.get('address', '')
        require(re.fullmatch(r'[0-9a-fA-F]{4}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-7]', address) is not None, 'unverified', 'Explicit PCI address required')
        vendor, device = check.get('vendor'), check.get('device')
        require(all(isinstance(v, str) and re.fullmatch(r'0x[0-9a-fA-F]{4}', v) for v in [vendor, device]), 'unverified', 'Expected vendor/device hex IDs required')
        base = '/sys/bus/pci/devices/'+address
        output = remote(check, 'cat '+shlex.quote(base+'/vendor')+' '+shlex.quote(base+'/device'), timeout).splitlines()
        require([line.lower() for line in output] == [vendor.lower(), device.lower()], 'mismatch', 'PCI IDs differ: '+str(output))
        if check.get('require_bound'):
            remote(check, 'test -L '+shlex.quote(base+'/driver')+' && readlink '+shlex.quote(base+'/driver'), timeout)
        return {'address': address, 'vendor': vendor, 'device': device, 'driver_required': bool(check.get('require_bound'))}
    raise CheckFailure('unverified', f'Unsupported check kind: {kind!r}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--timeout', type=float, default=10.)
    args = parser.parse_args()
    try:
        require(0 < args.timeout <= 60, 'unverified', 'Timeout must be between 0 and 60 seconds')
        manifest = json.loads(args.manifest.read_text())
        checks = manifest.get('checks')
        require(isinstance(checks, list) and bool(checks), 'unverified', 'Manifest must contain nonempty checks')
        results = []
        for index, check in enumerate(checks):
            label = check.get('id', f'check-{index+1}') if isinstance(check, dict) else f'check-{index+1}'
            try:
                require(isinstance(check, dict), 'unverified', 'Check must be an object')
                evidence = check_one(check, args.timeout)
                results.append({'id': label, 'status': 'passed', 'evidence': evidence})
            except CheckFailure as error:
                results.append({'id': label, 'status': error.status, 'detail': error.detail})
            except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
                results.append({'id': label, 'status': 'unverified', 'detail': str(error)})
        passed = all(r['status'] == 'passed' for r in results)
        print(json.dumps({'passed': passed, 'action': 'continue' if passed else 'stop-and-request-user-input', 'checks': results}, ensure_ascii=False, indent=2))
        return 0 if passed else 1
    except (CheckFailure, OSError, ValueError, AttributeError) as error:
        print(json.dumps({'passed': False, 'action': 'stop-and-request-user-input', 'error': str(error)}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
