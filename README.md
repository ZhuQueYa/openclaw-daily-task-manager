# OpenClaw 日常任务管理 Skill

**用对话管任务，不用自己改文件。** 装好后，对 OpenClaw 说「记一下」「今天做什么」「做完了」就行。

**环境要求：** Windows 10/11 · **Python 3.10 或更高** · 已安装 OpenClaw（工具仅用 Python 标准库，无需 `pip install`）

---

## 为什么需要它

| 你可能遇到过 | 这个 Skill 的做法 |
|-------------|------------------|
| 任务记在聊天、便签、脑图里，到处找 | 统一进本地 Markdown，OpenClaw 只通过命令读写 |
| Agent 直接改 `TASKS.md`，改乱或改丢 | **禁止手改文件**，所有变更走固定命令，结果可核对 |
| 每天早上不知道先做哪件 | `today` 突出 1～3 件 + 一句「下一步」 |
| 口头说「三点提醒我」容易忘 | 记任务时写入提醒，Skill 帮你对接 OpenClaw 定时 |

你不需要懂 Python、目录结构或 CLI 参数——**OpenClaw 加载 Skill 后，用自然语言即可。**

---

## 它能做什么

- **记任务**：一句话丢进来，自动分到今天 / 明天 / 待办 / 排期等
- **今日计划**：生成「今天先做啥」，信息克制、不刷屏
- **查任务**：今天、本周未完成、Backlog 等，按你说的范围列
- **完成任务**：说关键词就能标记完成并归档
- **日切与备份**：明天的事滚到今天；睡前可备份
- **定时提醒**（可选）：说了具体钟点，会走提醒流程
- **TAIE 脑图联动**（可选）：和 XMind 里的红旗任务同步

数据都在你本机，**不会**随 Git 上传（见 [隐私说明](#隐私说明)）。

---

## 30 秒快速安装

> 详细步骤、手动安装和排错见 **[安装指南](docs/INSTALL.md)**。

**环境：** Windows 10/11 · **Python 3.10+**（安装后运行 `python --version` 确认）· 已安装 OpenClaw

```
复制命令 → 运行安装脚本 → 填 3 处路径 → 同步 Skill → 完成
```

```powershell
# 1. 克隆
git clone https://github.com/ZhuQueYa/openclaw-daily-task-manager.git
cd openclaw-daily-task-manager

# 2. 一键初始化（把路径改成你的）
powershell -ExecutionPolicy Bypass -File daily_task_manager\scripts\init.ps1 -ProjectRoot "C:\Users\你的用户名\daily_task_manager"

# 3. 填路径（见下方「只需配置 3 处」）

# 4. 检查是否就绪
C:\Users\你的用户名\daily_task_manager\scripts\run.cmd check
```

**只需配置 3 处：**

| 配置什么 | 填在哪里 | 示例 |
|---------|---------|------|
| 工具安装路径 | `config\paths.json` 里所有路径、`scripts\run.cmd` 的 `ROOT` | `C:\Users\你\daily_task_manager` |
| 任务数据位置 | 一般与工具同目录下的 `data\life\`（`init` 已建好） | 同上，无需单独选文件夹 |
| OpenClaw Skill 目录 | 把 `daily-task-manager\` 复制到 OpenClaw 的 Skill 目录，并改 `SKILL.md` 里的路径 | `%USERPROFILE%\.openclaw\plugin-skills\daily-task-manager` |

同步 Skill 后**重启 OpenClaw gateway**。看到 `check_result: ok` 就可以开始用。

---

## 3 个最常用例子

### 1. 记一条带时间的任务

**你说：**

> 帮我记录一个明天下午三点提交材料的任务

**OpenClaw 会：** 调用「记录任务」，把你的原话写进任务池；若有明确钟点，会按 Skill 规则处理提醒。

**你会得到：** 任务已记下，属于明天/排期；需要时会提示是否设提醒。

---

### 2. 今天先做什么

**你说：**

> 今天我应该先做什么？

**OpenClaw 会：** 必要时先做日切，再生成今日计划。

**你会得到：** 1～3 件重点 + 一句建议的「下一步」，而不是整页任务清单。

---

### 3. 完成 / 查看任务

**你说：**

> 把这个任务标记为完成  
> 查看本周还没完成的任务

**OpenClaw 会：** 用关键词匹配完成并归档；或按范围列出未完成任务。

**你会得到：** 完成确认，或一份按你要求筛选的列表（来自真实文件，不是 Agent 凭记忆编造）。

---

## OpenClaw 怎么使用它

1. **安装并同步 Skill**（见 [docs/INSTALL.md](docs/INSTALL.md)）
2. **重启 gateway**，确保 Skill 已加载
3. **像和同事说话一样**下指令即可，例如：

| 你可以这样说 | Skill 大致会做的事 |
|-------------|-------------------|
| 记一下：下周买打印机 | 记录任务 |
| 今天做什么 / 我上班了 | 日切 + 今日计划 |
| 还有什么没做 | 列出未完成任务 |
| 做完了，周报那个 | 标记完成 |
| 提醒我三点开会 | 记录 + 定时提醒流程 |
| 检查一下任务系统 | 健康检查 |

**你不需要：** 自己打开 `TASKS.md` 编辑、记 CLI 命令、了解 `app/` 里有哪些模块。

**建议每天：** 早上问「今天做什么」→ 随时「记一下」→ 完成时说「做完了」→ 睡前可说「备份一下」。

---

## 常见问题

**需要哪个 Python 版本？**  
**3.10 或更高**（3.11、3.12 均可）。运行 `python --version` 确认；只需标准库，不用装额外依赖。

**装完以后 OpenClaw 没反应？**  
确认 Skill 已复制到 OpenClaw 目录、`SKILL.md` 里的路径已改成你的安装路径，并已重启 gateway。见 [Skill 同步](docs/SKILL_SYNC.md)。

**`check` 失败？**  
多半是 `paths.json` 或 `run.cmd` 里的路径没改对。运行 `init.ps1` 后把里面的 `YourName` 全部换成你的用户名。见 [安装指南 · 故障排查](docs/INSTALL.md#故障排查)。

**Agent 还是直接改了我的 Markdown？**  
说明 Skill 未生效或被别的 Skill 覆盖。以本仓库的 `daily-task-manager/SKILL.md` 为准，并确保 gateway 加载的是最新副本。

**没有 TAIE 脑图能用吗？**  
可以。脑图是可选的；没有时只是「红旗同步」相关功能不可用，记任务、今日计划、提醒等照常。

**能用在 Mac / Linux 吗？**  
当前以 Windows 为主；其他系统见后续计划或 [CLI 参考](daily_task_manager/README.md)。

**Git push 失败、访问不了 GitHub？**  
这是网络/DNS 问题，与 Skill 无关。先保证本机能打开 [github.com](https://github.com)。

---

## 隐私说明

本仓库**只含** Skill 与工具代码、示例配置。**不含**你的真实任务、日志、脑图或提醒数据——这些留在本机安装目录，已在 `.gitignore` 中排除。

---

## 想了解更多

| 文档 | 适合什么时候看 |
|------|----------------|
| [docs/INSTALL.md](docs/INSTALL.md) | 第一次安装、换电脑 |
| [docs/SKILL_SYNC.md](docs/SKILL_SYNC.md) | 更新 Skill、路径替换 |
| [daily_task_manager/README.md](daily_task_manager/README.md) | 需要查完整 CLI 命令 |
| [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) | 想了解目录与实现 |

---

## 许可证

仓库尚未包含 LICENSE；开源发布前请自行添加。
