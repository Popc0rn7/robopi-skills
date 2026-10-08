---
name: oh-ros2
description: Develop, port, run, and diagnose ROS 2 packages on OpenHarmony, including SDK-based cross-compilation, message bindings, deployment, DDS communication, and simulation/hardware interface alignment. Use for OpenHarmony ROS 2 work, not general ROS on Linux or HarmonyOS UI application development.
---

# OpenHarmony ROS 2

把现有 ROS 2 能力迁移或开发到 OpenHarmony，保持用户需要的数据接口和功能，并用目标设备上的证据说明完成范围。交叉编译只是其中一个部分。


## 依赖预检：未通过即停止

实际构建、部署或运行前，按 [依赖预检](references/preflight.md) 建立本次必需清单，并运行 `scripts/preflight.py`。其他 skill 只有本次计划采用时才是依赖；确认它在当前可用清单中，不把磁盘文件存在当成可调用。

任何必需项缺失、版本不匹配、权限/超时导致未验证，或预检脚本不能执行，都停止当前依赖链并列出用户需要补充的内容。不自动安装、修复、提权重试或绕过；用户补充并重新预检通过后再继续。仅分析资料时不连接设备。这条规则优先于下文/旧参考中“排障后修复”的流程，排障说明只用于解释缺口。


## 先识别任务和实际环境

读取项目入口、构建脚本和现有验证记录；优先复用已工作的流程。记录目标镜像、架构/libc、ROS 发行版及前缀、RMW、Python ABI、SDK 与项目运行目录。历史案例的路径和版本不能代替当前检查。

按请求选择工作，不默认重建 ROS、改变通信拓扑、替换传感器算法或启动业务设备。用户已经给定的目录、部署布局和运行方式优先。

## 按需读取参考

- C/C++ 包、目标依赖或 toolchain：读 [cross-build.md](references/cross-build.md)。
- ROS 消息、Python native 扩展、NumPy ABI：另读 [python-interfaces.md](references/python-interfaces.md)。普通 Python 脚本通常只需安装。
- 环境初始化、部署、launch、主机↔板端 DDS 和运行诊断：读 [runtime-dds.md](references/runtime-dds.md)。
- 仿真替代真实传感器/控制器、时间与坐标适配：读 [interfaces.md](references/interfaces.md)。
- RoboPi 预装 Humble 或复用此次工程：读 [robopi-humble.md](references/robopi-humble.md)。这是已验证案例，不是所有 OpenHarmony 镜像的标准。

HDC 属于设备接入方式。若当前环境提供 hdc-master skill，设备操作可结合它；本 skill 不依赖该 skill 存在，也不保存设备 connect key。

## 实施与完成条件

区分主机执行的工具、目标链接的依赖、直接部署的脚本，以及仍留在主机的组件。不要把 CPU 架构一致当成 ABI 一致，也不要把某个已安装 ROS 包当成整套依赖都可用。

验证按任务逐级推进：目标 ABI/依赖检查 → 板端加载或 import → 必要的消息收发 → 请求所需的业务功能。可停止在与当前任务相称的一层；只编译的任务不自动扩展为设备部署或飞行测试。

能力对照使用相同输入、目标和验收门限。报告编译、通信、安全拒绝及功能完成各自的结果；拒绝请求不等于实现请求，更换失败目标不能算原目标通过。

失败时先保存命令、目标版本和最小日志，定位到生成工具、配置、链接、加载、通信或业务层后修正。不要无依据地升级基础环境、反复重启设备或放宽验收条件。

最终说明改动、产物位置、SDK/目标依赖来源、实际通过的验证，以及尚未验证的能力。启动脚本就绪、默认场景配置、合成消息测试和实际物理仿真是不同证据，不能互相替代。

## 执行边界

构建和检查在主机完成；部署仅操作用户指定的项目目录并保留可回退产物。更新前检查项目是否运行，停止或替换它需符合当前用户授权；不为部署杀掉无关进程。

创建 skill 或请求交叉编译不授权向设备发业务指令。启动模拟器、故障注入、解锁、起飞、真实运动等操作仅在当前任务明确涵盖时执行，不沿用案例中的历史批准。
