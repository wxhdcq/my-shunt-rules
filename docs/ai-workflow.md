# 用 iPhone 管理 AI 开发

这份流程把需求、实现、检查和验收留在 GitHub 的可追溯记录中。你在手机上决定做什么以及是否合并，AI 在独立环境和分支完成实现。

## 已有能力与当前边界

- 项目规则在 [AGENTS.md](../AGENTS.md)，任务入口在 [Issue 表单](../.github/ISSUE_TEMPLATE/ai_task.yml)，交付格式在 [PR 模板](../.github/pull_request_template.md)。
- [Check Rules](../.github/workflows/check-rules.yml) 对 PR 无路径过滤，使用 Python 3.11，离线校验产物、运行 pytest 并检查生成器没有改写已提交文件。
- `push` 检查仅针对 `main` 上指定的代码、配置和工作流路径。仅推送本次文档分支不会触发它；创建 PR 后必须查实际 Checks。
- [Update Rules](../.github/workflows/update-rules.yml) 仍每天抓取规则，有变化时直接提交默认分支。W1 不改变该行为；改为候选 PR 属于另行批准的 W2。
- 这些文档不等于已配置分支保护、Cloud 环境、自动派单或自动审查。没有实际操作和验证记录，就标为“未核实 / 未验证”，不推断账户中一定不存在这些配置。

## 一次任务的流程与验收

| 阶段 | 操作 | 通过标准 |
| --- | --- | --- |
| 1. 拆分 | Work 只读了解现状，形成一个 Issue 或等价任务记录 | 目标、基线、允许文件、验收命令、手机步骤、风险和回滚完整；用户批准范围清楚 |
| 2. 准备 | 核实最新基线，在独立工作区创建 `codex/<编号>-<简述>` | 目标仓库和 SHA 正确；工作区无遗留改动；依赖可安装；不需要生产密钥即可离线验证 |
| 3. 实施 | 只修改批准范围，运行任务检查和既有回归测试 | 所需命令成功；没有意外生成物变更；失败最多自动修复两轮后报告具体阻塞 |
| 4. PR | 提交候选分支，创建 PR，填写证据 | PR diff 与范围一致；记录 head、base、实际测试 commit；`Check Rules` 的 `check` 实际运行成功 |
| 5. 独立审查 | 另一个审查任务读候选 diff、相关代码和证据 | 记录审查 SHA；阻塞问题解决；修改后重跑相关检查，不能仅凭“没有评论”认定通过 |
| 6. 手机验收 | 用户查看 Files changed、Checks 和专用场景 | 每项预期有实际结果；未验证项明确；用户决定继续修改或批准合并指定 SHA |
| 7. 合并与后验 | 只有明确批准后才合并；检查主分支结果 | 合并前重新核实 head/base；若相关版本已变化则重新验证；完成后置验收，发现问题按约定回滚 |

同一仓库先同时运行一个实施任务，可配一个独立只读审查任务。一个任务一个分支和 PR，先完成再推广；不用额外购买编排服务或接入付费 API。

## Cloud 环境怎么使用

在 ChatGPT Work 中整理任务，之后可把完整任务交给 Codex Cloud。官方说明 iPhone 可以选择已发布的环境；环境创建与发布入口在网页或桌面。只有手机时可尝试 Safari 网页，若入口或权限不可用，要报告卡住的具体步骤，不能声称环境已经建好。

首次环境准备是独立待实施阶段：选择本仓库、Python 3.11，并安装 `requirements.txt`。在两个独立新任务中复跑离线检查，记录环境、版本、SHA 和结果，才算环境验收通过。现有依赖未锁定；完全可复现的依赖与覆盖率基线属于后续 T1。

本流程不要求把 API key 放进仓库，也不要求安装 `openai/codex-action`。若环境不能联网安装依赖，保留已有验证结果并报告限制，不通过跳过安装和测试来交付。

## 标准离线检查

在干净的已提交候选 checkout 中执行 [AGENTS.md](../AGENTS.md) 的命令。检查包括两项校验、pytest、README 和 manifest 再生成，以及 Git 差异和状态。生成器检查必须真实运行，不能只检查文件存在。

W1 起始提交 `f5f50ea3e6da90576ea2ec71c615f530c775170a` 有 36 项测试。之后以实际收集和通过数为准；pytest 通过不证明全项目覆盖率。完整构建会联网并更新生成物，文档任务不运行它。

PR 的 CI 可能 checkout 临时合并提交，而不是 head 本身。证据应同时列出：任务起始 SHA、当前 base SHA、当前 head SHA、实际测试 commit 和 Actions 链接。检查必须对应当前 head/base 组合；目标分支因定时任务更新后，也需重新判断并运行相关验证。

如果 Checks 显示待批准，需要有权限的人在 GitHub 批准运行；查不到运行记录时报告“未查到运行记录”，并继续确认是否未触发或尚未可见。已创建的运行按实际状态记录：失败、取消、跳过、排队、待批准、运行中和成功不能混淆。本规范本身不会让检查成为 GitHub 强制合并门槛。

## 手机验收操作

1. 打开 AI 提供的 PR 链接；GitHub App 缺少某个入口时，在 Safari 打开同一链接。
2. 在 **Files changed** 核对允许文件，特别检查是否出现规则源、`dist/`、工作流或依赖的意外修改。
3. 在 **Checks** 打开 `Check Rules` → `check`，确认校验、测试和“发布文件未改变”步骤确实成功。单个绿色摘要不能代替这些证据。
4. 查看独立审查结论，按任务专用步骤验收。实际客户端规则加载或网络行为如果没测试，就保留为待验，不能用 Python 测试替代。
5. 用下面的记录给出明确决定。PR 作者不能用自己的 GitHub 审查批准来替代人工验收记录；不要给单人项目设置无法满足的额外审批人数。

```text
PR：
我验收的 head SHA：
当前 base SHA：
Checks 和人工场景结果：
未验证项目：
决定：继续修改 / 允许合并上述 SHA
部署或仓库设置变更：未授权 / 另行列明授权
```

合并规则产物会影响直接订阅 `main` 文件的用户，所以批准前必须说明实际影响。W1 仅新增四个规范和模板文件，不改变规则内容或现有工作流；已有定时更新仍会继续运行。

## W1 的验收与首次启用

本阶段只新增以下四个文件：

- `AGENTS.md`
- `.github/ISSUE_TEMPLATE/ai_task.yml`
- `.github/pull_request_template.md`
- `docs/ai-workflow.md`

合并前：核对 Issue YAML 语法及字段、文档相对链接、四文件范围；重跑 36 项既有测试与标准离线检查；PR 手工填写完整摘要和证据；独立审查通过。交付 PR 后等待用户，不能直接写 `main`。

后置启用验收：模板合入默认分支后，在新建 Issue 页面确认出现“AI 开发任务”，打开并检查必填字段；在有实际差异的新 PR 创建页面确认自动带入 PR 模板。无需仅为验证而提交空 Issue 或无意义 PR。若页面提示模板错误，另开修复任务；尚未合并时只记“待启用”，不能提前宣称自动入口已生效。

回滚：未合并时关闭 PR 即可停止交付；合并后经用户批准，用新分支和 revert PR 撤销 W1 的四个新增文件，避免回退其他人的提交。回滚同样经过检查，不强制重置主分支。

## 参考

- [GitHub Issue 表单语法](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms)
- [GitHub Issue 和 PR 模板](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/about-issue-and-pull-request-templates)
- [Codex Cloud](https://learn.chatgpt.com/docs/cloud)
- [Codex 云环境](https://learn.chatgpt.com/docs/environments/cloud-environments)
