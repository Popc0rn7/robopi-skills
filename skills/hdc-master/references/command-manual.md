# HDC 操作手册

覆盖：架构/版本 → 目标与服务 → shell → 文件 → TCP/USB → 转发 → 应用 → 日志/调试 → 高级命令。
示例使用 POSIX 主机 shell；Windows 的引号与主机路径需要相应适配。示例 `<key>`、路径、端口都须替换为实际值，不能直接执行占位符。

命令基线：本机 `hdc -v` 为 **3.2.0g**，2026-10-08 核对了普通及 verbose 帮助。以下设备操作没有因编写手册而执行；帮助存在不代表当前镜像或权限允许该功能。[来源与版本](sources.md)

## 1. 架构、工具与全局参数

client 是每次主机命令，server 是主机后台连接管理，hdcd 是设备守护进程。业务程序是 shell 启动的另一层进程。

```sh
command -v hdc
hdc -v
hdc -h
hdc -h verbose
```

| 参数/命令 | 用途与注意 |
|---|---|
| `-t <key>` | 选择设备；放在业务命令之前 |
| `-s [ip:]port` | 选择/配置主机 HDC server 地址，不是板端 TCP 监听地址 |
| `-l[0-6]` | 当前帮助给出的命令日志级别；其他版本范围可能不同 |
| `checkserver` | 检查 client/server 版本，不检查应用版本 |
| `OHOS_HDC_SERVER_PORT` | 当前帮助的主机 server 端口变量，默认 8710 |
| `OHOS_HDC_LOG_LEVEL` | server 日志变量，与命令 `-l` 的范围未必一致 |

`hdc` 在需要时可启动主机 server。多份 SDK 的可执行文件或 IDE 自带工具可能连接到旧 server；记录可执行文件路径再诊断，不先替换设备镜像。

## 2. 目标、等待和主机服务

```sh
hdc list targets -v
hdc -t '<key>' shell uname -a
hdc -t '<key>' shell param get const.product.name
hdc -t '<key>' shell param get const.product.model
```

只有执行设备 shell 时才需要其工具存在。设备标识以实际 list 输出为准，TCP key 通常包含地址和端口。

| 命令 | 操作范围 |
|---|---|
| `start` | 主机 server |
| `start -r` / `kill -r` | 主机 server 重启；可能中断全部会话 |
| `kill` | 停止主机 server，不是停止单个远端业务进程 |
| `reconnect <key>` | 当前帮助描述为 USB 重连和重新枚举 |
| `-t <key> wait` | 等设备可用；设置外层超时，不无限等待 |
| `discover` | verbose 帮助列出的 TCP 局域网发现；不等于自动授权 |

重启前确认其他开发会话影响，且确实诊断到 server 层；不是固定恢复序列。

## 3. 远端 shell、引号与退出状态

```sh
hdc -t '<key>' shell
hdc -t '<key>' shell 'ps -A'
hdc -t '<key>' shell 'ps -A | grep my_program'
```

最后一个 pipeline 在板端执行；若把 `|` 写在主机引号之外，后段在主机执行。变量、`$()`、重定向也要按预期主机/远端边界处理。任意用户输入应按 shell 参数转义，不用 JSON 编码代替 shell quoting。

脚本式执行可携带退出码标记，例如已确认存在的业务程序：

```sh
hdc -t '<key>' shell '/data/local/tmp/my-project/probe; hdc_rc=$?; printf "\nREMOTE_EXIT:%s\n" "$hdc_rc"'
```

读取标记和实际输出；若需要把远端失败映射成主机失败，由调用脚本检查它。不要假设每个 HDC 版本都可靠地传递远端退出码。检查进程退出需核对目标 PID 和命令行，不用笼统 `pkill python`。

`hdc -t <key> shell -b <bundle-name> ...` 是当前帮助的应用调试目录形式，受包调试属性/权限限制，不等于任意 root shell。

## 4. 文件发送、接收和校验

```sh
hdc -t '<key>' file send './probe' '/data/local/tmp/my-project/probe'
hdc -t '<key>' file recv '/data/local/tmp/my-project/run.log' './run.log'
hdc -t '<key>' shell 'ls -l /data/local/tmp/my-project/probe'
hdc -t '<key>' shell 'sha256sum /data/local/tmp/my-project/probe'
```

先检查目标目录是否存在、可写及有足够空间；按任务创建明确的目录。目录传输先确认落点和层级，避免把同名目录多嵌套一层。接收也可能覆盖本地文件，选择合适输出路径。

发送前记录本地大小/校验值，发送后核对远端；必要时保留旧文件再替换。传输完成不保证执行权限、解释器、ABI 和动态库正确。读写系统分区失败时，不自动 remount，优先用用户指定的可写开发目录。

当前帮助列出 `-a`（时间戳）、`-sync`（新文件更新）、`-m`（mode sync）、`-z`（压缩）、`-cwd`、`-b`。帮助中的选项汇总还出现 `-s`，不能凭缩写推测它等同于 `-sync`；使用时按当前版本说明确认。压缩包通常不需要再 `-z`。

## 5. TCP 与 USB 模式

主机 server 默认端口 8710 和设备 hdcd 的 TCP 端口是**两处独立监听**，不必相同。HDC TCP 可走有线 Ethernet，也可走 Wi-Fi；tmode 不负责配置 IP 或无线连接。

已经有 USB 管理通道，并且用户请求开启设备 TCP 调试时：

```sh
hdc -t '<usb-key>' shell ifconfig
hdc -t '<usb-key>' tmode port 8710
hdc tconn '<device-ip>:8710'
hdc list targets -v
hdc -t '<device-ip>:8710' shell uname -a
```

