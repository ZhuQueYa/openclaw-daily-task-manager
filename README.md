# OpenClaw Life Assistant — Daily Task Manager

面向 **OpenClaw** 的 Windows 日常任务管理工具包：Python CLI 负责确定性文件读写，OpenClaw Skill 负责识别用户意图并调用 CLI。

> **本仓库只包含代码、Skill 模板与示例配置。** 不包含你的真实任务数据、日志、归档、照片或 TAIE 脑图。使用前请复制 example 配置并修改本机路径。

## 项目简介

Daily Task Manager 是一套「低压力、Markdown 驱动」的个人任务系统，专为与 OpenClaw Agent 配合而设计：

- **Python 工具**（`daily_task_manager/`）：捕获任务、生成今日计划、日切、归档、读取 TAIE 红旗、管理定时提醒 JSON
- **OpenClaw Skill**（`daily-task-manager/`）：告诉 Agent 何时调用哪条 CLI 命令，禁止 Agent 直接手改任务文件

## 解决什么问题

| 痛点 | 本项目的做法 |
|------|-------------|
| Agent 直接改 Markdown 不可控 | 所有变更经 CLI，输出结构化 JSON |
| 任务散落多处 | 统一 `TASKS.md` / `BACKLOG.md` + `paths.json` |
| 今日计划信息过载 | `today` 突出 1–3 项 + `next_step` |
| TAIE 脑图与任务池脱节 | `today` 双向同步 TAIE 红旗 |
| 明确钟点提醒 | `capture` 写入 JSON，Skill 创建 OpenClaw cron |

## 主要功能

- **任务捕获** `capture`：按自然语言分类到 Today / Tomorrow / Scheduled / Backlog 等
- **今日计划** `today`：生成 `TODAY.md`，同步 TAIE 红旗
- **任务查询** `list-tasks`：按 scope 列出未完成任务
- **完成归档** `done`：移出 TASKS 并写入 `daily_done`
- **日切** `rollover`：Tomorrow → Today，Scheduled 过期 → Overdue
- **定时提醒** `timed_reminders.json` + OpenClaw cron + `fire-reminder`
- **TAIE 读取** `taie-red`：从 `.xmind` 读取红旗任务
- **健康检查** `check` / **备份** `backup`

## 项目结构

```
openclaw-life-assistant-tools/
├── README.md                    # 本文件
├── .gitignore
├── docs/
│   ├── INSTALL.md               # 详细安装步骤
│   ├── SKILL_SYNC.md            # Skill 同步到 OpenClaw
│   └── PROJECT_STRUCTURE.md     # 目录说明
├── daily-task-manager/          # OpenClaw Skill 源文件
│   ├── SKILL.md
│   └── REMINDERS.md
└── daily_task_manager/          # Python CLI 工具
    ├── app/                     # Python 模块
    ├── config/
    │   └── paths.example.json   # 复制为 paths.json 后使用
    ├── examples/                # 示例 Markdown / JSON
    ├── scripts/
    │   ├── run.cmd.example      # 复制为 run.cmd 后使用
    │   └── init.ps1             # 首次初始化脚本
    └── README.md                # CLI 命令参考
```

运行时目录（**不提交 GitHub**，见 `.gitignore`）：

```
<PROJECT_ROOT>/
├── config/paths.json            # 本机真实配置
├── data/life/*.md               # 任务 Markdown
├── data/taie/TAIE.xmind         # 可选脑图
├── data/reminders/              # timed_reminders.json
├── data/archive/daily_done/     # 完成归档
├── logs/
└── backup/
```

## 环境要求

- **操作系统：** Windows 10/11
- **Python：** 3.10+（仅标准库，无第三方依赖）
- **OpenClaw：** 已安装并可运行 gateway（用于 Skill 与 cron 提醒）
- **可选：** XMind 格式的 TAIE 脑图

## 快速安装

详细步骤见 [docs/INSTALL.md](docs/INSTALL.md)。

```powershell
# 1. 克隆仓库
git clone <your-repo-url> openclaw-life-assistant-tools
cd openclaw-life-assistant-tools

# 2. 选择安装目录（可与仓库分离，也可直接用仓库内 daily_task_manager）
$ProjectRoot = "C:\Users\YourName\daily_task_manager"

# 3. 复制工具文件到安装目录（若分离部署）
# 或直接在仓库内 daily_task_manager 目录操作

# 4. 创建虚拟环境并安装（无 requirements.txt，标准库即可）
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 5. 初始化目录与示例配置
cd daily_task_manager
powershell -ExecutionPolicy Bypass -File scripts\init.ps1 -ProjectRoot $ProjectRoot

# 6. 编辑 config\paths.json 与 scripts\run.cmd

# 7. 健康检查
scripts\run.cmd check
```

## 配置步骤

1. 复制 `config/paths.example.json` → `config/paths.json`
2. 将所有路径改为你的 `<PROJECT_ROOT>`（Windows 反斜杠需写成 `\\`）
3. 复制 `scripts/run.cmd.example` → `scripts/run.cmd`，设置 `ROOT` 与 `PYTHON`
4. 可选：将 `examples/sample_*.md` 复制到 `data/life/` 作为起点
5. 可选：放置 `data/taie/TAIE.xmind`
6. 运行 `scripts\run.cmd check` 确认路径正确

