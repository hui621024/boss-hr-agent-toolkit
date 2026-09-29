# BOSS HR 工具包操作说明（Windows）

## 1. 项目形态

本项目是 **Python 命令行工具 + Microsoft Edge 专用浏览器配置**。它没有 Dockerfile、没有常驻 Web 服务，也没有本地管理后台。生成的 HTML 是静态筛选报告，可以直接用浏览器打开。

运行环境：

- Windows 10/11
- Python 3.10+
- Microsoft Edge
- `patchright>=1.40`（安装脚本会一并安装）

## 2. 首次安装

在 PowerShell 中进入项目目录：

```powershell
Set-Location "D:\project\boss-hr-agent-toolkit"
.\install-windows.bat
```

也可手动安装：

```powershell
python -m pip install -e .
python -X utf8 -m boss_hr --help
```

这是 editable install。移动源码目录后，需要在新目录重新执行安装。

## 3. 一键启动

双击或在终端执行：

```powershell
.\start-windows.bat
```

该命令会检查 Python 和依赖、启动或复用专用 Edge，并打开 BOSS 招聘者页面。未指定岗位时，它不会创建筛选任务、读取简历或发送招呼。

直接启动某个岗位任务：

```powershell
.\start-windows.ps1 -Query "AI应用工程师"
```

常用参数：

| 参数 | 作用 |
|---|---|
| `-Query "岗位名"` | 登录有效时创建一次新 run，并停在人工确认门 |
| `-LoginWaitSeconds 120` | 最多等待登录 120 秒；默认 0，立即返回登录提示 |
| `-OutputDir "D:\output"` | 临时覆盖本次命令的输出根目录 |
| `-CheckOnly` | 只检查本地 Python/依赖，不启动 Edge、不连接 BOSS |
| `-NoPause` | 结束时不等待按 Enter，适合命令行或自动检查 |

启动脚本不会自动执行 `confirm`、`fetch`、`score`、`report` 或 `greet`。

通过启动脚本运行时，默认输出目录为：

```text
D:\project\boss-hr-agent-toolkit\boss-hr-output
```

该目录已加入 `.gitignore`，其中的简历、过程数据和报告不会被 Git 自动纳入版本控制。Cookie 仍保存在专用 Edge profile 中，不在此输出目录。也可通过 `-OutputDir` 或环境变量 `BOSS_HR_OUTPUT_DIR` 改到其他位置。

## 4. 登录与 Cookie 持久化

工具使用独立浏览器目录：

```text
%LOCALAPPDATA%\boss-hr-edge-profile
```

请始终在这个专用 Edge 窗口里登录 BOSS 招聘者后台。关闭窗口不会主动删除 Cookie，下次启动会复用该目录。BOSS 服务端仍可能因 Cookie 到期、异地登录、账号安全校验或会话失效而要求重新登录。

`start` 默认不等待扫码：未登录时返回 `waiting_user_login`，不会创建 run。完成登录后，用相同岗位名重跑启动命令。

## 5. 推荐的只读筛选流程

以下流程读取 BOSS 数据并在本地写 JSON/HTML，不给候选人发送消息。

### 5.1 创建任务

```powershell
.\start-windows.ps1 -Query "AI应用工程师"
```

成功后会返回：

- `run_id`
- `job_name`
- `encrypt_job_id`
- `status=waiting_user_confirmation`

保存这三个值，后续命令必须使用同一组值。

### 5.2 人工调整推荐条件

在专用 Edge 的 BOSS“推荐牛人”页面设置年龄、经验、学历、关键词等条件。确认页面候选池正确后再继续。

### 5.3 确认并读取 10 份在线完整简历

下面命令均为单行命令；把尖括号替换成上一步的真实值：

```powershell
python -X utf8 -m boss_hr confirm --job-name "<岗位名>" --encrypt-job-id "<岗位ID>" --run-id "<run_id>"
python -X utf8 -m boss_hr fetch --job-name "<岗位名>" --encrypt-job-id "<岗位ID>" --run-id "<run_id>" --count 10
```

### 5.4 评分

```powershell
python -X utf8 -m boss_hr score --job-name "<岗位名>" --encrypt-job-id "<岗位ID>" --run-id "<run_id>"
```

