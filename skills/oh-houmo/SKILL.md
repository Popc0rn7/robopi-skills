---
name: oh-houmo
description: Deploy, diagnose, cross-build, and validate Houmo NPU drivers, HAL/TCIM runtimes, and inference applications on OpenHarmony, including the RoboPi M50/xh2 integration. Use for Houmo accelerator work; general HDC access and ROS 2 package development use their own workflows.
---

# OpenHarmony Houmo

处理 OpenHarmony 上的 Houmo 加速器接入、驱动、运行库与推理程序。先识别实际设备/软件组合，再进行与用户任务相称的验证，不把看到硬件等同于推理能力可用。


## 依赖预检：未通过即停止

实际构建、部署或运行前，按 [依赖预检](references/preflight.md) 建立本次必需清单，并运行 `scripts/preflight.py`。其他 skill 只有本次计划采用时才是依赖；确认它在当前可用清单中，不把磁盘文件存在当成可调用。

任何必需项缺失、版本不匹配、权限/超时导致未验证，或预检脚本不能执行，都停止当前依赖链并列出用户需要补充的内容。不自动安装、修复、提权重试或绕过；用户补充并重新预检通过后再继续。仅分析资料时不连接设备。这条规则优先于下文/旧参考中“排障后修复”的流程，排障说明只用于解释缺口。


## 基于当前设备而不是旧记录

读取项目和厂商发布说明，确认设备型号/总线、系统架构/libc、完整内核版本、驱动版本/vermagic、HAL/TCIM runtime、SDK 与模型格式。若请求只是分析资料，不自动连接或修改板端。

M50/xh2 的既有详细流程见 [RoboPi M50 参考](references/robopi-m50.md)。其中 PCI ID、内核 6.6.86、目录、示例和 SDK 参数是历史案例，不是所有 Houmo 产品的默认值。尚未覆盖的新硬件或 API 先核对厂商资料，不能自行断言兼容。

## 按请求选择工作层

- 枚举/识别：只读检查总线、设备节点、已绑定驱动及 kernel log，保存实际输出。
- 驱动：在主机检查供应商归档、模块架构及完整 vermagic；加载前确认与目标内核匹配。已被其他进程使用时，不卸载/替换驱动。
- HAL/runtime：区分驱动包、HAL 库和 TCIM 库，核对实际动态依赖和可用工具；先做最小发现/运行测试。
- 推理：使用匹配目标后端的模型和已知样本，检查结果、耗时、错误及重复运行，而不只检查进程退出码。
- 应用构建：OHOS SDK 与部署包版本对应；生成目标 ELF，审计 loader/NEEDED，再进行板端验证。

出现失败时保存所在层的命令和错误，不跳到大型模型或重做整套系统。不要强制加载不兼容模块，或用主机 glibc 库补齐目标 musl 依赖。

## 构建和部署

构建留主机。解包前检查归档层级，部署到用户指定的可写项目位置，校验文件并保留可回退产物；厂商文档目录矛盾时对照实际包内容和命令，不盲目照抄表格。

按实际 SDK 选择后端及目标架构。旧 Eigen 编译错误的兼容定义仅在确认对应错误及厂商建议时采用，不对全部工程默认禁用优化。

HDC 是传输/shell/日志通道，可结合 hdc-master；无需把它的连接与端口手册复制进本 skill。ROS 2 集成仅在任务需要时结合 oh-ros2，NPU 可独立使用。

## 权限与验收

读取模块信息不授权 insmod/rmmod、修改启动配置或自动加载驱动。加载、更换、重启和影响共享设备的操作需符合当前用户授权；任务仅要求准备时停在可审查的包和方案。默认不配置开机加载。

按任务报告：硬件是否可见 → 驱动是否绑定 → runtime 是否发现设备 → 样本推理是否正确 → 自建程序是否重复运行。未完成的层明确标注，不把上层报告猜成已经验证。

记录内核/软件/模型来源与版本、部署位置、执行结果和残留进程。用户未请求时不改变模型、设备路线或 ROS 定位/规划逻辑。
