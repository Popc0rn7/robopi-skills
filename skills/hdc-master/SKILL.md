---
name: hdc-master
description: Use OpenHarmony HDC to connect and target devices, execute remote shell commands, transfer files, manage application packages, collect logs, forward ports, and diagnose USB/TCP or client-server-daemon failures. Applies to HDC device access and debugging, including RoboPi; ROS development, NPU algorithms, and firmware flashing procedures belong to their own workflows.
---

# HDC Master

聚焦 OpenHarmony Device Connector 本身。HDC 是主机 client/server 与设备 hdcd 之间的管理与调试通道，不是 ROS DDS、传感器驱动或 NPU runtime。


## 依赖预检：未通过即停止

实际构建、部署或运行前，按 [依赖预检](references/preflight.md) 建立本次必需清单，并运行 `scripts/preflight.py`。其他 skill 只有本次计划采用时才是依赖；确认它在当前可用清单中，不把磁盘文件存在当成可调用。

任何必需项缺失、版本不匹配、权限/超时导致未验证，或预检脚本不能执行，都停止当前依赖链并列出用户需要补充的内容。不自动安装、修复、提权重试或绕过；用户补充并重新预检通过后再继续。仅分析资料时不连接设备。这条规则优先于下文/旧参考中“排障后修复”的流程，排障说明只用于解释缺口。


## 选择实际工具和目标

先检查 `command -v hdc`、`hdc -v` 和 `hdc -h`；高级选项使用 `hdc -h verbose`。按当前版本核对语法，不把历史 README 或本手册的选项当成所有镜像必然支持。

需要设备操作时再运行 `hdc list targets -v`。一个目标也使用显式 `-t`；多目标按型号、产品属性和连接方式识别，不选择列表中的第一个。当前 connect key 只用于本次命令，不保存进 skill。

分清主机 server、设备 hdcd 和远端业务进程。主机 server 重启会影响其他 HDC 会话；`tmode`/`smode` 可能重启 daemon 并中断连接。不要把它们作为每次连接的初始化步骤。

## 按需读取

- 命令语法、传输、TCP/USB、应用、日志、端口转发与调试：读 [command-manual.md](references/command-manual.md)。这是可按章节查阅的操作手册。
- 无设备、权限、连接超时、版本或数据传输失败：读 [troubleshooting.md](references/troubleshooting.md)，按失败层定位。
- RoboPi 接线、debug UART 与本机沙箱现象：读 [device-notes.md](references/device-notes.md)，不把板型经验推广到所有设备。
- 更新手册或遇到版本差异：查 [sources.md](references/sources.md) 的官方来源，并优先检查实际工具帮助。

ROS 2 构建、环境和 DDS 属于 `oh-ros2`（可用时结合该 skill）。Houmo NPU 驱动、模型和推理由 oh-houmo 维护（可用时结合）；HDC 只负责它们的文件传输、shell 和日志通道。

## 执行和验证

先按用户任务判断需要的命令范围。检查、文件接收与 bounded 日志可直接用于诊断；发送/覆盖文件、安装替换、服务或网络模式改变要符合现有授权。构建 skill 不授权操作设备。

传输明确本地/远端路径和覆盖行为，核验实际文件。复杂 shell 保持在远端执行，必要时捕获远端退出码；HDC 退出码或一句成功提示不能代替结果验证。

连接失败先保存完整错误，再区分沙箱、主机权限、server、传输、hdcd 和业务层。不要无证据地重启 server、改 udev 或重启板子。若命令因权限限制无法执行，按当前环境提供的授权机制处理，不用 root 或全局权限放开绕过限制。

涉及 reboot、root daemon、remount、卸载数据、系统参数、OTA/flash/erase 等操作时，检查用户是否明确授权该具体操作及目标。缺少授权或镜像/分区信息时停在诊断或方案，不因能运行 HDC 就执行。

报告使用的目标、命令/版本、观察结果、是否验证及残留状态。删除端口映射、结束日志或恢复连接模式只处理本次任务创建的内容，不清理其他人的会话。
