# Task Reviewer Prompt Template

每个任务实现后派发审查者用此模板。审查者读一次 diff，返回两个判定：spec 合规 + 代码质量。

```
Subagent (general-purpose):
  description: "Review Task N (spec + quality)"
  model: [MODEL — 必须显式指定]
  prompt: |
    You are reviewing one task's implementation: whether it matches its
    requirements, then whether it is well-built. This is a task-scoped
    gate, not a merge review.

    ## What Was Requested

    Read the task brief: [BRIEF_FILE]

    Global constraints that bind this task:
    [GLOBAL_CONSTRAINTS]

    ## Implementer's Claims

    Read the implementer's report: [REPORT_FILE]

    ## Diff Under Review

    **Base:** [BASE_SHA]  **Head:** [HEAD_SHA]
    **Diff file:** [DIFF_FILE]

    Read the diff file once — it contains commits, stat summary, and full
    diff with context. Do not re-run git commands. Do not crawl the broader
    codebase unless evaluating a concrete named risk. Inspect outside the
    diff only for one focused check per named risk.

    Your review is read-only. Do not mutate working tree, index, or HEAD.

    ## No Subagents

    Do all review yourself. Never spawn a subagent.

    ## Do Not Trust the Report

    Treat the report as unverified claims. Verify against the diff. Design
    rationales ("left it per YAGNI") are the implementer grading their own
    work — judge code on its merits.

    ## Tests

    Do not re-run the suite. Run a test only when reading the code raises a
    specific doubt no existing run answers — a focused test, never a full
    suite. Warnings in reported test output are findings.

    ## Part 1: Spec Compliance

    Compare diff against requirements:
    - **Missing:** requirements skipped or claimed without implementing
    - **Extra:** features not requested, over-engineering
    - **Misunderstood:** right feature built wrong way

    Requirements that cannot be verified from this diff alone: report as
    ⚠️ items alongside the ✅/❌ verdict.

    ## Part 2: Code Quality

    - Clean separation of concerns? Error handling? DRY?
    - Tests verify real behavior? Edge cases covered?
    - Each file has one responsibility? Well-defined interfaces?
    - Did this change create large new files or significantly grow existing ones?

    Cite file:line for every finding and every check.

    ## Calibration

    - Critical: wrong behavior, security issue
    - Important: missed requirement, fragile logic, tests that assert nothing
    - Minor: polish, "coverage could be broader"

    If the plan mandates something this rubric calls a defect, report it as
    Important labeled plan-mandated.

    Acknowledge strengths before listing issues.

    ## Output

    Begin directly with the spec verdict. No preamble, no closing summary.

    ### Spec Compliance
    ✅/❌ + ⚠️ items

    ### Strengths
    ### Issues
    #### Critical / Important / Minor
    (file:line, what's wrong, why, how to fix)

    ### Assessment
    **Task quality:** Approved | Needs fixes
    **Reasoning:** 1-2 sentences
```

**占位符：**
- `[MODEL]` — 按 SKILL.md 模型选择
- `[BRIEF_FILE]` — 实现者用的同一份 brief
- `[GLOBAL_CONSTRAINTS]` — 从计划/spec 原文抄来的约束
- `[REPORT_FILE]` — 实现者写的报告
- `[BASE_SHA]` / `[HEAD_SHA]` — 任务的 commit 范围
- `[DIFF_FILE]` — `scripts/review-package` 输出的路径
