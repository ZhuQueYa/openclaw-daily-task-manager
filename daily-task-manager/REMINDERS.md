# Daily Task Manager — 定时提醒附录

主 Skill 见 `SKILL.md`。本节仅用于 **明确钟点提醒** 与 **cron 到点**。

## 何时读本文

- 用户话里含明确钟点（`17:00`、`下午5点`、`明天上午9点` 等）→ 先 `capture`，再按 capture JSON 分流
- 无明确钟点（「明天提醒我」「下午提醒我」）→ 任务池，**不建 cron**

## 固定流程

```
第 1 步：capture --text "用户原话" --json
第 2 步：读 mode / cron_required / recurring_required
第 3 步：按下面分支回复（禁止靠记忆）
```

## 分支 A：`mode = task_pool`，`cron_required = false`

- 只回复「已记录到任务池」+ `destination`
- **禁止**创建 cron；**禁止**说「到点我会提醒你」

## 分支 B：`mode = timed_reminder`，`cron_required = true`

- Python **只**写入 `timed_reminders.json`（`cron_created: false`）
- **你必须**在 OpenClaw 创建**一次性** cron，**严格按 capture JSON**：
  - `name` ← `cron_name`
  - `schedule.at` ← `cron_at`（ISO 8601，含时区）
  - `payload.message` ← **`cron_message` 原样**（禁止改写、禁止长 prompt）
  - `payload.lightContext` ← `true`
  - `payload.toolsAllow` ← `["exec"]`（**仅 exec**，禁止 read/write/today）
  - `payload.timeoutSeconds` ← `90`
  - `failureAlert` ← `false`
  - `deleteAfterRun` ← `true`
  - `sessionTarget` ← `isolated`
  - `delivery` ← 当前用户会话 channel + to
- 可参考 JSON 的 **`cron_spec`**（delivery 需补当前会话）
- **禁止** cron message 里写 `--json` 或旧式「请调用 fire-reminder --json」
- 创建成功后才可说「已设置 X 点提醒」
- **cron 创建失败** → 明确说「定时提醒未能生效」，**禁止**假装成功

### 到点执行链（cron 内 agent 只做一步）

1. **exec** 跑 capture JSON 的 **`cron_command`**（**不要加 `--json`**）
2. 读 stdout `deliver:` 行：
   - `NO_REPLY` → 最终回复 **`NO_REPLY`**
   - 否则去掉 `deliver:` 前缀，**原样**为唯一回复
3. **禁止**再跑 `today`、禁止读 TODAY.md、禁止加载 daily-task-manager skill

### 到点回复

- 用户看到 `deliver:` 内容，如：`提醒到点：测试成功。已记录触发。`
- **禁止** cron 阶段展开今日计划或 TAIE 长列表

## 分支 C：`recurring_required = true`

- **先问用户**是否确认重复提醒
- **禁止**自动创建 cron；**禁止**用任务池代替

## 分支 D：`capture_result = failed` 且含「今天的时间已过」

- 告知时间已过期，请改时间
- **禁止**自动创建 cron

## capture 专用

- `--text` **原样**用户原话，不要改写
- 有无 cron **只看 capture JSON**
- `fire-reminder`：**cron 到点禁止 `--json`**

## 用户反馈 ≠ 新提醒

「提醒成功 / 测试成功 / 收到了 / 闭环完毕」→ **不要**再 capture，**不要**建新 cron。只简短确认。

新提醒须含**新时间或新内容**，仍走 capture。

## JSON 关键字段（capture / fire-reminder）

| 字段 | 用途 |
| ---- | ---- |
| `mode` | `task_pool` / `timed_reminder` / `recurring_confirm` |
| `cron_required` | `true` 时必读 `REMINDERS.md` 建 cron |
| `cron_message` `cron_at` `cron_spec` `cron_command` | cron 配置 |
| `cron_created` | 恒 false（Python 未建 cron） |
| fire-reminder stdout | 仅 `deliver: …` 或 `deliver: NO_REPLY` |
