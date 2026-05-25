# Daily Task Manager — CLI 参考

> 项目总览与安装见仓库根目录 [README.md](../README.md)。本文档为命令与行为细节参考。

面向 **OpenClaw** 的 Windows 日常任务管理 CLI。Python 负责确定性读写；OpenClaw 只通过 `scripts\run.cmd` 调用命令，不直接改任务文件。

## 原则

| 原则 | 说明 |
|------|------|
| 确定性执行 | 所有任务变更经本 CLI，不由 Agent 自由编辑 Markdown |
| 路径集中 | 业务代码只读 `config\paths.json`，不写死路径 |
| 统一入口 | 一律 `scripts\run.cmd <命令>` |
| 稳定输出 | 默认简洁文本；加 `--json` 得结构化结果 |
| UTF-8 BOM | Markdown 使用 `utf-8-sig`，避免 PowerShell 乱码 |
| 标准库 | 无第三方依赖 |
| TAIE | `.xmind` 用 `zipfile` 读 `content.json` |
| 低压力 | 今日计划突出 1–3 项，不排满清单 |

## 目录结构

```
<PROJECT_ROOT>/
├─ app/           # Python 模块
├─ config/paths.json          # 从 paths.example.json 复制
├─ data/life/     # TASKS / TODAY / BACKLOG 等（运行时，不提交 Git）
├─ data/taie/TAIE.xmind
├─ data/archive/daily_done/
├─ scripts/run.cmd
├─ logs/
└─ backup/
```

## 环境

- Windows
- Python 3.10+（在 `run.cmd` 中配置虚拟环境路径）
- 时区：`config\paths.json` → `Asia/Shanghai`（可改）

首次安装：复制 `config/paths.example.json` 与 `scripts/run.cmd.example`，见 [docs/INSTALL.md](../docs/INSTALL.md)。

## OpenClaw 调用方式

**唯一入口**：

```bat
<PROJECT_ROOT>\scripts\run.cmd <命令> [参数] [--json]
```

建议 OpenClaw 工作流：

1. **早晨**：`rollover` → `today` → 把 `next_step` 告诉用户  
2. **随时记录**：`capture --text "..."`  
3. **查看红旗**：`taie-red`  
4. **完成**：`done --text "关键词"`  
5. **睡前/日切前**：`backup`  
6. **健康检查**：`check`

需要机器解析时，每条命令末尾加 `--json`。

### 命令一览

| 命令 | 示例 | 说明 |
|------|------|------|
| `check` | `run.cmd check` | 检查路径与关键文件 |
| `paths` | `run.cmd paths` | 输出 paths.json |
| `taie-red` | `run.cmd taie-red` | 读取 TAIE **全部**红旗 |
| `capture` | `run.cmd capture --text "..."` | 任务池或**定时提醒** |
| `list-reminders` | `run.cmd list-reminders` | 查看 timed reminders |
| `list-tasks` | `run.cmd list-tasks --scope unfinished` | 按范围列出未完成任务 |
| `fire-reminder` | `run.cmd fire-reminder --id <id>` | 到点触发（由 OpenClaw cron 调用） |
| `cancel-reminder` | `run.cmd cancel-reminder --id <id>` | 取消定时提醒 |
| `today` | `run.cmd today` | 生成 `TODAY.md` |
| `done` | `run.cmd done --text "关键词"` | 完成并归档 |
| `rollover` | `run.cmd rollover` | 日切 |
| `backup` | `run.cmd backup` | 带时间戳备份核心 Markdown |

### list-tasks scope

| `--scope` | 包含分区 |
|-----------|----------|
| `today` | Today / Active、Overdue |
| `active` | Today / Active、Overdue、Next Round |
| `unfinished` | 上述 + Tomorrow、Waiting、Deferred、Scheduled（**不含 Backlog**） |
| `backlog` | 仅 BACKLOG.md |
| `tomorrow` / `next` / `overdue` / `waiting` / `scheduled` | 对应单一分区 |
| `all` | TASKS 全部分区 + Backlog |

### 退出码

- `0`：成功  
- `2`：失败（配置、TAIE 读取、空参数等）

## capture 与定时提醒

含明确钟点（`17:00`、`下午5点` 等）→ 写入 `data\reminders\timed_reminders.json`。  
Python **不**创建 OpenClaw cron；Skill 须按 `REMINDERS.md` 创建一次性 cron。

**cron 到点唯一命令**（不要加 `--json`）：

```bat
<PROJECT_ROOT>\scripts\run.cmd fire-reminder --id <reminder_id>
```

详见 OpenClaw Skill [REMINDERS.md](../daily-task-manager/REMINDERS.md)。

## today / rollover / done

- **today**：双向同步 TAIE 红旗与 TASKS → Today / Active，再生成 TODAY.md  
- **rollover**：Tomorrow → Today；Scheduled 过期 → Overdue  
- **done**：关键词匹配第一个未完成任务，移入 `daily_done/YYYY-MM-DD.md`

## 修改路径

只改 `config\paths.json`，然后执行 `run.cmd check` 验证。

## 禁止事项

- 不自动发消息、不改日历、不下单  
- 不使用数据库  
- OpenClaw 不应直接编辑 `data\life\*.md`，应调用本 CLI  

## 直接调用 Python（调试用）

```bat
cd /d <PROJECT_ROOT>
<PYTHON>\python.exe app\main.py --config config\paths.json check
```

与 `run.cmd` 等价。