上述端口仅为示例。确认指定网络/监听范围，保存回退连接方式。`tmode` 可能中断原连接，官方 README 与本地帮助对重启对象的措辞不同，不承诺“设备绝不会受影响”。

| 命令 | 作用 |
|---|---|
| `tconn <ip>:<port>` | 主机连接已监听的设备，不自动在设备开监听 |
| `tconn <ip>:<port> -remove` | 移除主机连接，不代表板端监听已经关闭 |
| `-t <key> tmode usb` | 切换设备模式；连接会变化 |
| `-t <key> tmode port close` | 当前帮助的关闭 TCP 形式，先确认该版本支持 |

收尾核对设备监听和目标列表。不要为了 TCP 失败直接修改 persist 参数或重启设备。当前 verbose 帮助还列出 `OHOS_HDC_ENCRYPT_CHANNEL`，是否可用、配对和访问控制需单独核对，不能把“能连上”当成安全配置完成。

## 6. 端口转发与反向转发

两种方向都需先有对应服务监听；HDC 不替你启动业务服务。

```sh
# 主机访问 localhost:15678 → 板端 TCP 服务 23456
hdc -t '<key>' fport tcp:15678 tcp:23456
# 板端访问本机 TCP 23456 → 主机服务 15678
hdc -t '<key>' rport tcp:23456 tcp:15678
hdc -t '<key>' fport ls
```

| 形式 | 参数顺序 |
|---|---|
| `fport localnode remotenode` | 主机监听端点在前，设备服务端点在后 |
| `rport remotenode localnode` | 设备监听端点在前，主机服务端点在后 |

本机帮助用 `fport ls` 列出正/反转发，用 `fport rm <taskstr>` 删除任务。根据列表确认自己的 task string 再删除；某些版本接受端点对，避免凭记忆删除其他任务。

端点形式还包括 `localfilesystem:`、`localreserved:`、`localabstract:`、`dev:`、`jdwp:`（远端）和 Ark 调试端点。使用前确认当前版本支持和实际服务。不要把 TCP 转发当成 UDP 转发或自动 DDS 多播隧道。

默认 host 转发监听行为按版本核对；verbose 帮助有 `-e <ip>` 选择 host 监听地址，扩大到所有接口会改变服务暴露范围，仅在任务要求时使用。

## 7. 应用安装与卸载

```sh
hdc -t '<key>' install './example.hap'
# 用户请求替换已安装版本时：
hdc -t '<key>' install -r './example.hap'
# 用户请求卸载具体 bundle 时：
hdc -t '<key>' uninstall '<bundle-name>'
```

当前帮助列出 `.hap`、`.hsp`、`.app` 及多包/目录支持；实际依赖和安装策略由系统包管理决定。安装后用镜像支持的 `bm`/应用管理查询，必要时启动指定应用并核对日志，不能仅凭 file send 判断安装完成。

`-s` 表示 shared bundle；`-g` 涉及授予权限；`uninstall -k` 保留数据/缓存，但并不保证业务数据完整。用户只要求安装时不自动卸载旧包或清理数据。

当前帮助把若干 `bm` 附加参数作为同一个引号参数传入，如 `"-u 100"`；使用 `install -h` / `uninstall -h` 等查询形式前结合帮助确认其设备侧行为，不按普通 GNU 参数规则猜测。

## 8. 日志、报告和调试进程

| 入口 | 用途 |
|---|---|
| `-t <key> hilog -h` | 查看该设备日志命令参数 |
| `-t <key> hilog` | 日志流，需要明确结束条件 |
| `-t <key> shell 'hilog -x'` | 已有镜像上的一次性日志形式，先确认支持 |
| `-t <key> shell 'dmesg'` | 内核日志；权限和工具按镜像变化 |
| `-t <key> bugreport <file>` | 收集报告，按当前版本确认输出位置并核对文件 |
| `-t <key> jpid` | JDWP 进程列表，不是所有系统进程 |
| `-t <key> track-jpid` | 持续跟踪调试进程；需超时或显式结束 |

主机有 `timeout` 时可限制流式收集：

```sh
timeout 10 hdc -t '<key>' hilog > './device-hilog.log' 2>&1
```

外层超时结束码要与业务失败区分。筛选时间、tag、PID 或服务应先查看设备支持的参数；设备可能没有 GNU 工具。系统全量报告可能很大，应按任务先收最小相关日志。

## 9. 高级命令和权限边界

| 命令族 | 需要核实的范围 |
|---|---|
| `smode` / `smode -r` | 当前版本的 daemon root/退出 root；老版本可能用其他语法 |
| `target mount` | 系统分区读写能力，非普通开发目录写入 |
| `target boot`、bootloader/recovery/MODE | 设备重启和启动模式，属于中断设备操作 |
| `keygen <file>` | 新认证密钥文件；不要覆盖或公开现有私钥 |
| `spawn-sub` / `killall-sub` | 主机子 server 管理，影响多设备/其他会话 |
| `checkdevice` / `any` | 当前 verbose 帮助注明为 HDC UART 功能，不是通用 USB 自动选板 |
| `update`、`flash`、`erase`、`format`、`sideload` | 系统更新/分区操作；本手册不提供自动刷机步骤 |

HDC UART 是协议传输；板子 debug UART 的串口终端不一定运行 HDC。设备允许 root、flash 或安装 debug 包也取决于镜像构建与授权。

手册提供命令含义不授权执行。需要上述设备变更时先核对用户具体目标、权限、镜像/分区和回退；无法核实则停在说明与诊断。
