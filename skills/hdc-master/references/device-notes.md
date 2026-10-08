# 设备接入备注：RoboPi

仅在连接 RoboPi 时使用；这不是 HDC 的全平台参数或通用接线标准。

- 已有案例使用 RoboPi USB OTG Type-C 连接 HDC。当前板型接口位置仍按其硬件资料确认，不把任意 Type-C 都当成 device 口。
- `067b:2303` 常见于 PL2303 debug UART 转接器，不凭旧 README 例子认定它是 HDC USB VID/PID。看实际枚举变化。
- debug UART 可辅助查看 hdcd/USB gadget；串口终端不是 HDC UART 协议连接，两者不能混用。
- 历史工作站的普通终端 udev 可工作，受限工具环境却返回 E002110。先区分执行环境，不能据此认定用户接线错误，也不能认定所有机器权限都已设置好。
- 系统 shell 工具可能是精简实现。参数不支持时检查该设备帮助；不用完整 GNU/Linux 选项强行解释输出。

ROS 前缀、Python/NumPy ABI、NPU 模块、模型和推理配置不属于本手册。ROS 内容由 oh-ros2 维护；Houmo M50/xh2 内容由 oh-houmo 维护。原 robopi-hdc 的完整资料保留归档。
