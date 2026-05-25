---
name: daily-task-manager
description: >-
  日常任务、提醒、今日计划、日切、TAIE、定时提醒、未完成任务、Backlog。
  必须用 <PROJECT_ROOT>\scripts\run.cmd；禁止手改 TASKS/TODAY/提醒 JSON。
  每次一条命令、加 --json；钟点提醒见 REMINDERS.md；禁止凭记忆列任务。
---

# Daily Task Manager

> **路径说明：** 下文 `<PROJECT_ROOT>` 请替换为你本机 daily_task_manager 安装目录，例如 `C:\Users\YourName\daily_task_manager`。同步 Skill 后务必修改本节与 `REMINDERS.md` 中的路径。

## 1. When to use

- 今天做什么 / 今天计划 / 我上班了
- 今天未完成 / 还有什么没做 / 当前任务 / Backlog / 明天 / 排期
- 提醒我 / 记一下 / X 点提醒我（含明确钟点）
- 做完了、日切、TAIE 红旗、备份、检查

## 2. Do not use when

- 早报、新闻 → `news-pusher`
- 英语积累、复习、跟读 → `english-learning`
- 摄影 temp 整理 → `photography-manager`
- 个人资料 inbox → `personal-library-manager`

## 3. Fixed paths

| 用途 | 路径 |
| ---- | ---- |
| 唯一入口 | `<PROJECT_ROOT>\scripts\run.cmd` |
| TAIE | `<PROJECT_ROOT>\data\taie\TAIE.xmind` |
| 今日计划（工具生成后只读） | `<PROJECT_ROOT>\data\life\TODAY.md` |
| 定时提醒 | `<PROJECT_ROOT>\data\reminders\timed_reminders.json` |
| 配置 | `<PROJECT_ROOT>\config\paths.json` |

全局安全见 `SKILL_ROUTER.md`（若你的 OpenClaw 工作区有该文件）。

## 4. Commands / actions

**铁律：** 禁止手改 life/reminders/TAIE；只信 `*_result: ok`；每次 **一条** 命令（日切+计划：`rollover` 再 `today`）。

**执行四步：** 意图 → 复制命令 → 看 JSON → 按 §7 回复。

```bat
<PROJECT_ROOT>\scripts\run.cmd <子命令> [参数] --json
```

| 子命令 | 说明 |
| ------ | ---- |
| `capture --text "用户原话"` | 记录；**有明确钟点** → 读 `REMINDERS.md` |
| `today` | 今日计划（不展开 Backlog/Tomorrow/Scheduled 条目） |
| `list-tasks --scope <scope>` | 查询；见 §5 |
| `done --text "关键词"` | 完成（短关键词） |
| `taie-red` | 全部 TAIE 红旗（用 `title_short`） |
| `rollover` / `backup` / `check` | 日切 / 备份 / 检查 |
| `list-reminders` / `cancel-reminder --id <id>` | 提醒列表 / 取消 |
| `fire-reminder --id <id>` | **cron 到点专用，禁止 --json** |

完整命令列表见下（复制用，记得替换 `<PROJECT_ROOT>`）：

