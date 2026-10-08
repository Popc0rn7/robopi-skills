# RoboPi Skills

用于维护 RoboPi 相关 agent skills。每个 skill 是一个自包含目录，可独立复制、安装和发布。

## 文件组织

```text
robopi-skills/
├── README.md                  # 仓库入口与 skill 索引
├── .gitignore
├── AGENTS.md                  # 仓库维护与 skill 编写规范
└── skills/
    ├── README.md              # skill 目录说明
    └── <skill-name>/
        ├── SKILL.md           # 必需：触发条件与执行指引
        ├── agents/
        │   └── openai.yaml    # 可选：客户端展示元数据
        ├── references/        # 可选：按需读取的详细文档
        ├── scripts/           # 可选：可执行工具与验证脚本
        └── assets/            # 可选：模板、示例数据及其他静态资源
```

图中的 `<skill-name>` 是结构示例。仅创建实际需要的可选目录。

所有 skill 平铺在 `skills/` 下，使用稳定的目录名作为标识；领域分类通过下面的索引表达，不改变安装路径。skill 内部资源使用相对路径，不依赖仓库根目录或其他 skill 的文件。

## Skill 索引

| Skill | 用途 | 路径 |
| --- | --- | --- |
| `hdc-master` | OpenHarmony HDC 设备接入、文件传输、应用管理与排障 | [skills/hdc-master](skills/hdc-master/SKILL.md) |
| `oh-ros2` | OpenHarmony ROS 2 开发、交叉编译、部署与 DDS 诊断 | [skills/oh-ros2](skills/oh-ros2/SKILL.md) |
| `oh-houmo` | OpenHarmony Houmo NPU 驱动、运行库与推理验证 | [skills/oh-houmo](skills/oh-houmo/SKILL.md) |
| `robopi-wifi` | RoboPi 原生 Wi-Fi 工具部署、热点连接、重连与诊断 | [skills/robopi-wifi](skills/robopi-wifi/SKILL.md) |

## 安装与使用

`skills/` 是源码目录；使用时将整个 skill 目录安装到客户端的发现路径，包括 `SKILL.md` 和配套资源。

| 客户端 | 个人级安装目录 | 项目级安装目录 | 显式调用 |
| --- | --- | --- | --- |
| Codex | `~/.agents/skills/` | `<项目>/.agents/skills/` | `$<skill-name>` |
| Claude Code | `~/.claude/skills/` | `<项目>/.claude/skills/` | `/<skill-name>` |

以下以 `hdc-master` 为例，实际操作时替换成索引中的 skill 名称。安装前确认目标目录没有同名 skill。

### Codex 从 GitHub 安装

仓库上传到 GitHub 后，可以在 Codex 对话中使用内置的 skill `skill-installer`：
```text
$skill-installer 安装 https://github.com/Popc0rn7/robopi-skills/tree/main/skills/hdc-master
```

该内置 installer 默认安装到 `$CODEX_HOME/skills/`，通常为 `~/.codex/skills/`，与上面的手动安装路径不同；目标目录已存在时会停止，不会自动覆盖。

`skill-installer` 是 Codex 的内置工具。本仓库目前没有提供统一安装脚本；Claude Code 使用上面的本地复制方式。

### 本地复制安装

在本仓库根目录执行，选择对应客户端的命令。

Codex：

```bash
mkdir -p ~/.agents/skills
cp -R skills/hdc-master ~/.agents/skills/
```

Claude Code：

```bash
mkdir -p ~/.claude/skills
cp -R skills/hdc-master ~/.claude/skills/
```

只在指定项目使用时，将目标目录替换为该项目的 `.agents/skills/` 或 `.claude/skills/`。复制安装后，仓库更新不会自动同步到已安装副本。

### 验证与调用

在 Codex 中运行 `/skills` 查看安装结果，通过 `$hdc-master` 调用。在 Claude Code 中输入 `/hdc-master` 调用。两个客户端也可以根据 skill 的 `description` 自动选择使用。

Codex 会自动发现 skill 的变化；若未出现，重启客户端。Claude Code 安装后可开启新会话验证。

安装目录和调用方式参考 [Codex 官方说明](https://learn.chatgpt.com/docs/build-skills) 与 [Claude Code 官方说明](https://code.claude.com/docs/en/skills)。

## 跨客户端兼容约定

- Codex 与 Claude Code 共用 `skills/<skill-name>/` 中的一份源码。
- `SKILL.md` 的 frontmatter 包含通用字段 `name` 和 `description`，其中 `name` 与目录名一致。
- 流程正文使用通用操作描述和相对资源路径；避免依赖某一客户端专属的工具名称、动态命令注入或子 agent 配置。
- `agents/openai.yaml` 是 Codex 的可选客户端元数据，不作为通用流程的运行前提。
- 安装 skill 不等于安装其外部依赖；所需 SDK、HDC、Python 等工具及环境配置应在各 skill 中明确说明。

## 新增与维护

1. 在 `skills/` 下创建使用小写字母、数字与连字符的目录。
2. 编写 `SKILL.md`，按需添加文档、脚本和资源。
3. 验证相对链接、脚本行为和运行前提，再更新本页索引。

详细约定见 [仓库维护与编写规范](AGENTS.md)。
