# Skill 同步指南

OpenClaw 不会自动读取 Git 仓库里的 Skill 文件。你需要把 `daily-task-manager/` **复制**到 OpenClaw 实际加载 Skill 的目录，并修改其中的路径占位符。

## 源文件位置

本仓库中 Skill 源目录：

```
openclaw-life-assistant-tools/daily-task-manager/
├── SKILL.md       # 主 Skill：命令路由、安全规则
└── REMINDERS.md   # 定时提醒附录：cron 创建规范
```

**原则：** 仓库里是源文件；OpenClaw 运行的是副本。更新 Skill 后需重新复制并重启 gateway。

## OpenClaw 可能加载 Skill 的目录

根据你的 OpenClaw 安装，Skill 可能位于以下之一（或同时存在，以你的配置为准）：

| 类型 | 典型路径 |
|------|----------|
| 全局 plugin-skills | `C:\Users\<You>\.openclaw\plugin-skills\daily-task-manager\` |
| workspace skills | `C:\Users\<You>\.openclaw\life_assistant\skills\daily-task-manager\` |

请将 `<You>` 替换为你的 Windows 用户名。

## 复制 Skill（PowerShell）

### 同步到 plugin-skills

```powershell
$RepoRoot = "E:\path\to\openclaw-life-assistant-tools"
$SkillName = "daily-task-manager"
$Dst = Join-Path $env:USERPROFILE ".openclaw\plugin-skills\$SkillName"

New-Item -ItemType Directory -Force -Path $Dst | Out-Null
Copy-Item -Path "$RepoRoot\$SkillName\*" -Destination $Dst -Recurse -Force

Write-Host "Synced to: $Dst"
```

### 同步到 workspace skills

```powershell
$RepoRoot = "E:\path\to\openclaw-life-assistant-tools"
$SkillName = "daily-task-manager"
$Dst = Join-Path $env:USERPROFILE ".openclaw\life_assistant\skills\$SkillName"

New-Item -ItemType Directory -Force -Path $Dst | Out-Null
Copy-Item -Path "$RepoRoot\$SkillName\*" -Destination $Dst -Recurse -Force

Write-Host "Synced to: $Dst"
```

### 一键同步到两处（可选）

```powershell
$RepoRoot = "E:\path\to\openclaw-life-assistant-tools"
$SkillName = "daily-task-manager"
$Targets = @(
    (Join-Path $env:USERPROFILE ".openclaw\plugin-skills\$SkillName"),
    (Join-Path $env:USERPROFILE ".openclaw\life_assistant\skills\$SkillName")
)

foreach ($Dst in $Targets) {
    New-Item -ItemType Directory -Force -Path $Dst | Out-Null
    Copy-Item -Path "$RepoRoot\$SkillName\*" -Destination $Dst -Recurse -Force
    Write-Host "Synced: $Dst"
}
```

## 修改路径占位符

复制后，编辑目标目录中的 `SKILL.md`，将 `<PROJECT_ROOT>` 全部替换为你的 Python 工具根目录，例如：

```
C:\Users\YourName\daily_task_manager
```

**必须修改的引用：**

- `scripts\run.cmd` 完整路径
- `data\taie\TAIE.xmind`
- `data\life\TODAY.md`
- `data\reminders\timed_reminders.json`
- `config\paths.json`

`REMINDERS.md` 一般不含硬编码路径，通常无需修改。

## 重启 OpenClaw gateway

Skill 文件变更后必须重启 gateway 才会生效：

```powershell
# 若已安装 openclaw CLI
openclaw gateway restart
```

或通过你的 OpenClaw 服务管理界面重启。

## 验证 Skill 是否生效

### 1. 检查文件是否到位

```powershell
Get-ChildItem "$env:USERPROFILE\.openclaw\plugin-skills\daily-task-manager"
# 应看到 SKILL.md、REMINDERS.md
```

### 2. 检查 SKILL.md 路径

```powershell
Select-String -Path "$env:USERPROFILE\.openclaw\plugin-skills\daily-task-manager\SKILL.md" -Pattern "PROJECT_ROOT"
```

不应再出现未替换的 `<PROJECT_ROOT>`。

### 3. 对话测试

在 OpenClaw 中发送：

| 你说 | 期望 Agent 行为 |
|------|----------------|
| 「检查一下任务系统」 | 执行 `run.cmd check --json` |
| 「记一下：明天测试 Skill」 | 执行 `capture --text "..." --json` |
| 「今天做什么」 | 执行 `today --json`，回复含 `next_step` |

### 4. 确认 Agent 未手改文件

Agent 应只通过 `exec` 调用 `run.cmd`，不应直接 `write` 到 `TASKS.md`。

若 Agent 仍直接编辑 Markdown，检查：

- Skill 是否加载（gateway 日志）
- 是否有其他冲突 Skill
- `SKILL.md` 中安全规则是否被覆盖

## 更新 Skill 的流程

1. 在 Git 仓库中修改 `daily-task-manager/`
2. 重新执行上述 Copy-Item 同步
3. 再次替换 `<PROJECT_ROOT>`（若 SKILL.md 有更新）
4. 重启 gateway
5. 对话复测

## 与 Python 工具的关系

```
用户对话
   ↓
OpenClaw Agent（daily-task-manager Skill）
   ↓ exec
<PROJECT_ROOT>\scripts\run.cmd
   ↓
Python CLI（读写 Markdown / JSON）
   ↓
本机 data/ 目录
```

Skill 负责「意图 → 命令」；Python 负责「确定性文件操作」。两者通过 `run.cmd` 衔接，路径必须在两侧一致。
