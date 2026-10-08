# HDC 分层排障

按实际症状找失败层，不先执行重启、root 或全局权限放开。保存工具路径、版本、完整错误、目标列表和相关最小日志。

## 1. 本机工具启动失败

`command -v hdc` / `hdc -v` 失败：检查 SDK 的 host 平台和实际可执行文件。Linux 动态库失败用 readelf/ldd 查询 host 依赖；不要把板端库加入 host HDC 环境，也不要同时保留多个不明版本的 PATH 项。

IDE 与终端可能使用不同 SDK。列出进程与使用路径，确认 client/server 版本匹配；`checkserver` 不是设备 hdcd 版本检查。涉及设备版本时按镜像查 hdcd 版本，不承诺新 host 工具与所有旧设备兼容。

## 2. client 连接不到主机 server

若出现 `Connect server failed`、`E002110` 或 `operation not permitted`，先看执行环境是否禁止本地 server socket/USB；它不直接证明设备或 udev 故障。需要 host 权限时只对同一个诊断命令走当前工具的授权机制。

在用户正常终端或已允许的 host 环境重试成功，就保留该结论，不改设备、udev 或服务。授权被拒绝时报告执行边界，不绕过它。

若普通终端也失败，再核对 `-s` / `OHOS_HDC_SERVER_PORT`、监听占用、server 进程、client/server 版本和日志。确定 server 异常且允许中断会话时，再选择 `start` 或重启，不把 kill/start 当作常规检测步骤。

## 3. USB 没目标

- host 是否枚举 USB？Linux 用 `lsusb` 比较接线前后。无枚举先检查供电、数据线、实际 USB device/OTG 接口和完整开机。
- 已枚举但用户无访问权限？核对该 USB 节点的权限和实际 VID/PID；获准后配置匹配设备的 udev/group。
- 已有访问但 HDC 无目标？核对镜像 debug 开关、hdcd、USB gadget 与 host 版本。必要时从已存在的控制台读设备状态，不先开 root 或重启板子。

不复制 README 示例的 VID/PID，不 `chmod -R 777 /dev/bus/usb`。确需 udev 规则时，使用该主机实际存在的用户组和真实设备标识，例如：

```udev
SUBSYSTEM=="usb", ATTR{idVendor}=="<actual-vid>", ATTR{idProduct}=="<actual-pid>", MODE="0660", GROUP="<actual-group>", TAG+="uaccess"
```

重新加载规则及连接属于后续修复，不由查看 skill 自动执行。root 对比枚举仅在授权允许且必要时用作诊断，不把 sudo HDC 当作长期方案；root 启动的 server 还可能与普通用户版本/权限混杂。

## 4. TCP 没目标或超时

按顺序检查：设备已有正确 IP → 主机到设备路由/端口可达 → 设备 hdcd 实际监听 → tconn 使用该监听端口 → 必要的授权/认证 → 目标列表。

能 ping 不证明端口开放；没有 ping 回复也不能单独证明所有 TCP 不可达。区分主机 server 端口与设备监听端口。tconn 成功不等于 TCP 模式永久配置已完成。

若 USB 正常而 TCP 失败，用 USB 读取网络/监听状态；只在用户要 TCP 调试时配置 tmode。不要为了诊断关闭防火墙、永久写 persist 参数或开放所有网卡。

## 5. 传输或安装失败

检查源文件、目标选择、路径层级、权限、空间、文件大小及校验值。`read-only file system` 不等于必须 remount，项目产物应优先部署到其可写目录。

传输可用但应用失败：查看安装返回的系统错误，确认包、签名、版本、共享依赖和用户。原生程序无法启动则检查目标 ABI、解释器/动态库；这属于程序运行问题，不证明 HDC 传输失败。

## 6. shell、日志或转发失败

- shell pipeline/变量展开落在错误机器：核对引号边界和远端退出标记。
- 日志命令不结束：区分流式/一次性模式，用超时或显式结束；别用 tail 限行假装上游流已结束。
- 端口任务存在但业务不可达：核对 fport/rport 方向、服务监听、host 监听接口和端点类型。
- 任务冲突：先列映射，删除自己的具体 task；不清空他人的全部映射。

定位到一层后只改这一层，并验证原失败命令。不要重复整套恢复流程或在证据不足时扩大系统变更。
