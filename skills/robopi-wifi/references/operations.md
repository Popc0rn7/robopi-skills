# 部署、用法与兼容性

## 随包产物

仅将两个 assets 部署到板子：
- robowifi：shell 启动脚本，从 PATH、相对/绝对路径或符号链接定位自身，清理本进程 ROS LD_PRELOAD。
- robowifi.bin：ARM64 动态链接程序，与已实测 robopi-wifi.bin 字节一致。

默认部署目录 `/sys_prod/robot/out/bin` 是当前 RoboPi 的可写且已在 PATH 中的目录。
这是本板惯例，不是所有 OpenHarmony 镜像通用路径。检查挂载、可写性、PATH 和已有文件。
`/usr/local/bin` 在原测试板上不存在且根分区只读，不为安装工具自动 remount。

已验证环境：SysLong RoboPi、Linux 6.6.86、OpenHarmony 7.0 测试镜像、ARM64。
其他版本先核对下列依赖；工具不适用于普通 Linux/Ubuntu。

## 设备预检

以下为板子 shell 查询示例，实际调用使用 hdc-master 选定的显式目标：

```sh
id
uname -m
param get const.product.name
printf '%s\n' "$PATH"
ls -ld /sys_prod/robot/out/bin
ls -l /system/lib64/platformsdk/libnativetoken_shared.z.so
ls -l /system/lib64/platformsdk/libtokensetproc_shared.z.so
ls -l /system/lib64/chipset-pub-sdk/libaccesstoken_sdk.z.so
ls -l /system/lib64/platformsdk/libwifi_sdk.z.so
```

需要 root/HDC 开发环境，以及上述原生库和服务的兼容 ABI。
有库文件不能证明 ABI 兼容，运行失败应保留错误；正式路径权限错误查 SELinux 日志，不关闭强制模式。
只查看服务状态可使用 `hidumper -s 1120`，它不会申请本工具身份。

## 安装

在主机确认目标及 skill assets 的绝对路径。不要保存设备 connect-key 到 skill。
下面的变量由本次环境填入：

```sh
robopi_target='本次确认的connect-key'
robowifi_assets='/绝对路径/robopi-wifi/assets'
hdc -t "$robopi_target" shell 'ls -l /sys_prod/robot/out/bin/robowifi /sys_prod/robot/out/bin/robowifi.bin'
```

安装授权后，首次安装可发送：

```sh
hdc -t "$robopi_target" file send "$robowifi_assets/robowifi" /sys_prod/robot/out/bin/robowifi
hdc -t "$robopi_target" file send "$robowifi_assets/robowifi.bin" /sys_prod/robot/out/bin/robowifi.bin
hdc -t "$robopi_target" shell 'chmod 755 /sys_prod/robot/out/bin/robowifi /sys_prod/robot/out/bin/robowifi.bin'
hdc -t "$robopi_target" shell 'command -v robowifi; robowifi --help'
```

已有同名文件则先校验并按用户授权备份/更新，不覆盖无关工具。
两个文件保持在同一目录。原来已安装 robopi-wifi 可以保留，不能因此误认新名称已存在。
复制成功后检查文件大小或哈希。帮助不申请权限，可用于纯安装验证。

## 首次执行前

在获准管理 Wi-Fi 的任务中，备份原生权限记录到一个新的、访问受限的位置。
例如使用本次确定未存在的 `/data/local/tmp/robowifi-token-backup-<日期时间>.json`；
不要复用固定备份名，不打印整份权限文件。

程序申请权限：
GET_WIFI_INFO、SET_WIFI_INFO、MANAGE_WIFI_CONNECTION、GET_WIFI_CONFIG、
SET_WIFI_CONFIG、GET_WIFI_INFO_INTERNAL，APL system_basic，processName robopi_wifi。
GetAccessTokenId 会持久创建/更新该身份，SetSelfTokenID 作用于当前进程。
若此前原版工具已创建相同身份，当前工具复用该身份，不新建无关权限。

## 连接与重连

交互连接应进入 `hdc -t "$robopi_target" shell` 再输入：

```sh
robowifi connect --ssid '热点名称'
```

密码在终端不回显。工具设置 DHCP，调用 AddDeviceConfig 和 ConnectTo，
打印 `Saved system network_id=N` 后等待认证及 IPv4（最长 60 秒）。记下实际编号。

```sh
robowifi reconnect N
robowifi status
robowifi disconnect
```

开放热点：`robowifi connect --ssid '热点名称' --open`。
自动化凭据输入：`--password-stdin`，从受保护的 stdin 读取一行，不把密码放到 argv。
支持开放热点、WPA/WPA2 PSK；SSID 最大 32 字节，PSK 8–63 字符或 64 位十六进制。
不提供仅 WPA3、企业 EAP、隐藏热点专用参数，不承诺这些模式可用。

配置由系统保存，不再使用旧 wpa.conf。配置编号和 IP 不保证跨设备相同。
reconnect 的完成判定是原生已连接且接口有 IPv4；不声称每次命令都经历了断开重连。

## 验证

```sh
robowifi status
ifconfig wlan0
hidumper -s 1120
hidumper -s NetConnManager
ping -c 3 用户指定的局域网IPv4
```

status 的 connected 必须为 1。断开后 IPv4 可能暂留，应以 connected 状态判断。
没有用户指定的对端时，用现有网关或报告地址/服务状态，不猜对端 IP。

原工具实测：原生权限成功、Wi-Fi connected、系统 DHCP 分配 IPv4、
NetConnManager IsAvailable:1、局域网 ping 成功、disconnect 和已保存配置的 reconnect 成功。
本 skill 分发的二进制未改；启动脚本仅重命名配套文件并调整帮助文本。
新命令名在板上的部署仍需按本次任务验证。

## 失败分层

- load/symbol 错误：库路径/ABI，不自动移植其他版本。
- GetAccessTokenId/SetSelfTokenID/ReloadNativeTokenInfo 失败：原生身份或权限环境。
- EnableWifi/AddDeviceConfig/ConnectTo 返回错误：查看 Wi-Fi 服务日志，-128 本身不能区分原因。
- 已认证无 IPv4：检查系统 DHCP 日志，不启动第二个 udhcpc。
- 有 IPv4 系统未识别：查 NetConnManager，不能只凭 ifconfig 判断系统集成成功。

使用 `hilog -x` 配合服务 PID/关键词和 tail 限制输出；避免输出凭据。
源码保留在项目 network-persistence/robopi-wifi/robopi-wifi.c，
编译采用 OpenHarmony SDK 26.0.1.45-Beta1。本 skill 无编译依赖；不能在 x86 主机直接执行 ARM64 二进制。