```bat
<PROJECT_ROOT>\scripts\run.cmd capture --text "..." --json
<PROJECT_ROOT>\scripts\run.cmd today --json
<PROJECT_ROOT>\scripts\run.cmd list-tasks --scope today --json
<PROJECT_ROOT>\scripts\run.cmd list-tasks --scope active --json
<PROJECT_ROOT>\scripts\run.cmd list-tasks --scope unfinished --json
<PROJECT_ROOT>\scripts\run.cmd list-tasks --scope all --json
<PROJECT_ROOT>\scripts\run.cmd list-tasks --scope backlog --json
<PROJECT_ROOT>\scripts\run.cmd list-tasks --scope tomorrow --json
<PROJECT_ROOT>\scripts\run.cmd list-tasks --scope scheduled --json
<PROJECT_ROOT>\scripts\run.cmd list-tasks --scope next --json
<PROJECT_ROOT>\scripts\run.cmd list-tasks --scope overdue --json
<PROJECT_ROOT>\scripts\run.cmd list-tasks --scope waiting --json
<PROJECT_ROOT>\scripts\run.cmd taie-red --json
<PROJECT_ROOT>\scripts\run.cmd done --text "..." --json
<PROJECT_ROOT>\scripts\run.cmd rollover --json
<PROJECT_ROOT>\scripts\run.cmd backup --json
<PROJECT_ROOT>\scripts\run.cmd check --json
<PROJECT_ROOT>\scripts\run.cmd list-reminders --json
<PROJECT_ROOT>\scripts\run.cmd cancel-reminder --id <id> --json
<PROJECT_ROOT>\scripts\run.cmd fire-reminder --id <reminder_id>
```

**明确钟点提醒：** 先 `capture`，再按 **`REMINDERS.md`** 建 cron（禁止靠聊天记忆）。

## 5. Decision table

| 用户说法 | 命令 | 注意 |
| -------- | ---- | ---- |
| 今天做什么 / 我上班了 | `today` | Tomorrow/Scheduled/Backlog **只报条数** |
| 今天还有什么没做 | `list-tasks --scope today` | 仅 Today/Active + Overdue |
| 现在能做什么 / 接下来 | `list-tasks --scope active` | + Next Round |
| 全部未完成 | `list-tasks --scope unfinished` | **不含** Backlog |
| 包括 Backlog / 堆积任务 | `list-tasks --scope all` | 仅用户明确要时 |
| Backlog / 明天 / 排期 | `scope backlog` / `tomorrow` / `scheduled` | 专用 scope |
| 提醒我 / X 点提醒 | `capture` → `REMINDERS.md` | 反馈「收到了」≠ 新 capture |
| 做完了 XXX | `done --text "关键词"` | |
| TAIE / 红旗 | `taie-red` | 列**全部** `title_short` |
| 日切 | `rollover` | 用户说「新的一天」可先 rollover 再 today |
| 新的一天全流程 | `rollover` → `today` | 各一条 |

**JSON 必看：** 退出码 0 + `*_result: ok`；`capture` 看 `mode`/`cron_required`；`today` 必提 `next_step`；`list-tasks` 只列当前 scope 的 `sections`；`done` 看 `found`。

## 6. Safety rules

- 禁止手改 TASKS/TODAY/BACKLOG/reminders/TAIE/归档
- 禁止凭记忆列任务、TAIE、提醒状态
- 禁止 cron 失败却说「已设置提醒」
- 禁止 `today` 回复里展开完整 Backlog/Tomorrow/Scheduled
- 禁止让用户自己打开 TASKS.md 查任务
- 禁止 cron 里 `fire-reminder --json` 或跑 `today`
- 其余见 `SKILL_ROUTER.md`、`REMINDERS.md`

## 7. Output format

**记录（任务池）：** `已记录到任务池。位置：{destination}`

**今日计划：** 1–3 重点 + TAIE 红旗**全部列出**（`title_short`）+ `下一步：{next_step}`；低能量最多 1+1。

**列表：** `【{scope} · 共 N 条】` + 各分区列完 pending。

**完成：** `好，「{task}」已标记完成` 或 `没匹配到，已记临时完成`。

**定时（登记后）：** 时间 + reminder_id；cron **创建成功**后才说会提醒。

全局成功/失败/待确认模板见 `SKILL_ROUTER.md`。

## 8. Failure handling

```text
没有完成。
失败原因：{error/message}（来自 JSON）
建议下一步：检查路径或重说关键词；勿假装已记录/已完成。
```

- `capture_result: failed` → 说明 `message`，过期时间勿建 cron
- `check_result: failed` → 列 `missing`
- `taie_read_result: failed` → 说读取失败
- 工具未跑或 `*_result` ≠ ok → **禁止**说已处理好
