---
name: robopi-wifi
description: Deploy and use the bundled robowifi native Wi-Fi tool on SysLong RoboPi OpenHarmony boards to connect hotspots, obtain IPv4 through system DHCP, reconnect saved networks, disconnect, and diagnose native permission or connection failures. Use for RoboPi Wi-Fi networking; general device access belongs to hdc-master, ROS development to oh-ros2, and Houmo NPU work to oh-houmo.
---

# RoboPi Wi-Fi

使用随包 `assets/robowifi` 和 `assets/robowifi.bin`。它们调用板上原生 Wi-Fi 服务及系统 DHCP，不是 wpa_cli/udhcpc 的包装。工具原名 robopi-wifi；本 skill 中命令名为 robowifi，二进制沿用已实测版本。

## 分工与预检

需要访问板子时结合当前可用的 `hdc-master`，按其目标选择和依赖预检流程操作。仅准备文件或解释用法时不连接板子。不要求 oh-ros2、oh-houmo 或 ROS 环境来使用 Wi-Fi。

先读 [operations.md](references/operations.md) 的部署与兼容性部分，确认本次所需文件、HDC 目标、root 身份和原生库可用。缺失或不兼容时报告具体项，不自动安装其他网络管理器或退回旧 Python DHCP、BusyBox、手动 wpa_supplicant 流程。

## 常用操作

```sh
robowifi status
robowifi connect --ssid '热点名称'
robowifi reconnect 网络编号
robowifi disconnect
```

- `connect` 提示输入密码，内部自动开启无线，保存系统热点配置并连接；不需要 enable 命令。
- `reconnect` 使用实际保存的网络编号，不能假定为 0；也会自动开启无线。
- `disconnect` 断开连接并等待确认，保留热点配置和无线开关。
- `status` 查询原生连接状态和 wlan0 的 IPv4。单独有地址、接口 UP 或接口调用返回 0 都不能证明连接完成。

## 鉴权与边界

除帮助外，每次命令在同一进程调用 GetAccessTokenId、SetSelfTokenID、ReloadNativeTokenInfo，然后访问 libwifi_sdk.z.so。身份为 `robopi_wifi`，不会借用其他服务 Token。

首次执行会创建或更新 `/data/service/el0/access_token/nativetoken.json` 中该身份的权限记录。部署文件与执行鉴权是两个步骤：在授权的连接/管理任务中说明该持久副作用，首次操作前备份现有权限记录；若用户只要求检查文件或安装程序，不顺带执行 status 等会初始化权限的命令。不要通过整份旧备份覆盖当前权限库，不改 SELinux、init 或只读分区来绕过失败。

密码使用交互输入，或受保护的 stdin；不通过命令行参数、工具输出或共享文档暴露。仅为验证需要读取用户已授权的热点配置，不把密码打包进 skill。

## 验证与报告

连接后查看工具 status、ifconfig wlan0 和 `hidumper -s NetConnManager`，必要时 ping 用户指定的局域网设备。目标是局域网时不要求外网访问。工具等待最多 60 秒，超时后系统请求可能仍在继续；查状态和 bounded hilog，不无限重试。

系统可能使用随机 MAC，IPv4 可能变化。热点配置已通过系统保存，不把磁盘保存等同于开机自启；重启自动重连尚未验证。不要同时启动其他 DHCP 或 supplicant 管理 wlan0。进一步部署、凭据输入、排障和命令参数见 [operations.md](references/operations.md)。

报告本次目标、安装/调用结果、SSID 和 IPv4（不含密码）、系统是否识别网络，以及未验证事项。构建 skill 不授权连接或修改任何板子。