`score` 是两阶段状态机。每次 `status=waiting_llm` 时，需要 Codex/Agent 读取返回的 `input_file`，按 `resume-screener/SKILL.md` 评分并写入 `output_file`，然后重复同一条 `score` 命令。所有候选人完成后返回 `status=scoring_complete`。

因此，纯批处理脚本不能独立完成语义评分。可以直接对 Codex 说：

```text
筛选 AI应用工程师，只读取 10 份在线完整简历，生成报告，不发送招呼。
```

### 5.5 生成报告

```powershell
python -X utf8 -m boss_hr report --job-name "<岗位名>" --encrypt-job-id "<岗位ID>" --run-id "<run_id>"
```

返回的 `data.report_file` 是最终 HTML 路径。

历史报告按岗位和 run 保存：

```text
D:\project\boss-hr-agent-toolkit\boss-hr-output\<encryptJobId>\runs\<run_id>\<run_id>_screening_report.html
```

### 5.6 保持只读

不要执行 `boss-hr greet`。该命令会在 BOSS 页面真实点击“打招呼”，候选人会收到消息。

“只读模式”指工具不点击打招呼、不发送消息、不主动更改候选人沟通状态。工具仍会访问 BOSS 页面和接口，平台可能记录访问行为；运行过程也会在本地创建 run、JSON、HTML 和专用 Edge Cookie 文件。

## 6. 当前数据来源与限制

- `fetch` 当前读取 **BOSS“推荐牛人”列表及其在线完整简历**。
- 当前不是候选人上传的附件简历来源。
- 当前尚未接入“主动发起沟通 / 新招呼”的候选人列表；不能用现有入口直接筛选该列表。
- 候选列表会刷新，人工复核应使用报告中的 BOSS 卡片位置、候选人标识和简历证据，不应只依赖临时序号。

## 7. 评分规则

当前总分权重：

| 维度 | 权重 |
|---|---:|
| 学历 | 15% |
| 工作经验 | 35% |
| 专业技能 | 25% |
| 项目经历 | 15% |
| 专业匹配 | 10% |

海外院校分数由后端内置数据计算。数据快照日期为 **2026-09-29**，以 QS 2027 为主，THE 2026、ARWU 2026 为补充；只收录中国求职者较常见的海外院校和别名。后端采用规范化后的精确别名匹配，未命中时暂按 60 分并标记人工复核。此改动只影响后端学历评分，不改变报告版式。

## 8. 常见状态

| 状态 | 含义 | 下一步 |
|---|---|---|
| `local_only` | 本地环境检查通过 | 可启动任务 |
| `waiting_user_login` | 专用 Edge 未登录 | 登录后重跑相同 `start` |
| `waiting_user_confirmation` | run 已创建，等待人工确认筛选条件 | 调整页面后执行 `confirm` |
| `candidates_fetched` | 简历已读取到本地 | 开始 `score` 循环 |
| `waiting_llm` | 等待 Agent 给当前候选人评分 | 写 `output_file` 后重跑 `score` |
| `scoring_complete` | 全部候选人评分完成 | 执行 `report` |
| `report_ready` | HTML 已生成 | 打开 `data.report_file` |

## 9. 故障排查

仅检查本地环境：

```powershell
.\start-windows.ps1 -CheckOnly -NoPause
```

检查 Edge/CDP/登录状态：

```powershell
python -X utf8 -m boss_hr doctor
```

常见处理：

- `patchright` 缺失：重新运行 `install-windows.bat`。
- `CDP_NOT_RUNNING`：运行 `start-windows.bat`。
- `BOSS_LOGIN_REQUIRED`：在专用 Edge 登录，再重跑原命令。
- 岗位名有多个匹配：改用返回列表中的 `encryptJobId` 启动。
- 移动了源码目录：在新目录重新执行 `python -m pip install -e .`。

## 10. 停止

本项目没有需要停止的本地服务。完成后关闭专用 Edge 和命令行窗口即可；不要删除 `%LOCALAPPDATA%\boss-hr-edge-profile`，否则保存的登录状态也会被删除。
