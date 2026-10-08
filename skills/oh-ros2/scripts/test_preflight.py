import importlib.util,json,os
from pathlib import Path
import subprocess,sys,tempfile,unittest
ENGINE=Path(__file__).with_name('preflight.py')
class Preflight(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
 def tearDown(self):self.temp.cleanup()
 def run_checks(self,checks,passed):
  manifest=self.root/'checks.json';manifest.write_text(json.dumps({'checks':checks}))
  result=subprocess.run([sys.executable,str(ENGINE),'--manifest',str(manifest),'--timeout','1'],capture_output=True,text=True)
  report=json.loads(result.stdout)
  self.assertEqual(result.returncode,0 if passed else 1,report)
  self.assertEqual(report['passed'],passed)
  self.assertEqual(report['action'],'continue' if passed else 'stop-and-request-user-input')
  return report
 def fake(self,source):
  path=self.root/'fake';path.write_text('#!'+sys.executable+'\n'+source);path.chmod(0o700);return str(path)
 def test_pass(self):
  meta=self.root/'abi.json';meta.write_text('{"SOABI":"target-abi"}')
  report=self.run_checks([{'kind':'tool','tool':sys.executable,'version_option':'--version'}, {'kind':'directory','path':str(self.root)}, {'kind':'json-values','path':str(meta),'expected':{'SOABI':'target-abi'}}, {'kind':'python-import','python':sys.executable,'module':'json'}, {'kind':'skill-available','skill':'oh-ros2','available_skills':['oh-ros2']}],True)
  self.assertEqual(len(report['checks']),5)
 def test_missing_and_unknown_block(self):
  report=self.run_checks([{'kind':'tool','tool':'__missing_hdc_preflight_test__'}, {'kind':'file','path':str(self.root/'absent')}, {'kind':'unknown'}, {'kind':'skill-available','skill':'oh-houmo','available_skills':[]}],False)
  self.assertEqual([r['status'] for r in report['checks']],['missing','missing','unverified','missing'])
 def test_mismatch(self):
  meta=self.root/'abi.json';meta.write_text('{"SOABI":"host-abi"}')
  report=self.run_checks([{'kind':'json-values','path':str(meta),'expected':{'SOABI':'target-abi'}}],False)
  self.assertEqual(report['checks'][0]['status'],'mismatch')
 def test_remote_missing_marker(self):
  hdc=self.fake('print("Error: remote shell not executed")')
  report=self.run_checks([{'kind':'hdc-identity','target':'fake-target','hdc':hdc}],False)
  self.assertEqual(report['checks'][0]['status'],'unverified')
 def test_remote_exit_despite_hdc_success(self):
  hdc=self.fake('print("\\nPREFLIGHT_REMOTE_EXIT:44")')
  report=self.run_checks([{'kind':'remote-file','path':'/nonexistent','target':'fake-target','hdc':hdc}],False)
  self.assertEqual(report['checks'][0]['status'],'missing')
 def test_remote_kernel_mismatch(self):
  hdc=self.fake('print("6.6.86\\nPREFLIGHT_REMOTE_EXIT:0")')
  report=self.run_checks([{'kind':'remote-kernel','expected':'different-kernel','target':'fake-target','hdc':hdc}],False)
  self.assertEqual(report['checks'][0]['status'],'mismatch')
 def test_remote_target_and_timeout(self):
  hdc=self.fake('import time;time.sleep(3)')
  report=self.run_checks([{'kind':'hdc-identity','target':'fake-target','hdc':hdc}, {'kind':'hdc-identity','hdc':hdc}],False)
  self.assertEqual([r['status'] for r in report['checks']],['unverified','unverified'])
 def test_skill_files_and_catalog_are_separate(self):
  folder=self.root/'example';folder.mkdir();(folder/'SKILL.md').write_text('---\nname: example\n---\n')
  report=self.run_checks([{'kind':'skill-files','skill':'example','roots':[str(self.root)]}, {'kind':'skill-available','skill':'example','available_skills':[]}],False)
  self.assertEqual([r['status'] for r in report['checks']],['passed','missing'])
 def test_pci_and_binding(self):
  hdc=self.fake('import sys;print("/drivers/xh2\\nPREFLIGHT_REMOTE_EXIT:0" if "readlink" in sys.argv[-1] else "0x1f6b\\n0x0c00\\nPREFLIGHT_REMOTE_EXIT:0")')
  self.run_checks([{'kind':'remote-pci','target':'fake-target','hdc':hdc,'address':'0000:01:00.0','vendor':'0x1f6b','device':'0x0c00','require_bound':True}],True)
 def test_vermagic(self):
  module=self.root/'test.ko';module.write_bytes(b'fixture')
  modinfo=self.fake('print("6.6.86 SMP mod_unload aarch64")')
  self.run_checks([{'kind':'module-vermagic','path':str(module),'modinfo':modinfo,'expected':'6.6.86 SMP mod_unload aarch64'}],True)
  report=self.run_checks([{'kind':'module-vermagic','path':str(module),'modinfo':modinfo,'expected':'other'}],False)
  self.assertEqual(report['checks'][0]['status'],'mismatch')
 def test_target_python(self):
  hdc=self.fake('import json;print(json.dumps(dict(SOABI="target-abi",version="2.4.0",file="/target/module")));print("PREFLIGHT_REMOTE_EXIT:0")')
  self.run_checks([{'kind':'remote-python-import','target':'fake-target','hdc':hdc,'python':'/target/python3','module':'numpy','expected':{'SOABI':'target-abi','version':'2.4.0'}}],True)
 def test_elf_machine(self):
  artifact=self.root/'program';artifact.write_bytes(b'fixture')
  readelf=self.fake('print("  Machine:                           AArch64\\n[Requesting program interpreter: /lib/ld-musl-aarch64.so.1]")')
  self.run_checks([{'kind':'elf','path':str(artifact),'machine':'AArch64','interpreter':'/lib/ld-musl-aarch64.so.1','readelf':readelf}],True)
  report=self.run_checks([{'kind':'elf','path':str(artifact),'machine':'other','readelf':readelf}],False)
  self.assertEqual(report['checks'][0]['status'],'mismatch')
 def test_no_path_placeholder_or_privileged_commands(self):
  before=set(self.root.iterdir())
  report=self.run_checks([{'kind':'file','path':'${OHOS_SDK_NATIVE}/missing'}, {'kind':'tool','tool':sys.executable,'version_option':'--install'}, {'kind':'remote-pci','target':'fake-target','address':'../../etc','vendor':'0x1f6b','device':'0x0c00'}],False)
  self.assertTrue(all(r['status']=='unverified' for r in report['checks']))
  self.assertEqual(set(self.root.iterdir())-before,{self.root/'checks.json'})
if __name__=='__main__':unittest.main()
