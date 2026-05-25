# 安装指南

按下面做，大约 **5～10 分钟** 就能用上。全程只需关心 **3 个路径**，不用先搞懂项目目录结构。

---

## 你需要准备

- **Windows 10/11**
- **Python 3.10 或更高**（推荐 3.10 / 3.11 / 3.12）
  - 从 [python.org](https://www.python.org/downloads/) 安装，勾选 **“Add python.exe to PATH”**
  - 安装后验证：
    ```powershell
    python --version
    ```
    应显示 `Python 3.10.x` 或更高（如 `3.12.x`）。低于 3.10 请升级后再继续。
  - 本项目**只用标准库**，不需要 `pip install` 任何第三方包
- **OpenClaw** 已安装，gateway 能正常启动
- 本仓库已克隆到本机

---

## 推荐安装（复制 → 运行 → 填路径 → 完成）

### 第 1 步：克隆仓库

```powershell
git clone https://github.com/ZhuQueYa/openclaw-daily-task-manager.git
cd openclaw-daily-task-manager
```

### 第 2 步：选定工具安装路径

选一个你想长期放工具的文件夹，例如：

```
C:\Users\你的用户名\daily_task_manager
```

下面用 `你的工具路径` 代替这个地址。

> **建议：** 工具与 Git 仓库分开（复制 `daily_task_manager` 到上面路径）。也可以直接在仓库里的 `daily_task_manager` 目录安装，把 `你的工具路径` 写成该目录的完整路径即可。

**若选择「复制到独立目录」：**

```powershell
$ToolPath = "C:\Users\你的用户名\daily_task_manager"
Copy-Item -Recurse -Force .\daily_task_manager\* $ToolPath
```

### 第 3 步：运行安装脚本（一键建目录和示例文件）

```powershell
cd 你的工具路径
powershell -ExecutionPolicy Bypass -File scripts\init.ps1 -ProjectRoot "你的工具路径"
```

脚本会自动：

- 创建 `data\life`、`data\reminders`、`logs` 等文件夹  
- 生成 `config\paths.json`、`scripts\run.cmd`（从示例复制）  
- 放入示例任务文件，方便马上试用  

### 第 4 步：只填 3 处路径

#### ① 工具安装路径

**文件 A：** `config\paths.json`  
把里面所有的 `C:\Users\YourName\daily_task_manager` 改成 `你的工具路径`。  
JSON 里反斜杠要写成双反斜杠，例如：`C:\\Users\\你\\daily_task_manager`。

**文件 B：** `scripts\run.cmd`  
修改这一行：

```bat
set "ROOT=你的工具路径"
```

#### ② Python 解释器路径（须为 3.10+）

仍在 `scripts\run.cmd`，修改：

```bat
set "PYTHON=C:\Users\你的用户名\AppData\Local\Programs\Python\Python312\python.exe"
```

填写前确认版本：

```powershell
& "C:\...\python.exe" --version
```

须为 **3.10 及以上**。不确定安装位置时，执行 `where.exe python`，把输出贴到 `PYTHON=` 后面。  
若你用虚拟环境，填虚拟环境里的 `python.exe` 即可（创建环境时也请用 3.10+：`python -m venv .venv`）。

#### ③ 任务数据位置

**通常不用单独配置。** `init` 已在 `你的工具路径\data\life\` 下建好 `TASKS.md`、`BACKLOG.md` 等。  
只要 `paths.json` 里的路径都指向 `你的工具路径`，数据就会保存在这里。

### 第 5 步：检查安装

```powershell
scripts\run.cmd check
```

看到 **`check_result: ok`** 表示工具侧就绪。

### 第 6 步：安装 OpenClaw Skill

把仓库里的 Skill 复制到 OpenClaw 加载目录（二选一，以你实际 OpenClaw 配置为准）：

```powershell
$RepoRoot = "克隆仓库的完整路径"   # 例如 E:\...\openclaw-daily-task-manager
$SkillDst = "$env:USERPROFILE\.openclaw\plugin-skills\daily-task-manager"

New-Item -ItemType Directory -Force -Path $SkillDst | Out-Null
Copy-Item -Path "$RepoRoot\daily-task-manager\*" -Destination $SkillDst -Recurse -Force
```

用记事本或编辑器打开 **`$SkillDst\SKILL.md`**，把文中所有 `<PROJECT_ROOT>` 替换成 **`你的工具路径`**（与 `run.cmd` 里 `ROOT` 一致）。

### 第 7 步：重启 OpenClaw

```powershell
openclaw gateway restart
```

或在 OpenClaw 管理界面重启 gateway。

### 第 8 步：对话试一句

在 OpenClaw 里说：

> 检查一下任务系统

应返回检查通过。再说：

> 记一下：安装测试任务

> 今天我应该先做什么？

能正常回复，即安装完成。

### 可选：接上 XMind 脑图（联动亮点）

若你用 XMind 管理长期目标，可把脑图复制到：

```
你的工具路径\data\taie\TAIE.xmind
```

在脑图节点上标 **红旗** 表示当前要推进的事。之后对 OpenClaw 说「今天做什么」，红旗会自动进今日任务池和 `TODAY.md`，无需每天手抄。

试一句：

> 脑图里有哪些红旗？

有文件且格式正确时会列出；没有脑图可跳过，不影响其他功能。

---

## 安装完成后你会得到什么

| 位置 | 作用 |
|------|------|
| `你的工具路径\data\life\` | 任务 Markdown（TASKS、TODAY、BACKLOG 等） |
| `你的工具路径\data\reminders\` | 定时提醒数据 |
| `你的工具路径\config\paths.json` | 本机路径配置（勿提交 Git） |
| OpenClaw Skill 目录 | Agent 如何理解你的话并调用工具 |

日常使用：**只和 OpenClaw 说话**，不必手动编辑这些文件。

---

## 手动安装（不用 init 脚本时）

适合想完全自己掌控每一步的用户。

1. 创建 `你的工具路径`，把仓库中 `daily_task_manager` 下的 `app`、`config`、`scripts`、`examples` 复制过去。  
2. 手动创建文件夹：`data\life`、`data\taie`、`data\archive\daily_done`、`data\reminders`、`logs`、`backup`。  
3. 复制 `config\paths.example.json` → `config\paths.json`，并改好所有路径。  
4. 复制 `scripts\run.cmd.example` → `scripts\run.cmd`，设置 `ROOT` 和 `PYTHON`。  
5. 从 `examples\` 复制 `sample_TASKS.md` → `data\life\TASKS.md`，`sample_BACKLOG.md` → `BACKLOG.md`（`TODAY.md` 可选）。  
6. 执行 `scripts\run.cmd check`。  
7. 按上文「第 6～8 步」同步 Skill 并重启 gateway。

---

## 故障排查

### Python 版本过低或找不到

| 现象 | 处理 |
|------|------|
| `python --version` 显示 3.9 或更低 | 安装 [Python 3.10+](https://www.python.org/downloads/)，并更新 `run.cmd` 里的 `PYTHON=` |
| `'python' 不是内部或外部命令` | 重装 Python 并勾选 “Add to PATH”，或直接在 `run.cmd` 写 `python.exe` 的完整路径 |

### `check_result: failed`

| 可能原因 | 处理 |
|---------|------|
| `paths.json` 路径写错或未改成你的用户名 | 全文搜索 `YourName`，全部替换；注意 `\\` |
| `data\life\TASKS.md` 不存在 | 重新运行 `init.ps1`，或从 `examples\` 手动复制 |
| `run.cmd` 里 `PYTHON` 指向错误 | `where.exe python` 核对路径 |
| 在错误目录执行 `run.cmd` | 应在 `你的工具路径` 下执行，或写绝对路径 |

查看详情：

```powershell
scripts\run.cmd check --json
```

### OpenClaw 不调用命令、直接改文件

- Skill 是否复制到正确目录（见 [SKILL_SYNC.md](SKILL_SYNC.md)）  
- `SKILL.md` 里是否还有未替换的 `<PROJECT_ROOT>`  
- 是否已 **重启 gateway**  
- 是否有其他 Skill 与任务管理冲突  

### `taie-red` 失败

可选功能。确认 `data\taie\TAIE.xmind` 存在；没有脑图可忽略，不影响记任务和今日计划。

### 定时提醒不响

记录任务时需带**明确钟点**；Skill 会根据结果创建 OpenClaw cron。详见 [daily-task-manager/REMINDERS.md](../daily-task-manager/REMINDERS.md)。

### 中文乱码

始终通过 `scripts\run.cmd` 调用；PowerShell 终端建议 UTF-8（`chcp 65001`）。

### `git push` 报 `Could not resolve host: github.com`

这是网络/DNS 无法访问 GitHub，与安装无关。换网络、改 DNS 或配置代理后再推送。本地 `commit` 成功后，网络恢复再执行 `git push` 即可。

---

## 下一步

- 在 OpenClaw 里按 [README 示例](../README.md#3-个最常用例子) 试用  
- 更新 Skill 时见 [SKILL_SYNC.md](SKILL_SYNC.md)  
- 需要完整命令列表时见 [daily_task_manager/README.md](../daily_task_manager/README.md)  
- 可选：把 TAIE 脑图放到 `data\taie\TAIE.xmind`
