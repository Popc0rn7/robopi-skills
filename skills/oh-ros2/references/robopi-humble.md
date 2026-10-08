# RoboPi Humble 已验证案例

来源：GCOPTER 项目 2026-10-06 至 2026-10-08 的脚本与验收记录。下列版本是历史快照，换镜像或设备时重新检查；不保证当前板端仍具有同样配置。

## 平台快照

- RoboPi RK3588；目标 AArch64/OpenHarmony musl。
- ROS 前缀 `/sys_prod/robot/install`；依赖前缀 `/sys_prod/robot/out`。
- Python 3.12.12、NumPy 2.4.0；Fast DDS 2.6.10；板端 OMPL 1.8。
- 匹配 SDK 示例：Clang 15.0.4、`arm64-v8a`、`c++_shared`。
- 板端缺少完整常规构建工具链；构建与源码保留主机。

直接 source 基础 setup 可能遇到旧 `/mnt/ohos/install` 路径。未有项目入口时，已验证 bootstrap 为：

```sh
export PATH=/sys_prod/robot/out/bin:/sys_prod/robot/install/bin:$PATH
export LD_LIBRARY_PATH=/sys_prod/robot/out/lib:/sys_prod/robot/install/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
export PYTHONPATH=/sys_prod/robot/install/lib/python3.12/site-packages:/sys_prod/robot/out/lib/python3.12/site-packages:/sys_prod/robot/out/lib/python3.12${PYTHONPATH:+:$PYTHONPATH}
export COLCON_CURRENT_PREFIX=/sys_prod/robot/install
. /sys_prod/robot/install/local_setup.sh
unset COLCON_CURRENT_PREFIX
```

域与 RMW 按当前项目选择，bootstrap 不默认开启外部发现。使用项目入口时直接复用其环境脚本，避免叠加多套路径配置。

## GCOPTER 工程实例

当当前工作区确实存在该项目时，可以查：

- `scripts/board/toolchain.cmake`、`build.sh`：SDK、目标搜索根和分阶段构建。
- `prepare.py`：依赖导出、历史路径修正与 SDK 准备。
- `prepare_python.py`：目标 ABI/NumPy 开发信息及工作容器消息源码。
- `package.py`、`deploy.py`：ELF/依赖闭包审计、运行包、校验与备份。
- `ros_env.sh`、`navigation.sh`、`navigation.py`：板端 bootstrap 和 launch 管理。
- `docs/openharmony-backend.md`、`docs/openharmony-sitl-verification.json`：职责拆分与验收范围。

这些文件属于项目，不由 skill 捆绑。若不在该工程，使用本 skill 的通用参考，不要求用户必须提供 GCOPTER。

仅在该工作区、目标和部署已获授权时，可复用完整构建步骤：

```sh
sh scripts/board/setup_host.sh
python3 scripts/board/prepare.py --target "$ROBOPI_TARGET"
sh scripts/board/build.sh probe
python3 scripts/board/prepare_python.py --target "$ROBOPI_TARGET"
sh scripts/board/build.sh python-interfaces
sh scripts/board/build.sh px4
sh scripts/board/build.sh planner
sh scripts/board/build.sh integration
python3 scripts/board/package.py
# 若当前任务包括部署：
python3 scripts/board/deploy.py --target "$ROBOPI_TARGET"
```

`interfaces` 是旧 C/C++-only 阶段，不能替代需要 rclpy 的 `python-interfaces`。
运行目录 `/data/workspace/robot/gcopter/build`、只部署 build 的布局、域 51 以及森林/lidar 默认值都属于本项目选择，不是其他项目默认值。

## 已完成与未完成

已迁移：规划器、项目消息、267 个 PX4 消息、Python mapper/执行桥、launch 与 CLI。消息 native 扩展交叉编译；普通 Python/shell 直接部署；板端复用既有 ROS/第三方库。

历史证据覆盖双向 DDS、同输入规划与合成后端，以及经明确批准的空场景/单墙虚拟飞行和仿真/传输停滞降落。关闭告警仍存在，但测试核对了退出和重启。

Agent 当时仍在主机，未验证板端 Agent 移植。森林虽成为默认场景，但未据此完成森林飞行验收；实际无线断开恢复、GNSS/IMU 融合、SLAM 和真机飞行也未验证。不要把历史通过范围扩展到新设备。
