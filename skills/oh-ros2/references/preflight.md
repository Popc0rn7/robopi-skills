# 按需依赖预检

此流程检查当前任务的必需依赖，不是安装器。先从项目入口和当前可用技能清单建立依赖表，再生成临时 JSON manifest；不能为了得到通过而漏掉必需项，也不检查与本任务无关的依赖。

## 执行与停止规则

1. 只请求分析资料时，不执行设备预检；需要实际构建/运行时选择该操作的依赖。
2. 需要其他 skill 时，从当前模型可用技能清单确认它存在，加入 `skill-available`。文件存在检查单独使用 `skill-files`，两者不是同一证据。
3. 必需路径/SDK/型号/期望版本未知时，把它标为未验证并停止，让用户提供；不从旧案例补出一个假定值。
4. 调用本 skill 的 `scripts/preflight.py --manifest <临时清单>`，检查退出码和 JSON。设备项仅在当前任务允许设备读取时列入，使用明确目标。
5. 只有所有必需项通过，才继续当前操作。缺失、不匹配、未验证、脚本无法执行或超时均停止该依赖链；不自动安装依赖、下载技能、提权重试、重启、开端口或加载驱动。
6. 给用户列出未通过项、观察结果、所需路径/版本/权限/资料及复验方式。用户补充后重新预检，再恢复，不把沉默或等待当成补齐。

脚本会汇总清单中的只读检查以便一次列出问题，不执行后续业务步骤。返回 0 表示清单检查通过，1 表示停止；命令行用法错误也按未通过处理。JSON `action` 为 `continue` 或 `stop-and-request-user-input`。

`passed` 仅证明清单列出的检查，不能证明清单完整、依赖闭包或功能已验收。模型要在执行前复核依赖表。内置检查不启动 ROS 节点、模拟器或推理，不改设备模式；目标 Python import 禁用 pyc 写入，但只对已明确选择的可信模块执行。

## Manifest 与结果

```json
{
  "checks": [
    {"id": "hdc-tool", "kind": "tool", "tool": "hdc", "version_option": "-v"}
  ]
}
```

每项都为必需项，没有默认忽略失败的 optional 模式。支持以下 kind：

| kind | 必需输入及验证范围 |
|---|---|
| `tool` | `tool`；可选 `version_option` 仅限 --version/-v/-h，`expect_contains` 核对输出；不自动执行其他参数 |
| `file` / `directory` | `path`；只证明存在与可读，不证明内容可用 |
| `json-values` | `path`、`expected` 字典；比较已采集的 ABI/版本元数据，不自行采集板端状态 |
| `skill-files` | `skill`、可选 `roots`；查 skill 文件和 name，不代表模型已启用 |
| `skill-available` | `skill`、`available_skills`；调用模型从实际当前清单提供列表，不从文件猜测 |
| `python-import` | host `python`、`module`；检查主机生成工具 import，不在主机执行目标扩展 |
| `elf` | `path`、`machine`；可选 SDK `readelf` 和 `interpreter`；检查 ELF 头，不等于完整 ABI/链接闭包 |
| `module-vermagic` | host 模块 `path`、完整 `expected`、可选 `modinfo`；读取模块信息，不加载 |
| `hdc-identity` | `target`、可选 `hdc` 和 `expect_contains`；读取 uname |
| `remote-file` / `remote-directory` | `target`、绝对 `path`；检测目标存在与可读 |
| `remote-kernel` | `target`、`expected`；精确比较 uname -r |
| `remote-pci` | `target`、实际 `address`、vendor/device 0xNNNN；可选 `require_bound`，不装驱动 |
| `remote-python-import` | `target`、绝对 target `python`、`module`；可选 `env`、`expected`，读取 SOABI/module version/file |

设备项可覆盖 `hdc` 路径。target import 的 `env` 只支持 PATH、LD_LIBRARY_PATH、PYTHONPATH、AMENT_PREFIX_PATH，值来自当前工程；不会 source 一个可能启动节点的脚本。HDC wrapper 读取远端退出标记，不把 HDC 返回 0 当成远端成功。

超时默认每项 10 秒，可通过 `--timeout` 设置最多 60 秒。脚本不执行任意 host/remote 命令清单；更复杂的业务检查仍由明确的已审查流程完成。

路径中的 `${...}` 和 `<...>` 占位符不得用于实际清单。版本预期来自当前 SDK/镜像/发布说明，不能照抄本文件或历史案例。清单仅放在本次临时目录，不把设备 connect key 保存到 skill 或项目。

## 分任务选择依赖

- C/C++ 构建：host CMake/Ninja、实际 host 生成器/Python、SDK toolchain/Clang、目标 ROS/第三方头文件与库及所需消息包。清单按 package.xml/CMake/项目工作流选择，不只检查 deps 目录存在。
- Python 消息：再加 host rosidl/ament/所需生成模块 import、目标 Python/NumPy 头文件、Python 库和 ABI metadata 校验。普通 Python 脚本部署不强制要求完整交叉编译 SDK。
- HDC 部署/设备运行：采用 hdc-master 时检查其可用性、HDC 工具、目标身份与对应 runtime；需要 rclpy/消息运行时使用 target import。离线构建不要求 HDC 或板子在线。
- 目标库闭包、typesupport 收发及业务功能仍按原有验证流程检查，不因基础预检通过宣称完整迁移完成。

## 检查器验证

`python3 scripts/test_preflight.py` 使用临时文件和模拟 HDC 验证成功、缺失、不匹配、超时、远端无退出标记及假成功等行为；不会连接板端。该测试不证明当前设备依赖已满足。
