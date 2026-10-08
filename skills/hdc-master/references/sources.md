# 来源与维护

核对日期：2026-10-08。手册是按任务组织的操作说明，不是官方文档全文副本。

- 用户提供的官方仓库：[OpenHarmony developtools_hdc](https://gitee.com/openharmony/developtools_hdc)。本次网页读取返回 405，未据此假设仓库不存在。
- 同一 OpenHarmony 组织的 GitHub 仓库：[README_zh.md](https://github.com/openharmony/developtools_hdc/blob/master/README_zh.md)。用于核对架构、基础命令及历史版本差异。
- 官方文档：[HDC 调试指南](https://github.com/openharmony/docs/blob/master/zh-cn/application-dev/dfx/hdc.md)。用于核对连接、管理通道与诊断术语。
- 本机 SDK 工具实际输出：`hdc -v` → `Ver: 3.2.0g`；`hdc -h`、`hdc -h verbose`。主要命令表与参数来自该帮助。
- 原 robopi-hdc 的本地设备接入经验：保留于 device-notes；ROS/NPU 业务资料不混入 HDC 主流程。

验证范围是本地帮助/版本与 skill 格式、引用审查；没有为手册测试重启设备、打开 TCP、转发端口、安装包或刷机。使用时再核对实际设备的能力和行为。

官方 README 的 udev、root、remount 示例不是默认自动修复流程；本 skill 选择按失败层定位并使用具体目标和最小范围变更。帮助中 tmode 的重启措辞与 README 有差异，所以不保证其只影响 daemon；在目标版本查实后执行。

更新某一版本差异时，记录来源和实际结果，避免把支持某个命令的单机观察变成跨版本要求。