## OpenClaw Skill 安装 / 同步

Skill 源文件在 `daily-task-manager/`。同步到 OpenClaw 后，**必须**把 `SKILL.md` 里的 `<PROJECT_ROOT>` 替换为本机路径。

详见 [docs/SKILL_SYNC.md](docs/SKILL_SYNC.md)。

```powershell
# 示例：复制到 plugin-skills
$Src = ".\daily-task-manager"
$Dst = "$env:USERPROFILE\.openclaw\plugin-skills\daily-task-manager"
New-Item -ItemType Directory -Force -Path $Dst | Out-Null
Copy-Item -Path "$Src\*" -Destination $Dst -Recurse -Force
# 然后重启 OpenClaw gateway
```

## Python 工具如何运行

**唯一入口：**

```bat
<PROJECT_ROOT>\scripts\run.cmd <命令> [参数] [--json]
```

- Python 代码只读 `config/paths.json`，不写死业务路径
- 默认输出简洁文本；加 `--json` 得结构化结果
- Markdown 使用 UTF-8 BOM（`utf-8-sig`），避免 PowerShell 乱码

OpenClaw Agent **不应**直接编辑 `data/life/*.md`，应通过 Skill 调用上述命令。

## 常用命令示例

```bat
scripts\run.cmd check
scripts\run.cmd capture --text "明天整理周报" --json
scripts\run.cmd today --json
scripts\run.cmd list-tasks --scope unfinished --json
scripts\run.cmd done --text "周报" --json
scripts\run.cmd rollover --json
scripts\run.cmd taie-red --json
scripts\run.cmd backup --json
scripts\run.cmd list-reminders --json
```

**推荐工作流：**

1. 早晨：`rollover` → `today` → 告知用户 `next_step`
2. 随时：`capture --text "..."`  
3. 完成：`done --text "关键词"`
4. 睡前：`backup`

完整命令说明见 [daily_task_manager/README.md](daily_task_manager/README.md)。

## 数据和隐私说明

| 类型 | 是否包含在本仓库 |
|------|-----------------|
| Python 源码 | ✅ 包含 |
| Skill 模板 | ✅ 包含 |
| 示例配置 / 示例 Markdown | ✅ 包含 |
| 真实 `paths.json` | ❌ 已 `.gitignore` |
| 真实 `TASKS.md` / `TODAY.md` / `BACKLOG.md` 等 | ❌ 已 `.gitignore` |
| `timed_reminders.json` | ❌ 已 `.gitignore` |
| 日志 / 备份 / 归档 | ❌ 已 `.gitignore` |
| `TAIE.xmind` 及个人文件 | ❌ 已 `.gitignore` |
| Token / webhook / 密码 | ❌ 不应出现在仓库中 |

所有个人运行数据保留在你本机 `<PROJECT_ROOT>`，不会随 Git 上传。

## 本机路径配置

以下文件含本机路径，**不应提交**，请使用 example 版本：

| 文件 | 说明 |
|------|------|
| `config/paths.json` | 从 `paths.example.json` 复制 |
| `scripts/run.cmd` | 从 `run.cmd.example` 复制 |
| `daily-task-manager/SKILL.md`（同步后） | 将 `<PROJECT_ROOT>` 替换为实际路径 |

## 故障排查

| 现象 | 检查 |
|------|------|
| `check_result: failed` | 编辑 `paths.json`，确认目录存在；运行 `init.ps1` |
| `taie_read_result: failed` | 确认 `TAIE.xmind` 路径正确且文件存在 |
| Skill 不触发 CLI | 确认 Skill 已同步、gateway 已重启、路径已替换 |
| 定时提醒不响 | 确认 `capture --json` 中 `cron_required: true` 后 Skill 已创建 cron |
| 中文乱码 | 使用 `run.cmd` 入口；终端设为 UTF-8 |
| `python` 找不到 | 在 `run.cmd` 中写虚拟环境完整路径 |

## 适合人群

- 已在用 **OpenClaw** 作为日常助手，希望任务管理「可控、可审计」
- 偏好 **Markdown + 本地文件**，不想引入数据库
- 使用 **TAIE / XMind** 管理长期目标，需要与今日任务池联动
- 接受 **Windows + Python 标准库** 技术栈

## 后续计划

- [ ] 更多 Life Assistant 工具（新闻、英语、摄影等）统一发布
- [ ] 提供 `topics.json` 等扩展配置示例
- [ ] Linux/macOS 启动脚本（当前以 Windows 为主）
- [ ] 一键 Skill 同步脚本

## 相关文档

- [docs/INSTALL.md](docs/INSTALL.md) — 逐步安装
- [docs/SKILL_SYNC.md](docs/SKILL_SYNC.md) — Skill 同步与验证
- [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) — 目录与忽略规则
- [daily_task_manager/README.md](daily_task_manager/README.md) — CLI 命令参考

## 许可证

发布前请自行添加 LICENSE 文件（当前仓库未包含）。
