# 消息生成和 Python 原生扩展

ROS Python 消息包不是只有 `.py` 文件。rosidl 同时生成 C/C++ typesupport、序列化支持和 Python native 扩展；使用 rclpy 时需完整匹配目标运行环境。

## 先采集目标 ABI

在已正确初始化的目标 Python 中获取：

```python
import json, sysconfig
print(json.dumps({key: sysconfig.get_config_var(key)
                  for key in ["SOABI", "EXT_SUFFIX", "VERSION"]}))
```

若生成器使用 NumPy，再查询目标 NumPy 版本和 `numpy.get_include()`。导出目标 Python/NumPy 开发头文件与 Python 库；不要使用主机 Ubuntu NumPy 头文件配目标扩展。

主机 Python运行生成器；目标 Python 头文件、库、SOABI 和扩展文件后缀决定板端 ABI。主机解释器不加载目标 rclpy 或编译好的消息扩展。尽量匹配生成工具需要的 Python 版本，并使用与目标 ROS 配套的 rosidl/ament 纯 Python 代码。

## 构建选项按实际生成器核对

已验证 Humble 工程向 CMake 显式传过：

- `Python3_EXECUTABLE` / `PYTHON_EXECUTABLE`：主机解释器。
- `PYTHON_SOABI`：目标 SOABI。
- `PYTHON_INCLUDE_DIR` / `PYTHON_LIBRARY`：目标开发文件。
- `PythonExtra_INCLUDE_DIRS`：目标 Python 与 NumPy include。

这些名称取决于生成器版本，不能假定所有 ROS 版本都使用同一组参数。检查 CMake cache、扩展编译命令和安装路径，确保结果不是主机 SOABI 或主机 `.so`。

仅 C/C++ 消息构建是适用时的优化，不适合需要 rclpy 消息的后端。即使项目自身不生成 Python bindings，预装标准消息的传递库依赖也可能包含 libpython，仍需审计。

## 验证

板端 import 自定义消息，并实际构造、序列化/反序列化；随后验证主机↔板端传输，覆盖数组、多段结构、序号/时间戳等代表性字段。仅 import 或发现话题不证明消息字段兼容。

不直接安装 manylinux/glibc wheel。优先复用镜像已有原生扩展或用目标工具链构建；纯 Python 依赖也需核对 Python 版本和实际依赖。

NumPy 版本差异有时会暴露应用代码行为改变，应修正已证实的兼容问题，不为了 import 方便就把目标基础环境整体换成主机版本。

## PX4 等外部消息源

消息定义与实际生产者固件匹配。可从已工作的容器导出源码并记录校验值，但不能凭“同为 px4_msgs”推断版本兼容。新固件的版本化消息与翻译能力需单独核对；历史工程的消息数量和分支不作为默认值。
