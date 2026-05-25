# 项目目录结构

本文档说明本仓库各目录的用途，以及哪些内容**不应**提交到 GitHub。

## 仓库根目录

```
openclaw-life-assistant-tools/
├── README.md                 # 项目总览与快速开始
├── .gitignore                # 排除运行数据与本地配置
├── docs/                     # 安装、同步、结构说明
├── daily-task-manager/       # OpenClaw Skill 源（≈ skills/）
└── daily_task_manager/       # Python CLI 工具（≈ tools/）
```

> 命名说明：当前目录名为 `daily-task-manager`（Skill）与 `daily_task_manager`（Python），功能上分别对应常见的 `skills/` 与 `tools/` 目录。

## daily-task-manager/ — OpenClaw Skill

| 文件 | 用途 |
|------|------|
| `SKILL.md` | Agent 路由：何时调用哪条 CLI、输出格式、安全规则 |
| `REMINDERS.md` | 明确钟点提醒的 cron 创建与到点执行规范 |

**提交：** ✅ 应提交（使用 `<PROJECT_ROOT>` 占位符，无个人数据）

**不同步到 Git：** 复制到 OpenClaw 后、已替换为本机路径的副本（位于 `~/.openclaw/...`）

## daily_task_manager/ — Python 工具

### app/

Python 源码模块：

| 模块 | 职责 |
|------|------|
| `main.py` | CLI 入口 |
| `config.py` | 读取 `paths.json` |
| `task_capture.py` | 捕获与分类任务 |
| `planner.py` | 生成 TODAY.md |
| `list_tasks.py` | 按 scope 查询 |
| `rollover.py` | 日切逻辑 |
| `archive.py` | 完成归档 |
| `reminders.py` | 定时提醒 JSON |
| `taie_reader.py` | 读取 XMind 红旗 |
| `storage.py` | 文件 I/O |
| `time_parser.py` | 自然语言时间解析 |

**提交：** ✅ 应提交

### config/

| 文件 | 提交 |
|------|------|
| `paths.example.json` | ✅ 示例配置 |
| `paths.json` | ❌ 本机真实路径（已 gitignore） |

### examples/

示例 Markdown 与 JSON，供首次部署复制：

- `sample_TASKS.md`
- `sample_TODAY.md`
- `sample_BACKLOG.md`
- `sample_timed_reminders.json`

**提交：** ✅ 应提交（均为虚构示例数据）

### scripts/

| 文件 | 提交 |
|------|------|
| `run.cmd.example` | ✅ 启动脚本模板 |
| `run.cmd` | ❌ 含本机 Python/ROOT 路径（已 gitignore） |
| `init.ps1` | ✅ 首次初始化脚本 |

### docs/（仓库级）

| 文件 | 用途 |
|------|------|
| `INSTALL.md` | 详细安装 |
| `SKILL_SYNC.md` | Skill 同步 |
| `PROJECT_STRUCTURE.md` | 本文件 |

## 运行时目录（不应提交 GitHub）

以下目录/文件存在于你的 `<PROJECT_ROOT>` 运行环境中，**全部在 `.gitignore` 中**：

```
<PROJECT_ROOT>/
├── config/paths.json              # 真实配置
├── scripts/run.cmd                # 真实启动脚本
├── data/
│   ├── life/
│   │   ├── TASKS.md               # 真实任务
│   │   ├── TODAY.md
│   │   ├── BACKLOG.md
│   │   ├── INBOX.md
│   │   ├── ENERGY_LOG.md
│   │   ├── SHOPPING.md
│   │   ├── RELATIONSHIPS.md
│   │   └── WEEKLY_REVIEWS.md
│   ├── taie/
│   │   └── TAIE.xmind             # 个人脑图
│   ├── reminders/
│   │   └── timed_reminders.json   # 真实提醒
│   └── archive/
│       └── daily_done/            # 完成归档
├── logs/                          # 运行日志
└── backup/                        # 带时间戳的 Markdown 备份
```

### 为何不上传这些

| 类型 | 原因 |
|------|------|
| `TASKS.md` 等 | 个人待办与工作内容 |
| `TAIE.xmind` | 个人目标与思维导图 |
| `timed_reminders.json` | 个人日程 |
| `logs/` | 可能含路径、操作记录 |
| `backup/`、`archive/` | 历史任务快照 |
| `paths.json` | 暴露本机目录结构 |
| 照片/PDF/Office | 个人隐私 |

## .gitignore 策略摘要

- **忽略整个** `daily_task_manager/data/`、`logs/`、`backup/`
- **忽略** `paths.json`、`run.cmd`、`timed_reminders.json`
- **忽略** 二进制个人文件（`.xmind`、图片、视频、Office 等）
- **保留** 源码、`*.example.json`、`examples/`、Skill 模板

运行时目录在首次使用时由 `init.ps1` 创建，或由 Python 写入文件时自动 `mkdir`。

## 代码中的路径约定

| 位置 | 约定 |
|------|------|
| `app/*.py` | 只通过 `load_paths(config)` 读路径，无硬编码 |
| `scripts/run.cmd` | 本机配置，不提交 |
| `SKILL.md` | 使用 `<PROJECT_ROOT>` 占位符 |
| `README.md` / `docs/` | 使用 `C:\Users\YourName\...` 示例路径 |

## 扩展目录（未来）

本仓库后续可能加入其他 Life Assistant 工具，结构可能扩展为：

```
skills/          # 多个 OpenClaw Skill
tools/           # 多个 Python 工具
config/          # 共享配置示例
examples/        # 跨工具示例数据
```

当前版本仅包含 Daily Task Manager 一个工具包。
