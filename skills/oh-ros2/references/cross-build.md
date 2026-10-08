# OpenHarmony ROS 2 交叉构建

用于编译 C/C++ 包或建立目标依赖环境。下面的路径变量是角色说明；从项目或当前设备发现实际值。

## 区分三个环境

| 环境 | 作用 | 典型内容 |
|---|---|---|
| 主机工具 | 在构建主机执行 | CMake、Ninja、Python、ament/rosidl 生成工具 |
| OHOS SDK | 决定目标系统与基础 ABI | 官方 toolchain、Clang、系统头文件、libc、C++ runtime |
| 目标 ROS/第三方依赖 | 提供目标包的头文件与链接库 | 板端 ROS、RMW/typesupport、Eigen、OMPL、Python native 库 |

普通 Ubuntu ARM64/glibc 库不能直接用于已验证的 OpenHarmony ARM64/musl 镜像。纯头文件依赖也要核对版本与导出的 CMake 配置。

## 准备依赖

先列出请求包的构建/运行依赖，核对目标设备是否具备。优先复用匹配镜像的导出快照，缺少的包再构建；不要默认整个 ROS 安装都要移植。

导出需要的 include/lib/share 和第三方开发元数据，保留原始快照与校验值。在单独副本中修正旧构建路径，记录修改；不要改板端基础 ROS 安装，也不要把纯主机依赖导成目标依赖。

目标镜像、SDK 或关键 ABI 改变后，不沿用未经核对的 CMake cache 或旧依赖快照。记录 SDK 元数据、库/包版本和源码版本；源码没有 Git 信息时使用文件校验值，不编造提交号。

## 配置构建

引入 SDK 的 `build/cmake/ohos.toolchain.cmake`，目标架构和 C++ runtime 由匹配 SDK 配置。不要仅设置 `CMAKE_SYSTEM_PROCESSOR` 就当作 OHOS 工具链。

常用查找策略：

```cmake
# 先按 SDK 要求设置目标参数，再 include 官方 toolchain。
list(APPEND CMAKE_FIND_ROOT_PATH "${TARGET_ROS_PREFIX}" "${TARGET_DEPS_PREFIX}")
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)
```

显式传入主机 Python/生成器，按依赖顺序安装到目标 overlay。只有目标 package 的库和头文件来自目标前缀；生成器中需要在主机 import 的纯 Python 源码另行匹配。无法在主机执行的目标 ELF/扩展，不能作为探测程序运行；仅在必要时提供有证据的交叉探测结果。

已有 colcon 工作流可传 toolchain 并复用；逐包 CMake/Ninja 也是可选方式，不要求所有项目换成某一种命令。

缺少第三方 CMake 元数据时可以在主机副本中补 imported target，但必须确认库、架构和传递依赖。不要用主机同名包掩盖目标缺失。保留编译命令，检查 link line 和实际解析路径。

## 审计与产物

用 SDK readelf 检查目标 ELF：架构、动态解释器、NEEDED 及 RPATH/RUNPATH。避免嵌入主机路径；有意设计的目标相对 RUNPATH 可保留并验证，不把“完全无 RUNPATH”视为通用要求。

递归解析所有自建 ELF/原生扩展的运行依赖，解析目录只包含包和目标依赖。系统 libc/loader 通常由镜像提供，不随意替换或打包覆盖。

产物至少区分构建树、安装 overlay、可部署 runtime。需要 `ros2 run`/`ros2 launch` 的包同时保留 ament index、share、消息资源和可执行入口；只有二进制不能证明 ROS 包安装完整。

通过编译后，再按授权执行板端加载、消息与业务验证。链接成功不保证运行期 Python ABI、类型支持或 DDS 一致。
