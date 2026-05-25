# 安装指南

本文档说明从零安装 Daily Task Manager 的完整步骤。假设你已克隆本仓库到本地。

## 1. 克隆仓库

```powershell
git clone <your-repo-url> openclaw-life-assistant-tools
cd openclaw-life-assistant-tools
```

## 2. 决定安装目录

你有两种部署方式：

| 方式 | 说明 |
|------|------|
| **A. 仓库内运行** | 直接在 `daily_task_manager/` 下配置，`PROJECT_ROOT` 指向该目录 |
| **B. 分离部署** | 将 `daily_task_manager/` 复制到如 `C:\Users\YourName\daily_task_manager`，与 Git 仓库分离 |

推荐 **B**：运行数据与代码仓库分离，升级代码时不影响任务数据。

```powershell
# 方式 B 示例
$ProjectRoot = "C:\Users\YourName\daily_task_manager"
Copy-Item -Recurse -Force .\daily_task_manager\* $ProjectRoot
cd $ProjectRoot
```

## 3. 创建 Python 虚拟环境

项目仅使用 Python 标准库，无需 `pip install`。

```powershell
python -m venv C:\Users\YourName\.venvs\life_assistant
C:\Users\YourName\.venvs\life_assistant\Scripts\Activate.ps1
python --version   # 建议 3.10+
```

## 4. 复制 example 配置

### 自动初始化（推荐）

在 `daily_task_manager` 目录（或你的 `$ProjectRoot`）执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\init.ps1 -ProjectRoot "C:\Users\YourName\daily_task_manager"
```

脚本会：

- 创建 `data/life`、`data/taie`、`logs`、`backup` 等目录
- 复制 `config/paths.example.json` → `config/paths.json`（若不存在）
- 复制示例 Markdown / JSON 到 `data/`（若不存在）
- 复制 `run.cmd.example` → `run.cmd`（若不存在）

### 手动复制

```powershell
Copy-Item config\paths.example.json config\paths.json
Copy-Item scripts\run.cmd.example scripts\run.cmd
Copy-Item examples\sample_TASKS.md data\life\TASKS.md
Copy-Item examples\sample_BACKLOG.md data\life\BACKLOG.md
```

## 5. 修改 paths.json

用编辑器打开 `config/paths.json`，将所有 `C:\Users\YourName\daily_task_manager` 替换为你的实际 `$ProjectRoot`。

注意 JSON 中反斜杠需转义：`\\`

```json
{
  "timezone": "Asia/Shanghai",
  "root": "C:\\Users\\YourName\\daily_task_manager",
  "life_dir": "C:\\Users\\YourName\\daily_task_manager\\data\\life",
  ...
}
```

## 6. 修改 run.cmd

编辑 `scripts/run.cmd`：

```bat
set "ROOT=C:\Users\YourName\daily_task_manager"
set "PYTHON=C:\Users\YourName\.venvs\life_assistant\Scripts\python.exe"
```

`run.cmd` 已在 `.gitignore` 中，不会误提交。

## 7. 初始化目录（若未用 init.ps1）

手动创建：

```powershell
$Root = "C:\Users\YourName\daily_task_manager"
@(
  "$Root\data\life",
  "$Root\data\taie",
  "$Root\data\archive\daily_done",
  "$Root\data\reminders",
  "$Root\logs",
  "$Root\backup"
) | ForEach-Object { New-Item -ItemType Directory -Force -Path $_ }
```

## 8. 运行 check

```powershell
cd C:\Users\YourName\daily_task_manager
scripts\run.cmd check
```

期望输出：

```
check_result: ok
```

若失败，会列出 `missing` 项。常见原因：

- `paths.json` 路径未改全
- `data/life/TASKS.md` 等文件不存在 → 从 `examples/` 复制
- `TAIE.xmind` 不存在 → 可选；没有时 `taie-red` 会失败，但不影响其他命令

JSON 模式：

```powershell
scripts\run.cmd check --json
```

## 9. 同步 Skill 到 OpenClaw

见 [SKILL_SYNC.md](SKILL_SYNC.md)。

简要步骤：

```powershell
$RepoRoot = "C:\path\to\openclaw-life-assistant-tools"
$SkillDst = "$env:USERPROFILE\.openclaw\plugin-skills\daily-task-manager"
New-Item -ItemType Directory -Force -Path $SkillDst | Out-Null
Copy-Item -Path "$RepoRoot\daily-task-manager\*" -Destination $SkillDst -Recurse -Force
```

同步后编辑 `$SkillDst\SKILL.md`，将所有 `<PROJECT_ROOT>` 替换为你的实际路径。

## 10. 重启 OpenClaw gateway

重启方式取决于你的 OpenClaw 安装。常见：

```powershell
# 若使用 openclaw CLI
openclaw gateway restart
```

或在 OpenClaw 管理界面重启 gateway 服务。

## 11. 测试常用命令

```powershell
# 记录任务
scripts\run.cmd capture --text "测试：明天整理文档" --json

# 今日计划
scripts\run.cmd today --json

# 列出未完成任务
scripts\run.cmd list-tasks --scope unfinished --json

# 完成（用关键词匹配）
scripts\run.cmd done --text "文档" --json

# 备份
scripts\run.cmd backup --json
```

在 OpenClaw 对话中测试：

- 「今天做什么」→ 应触发 `today --json`
- 「记一下：下周买打印机」→ 应触发 `capture --json`

## 下一步

- 放置你的 `data/taie/TAIE.xmind`（若有）
- 阅读 [daily_task_manager/README.md](../daily_task_manager/README.md) 了解 capture 分类与定时提醒
- 阅读 [daily-task-manager/REMINDERS.md](../daily-task-manager/REMINDERS.md) 了解 cron 配置
