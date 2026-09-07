# Scoped Re-Review Prompt Template

修复轮后派发限定复审用此模板。只验证 findings 是否修复 + 修复 diff 有无新问题。

```
Subagent (general-purpose):
  description: "Re-review Task N fix round R"
  model: [MODEL — 必须显式指定，小修复用便宜档]
  prompt: |
    You are re-reviewing a fix round. A previous review produced findings;
    an implementer attempted to fix them. Verdict each finding and inspect
    the fix diff — nothing else.

    ## Task

    Read the task brief: [BRIEF_FILE]

    ## Findings Under Verification

    [FINDINGS — 逐条列出]

    ## The Fix

    Read the implementer's report (fix reports appended at the end):
    [REPORT_FILE]

    **Fix base:** [FIX_BASE_SHA]  **Head:** [HEAD_SHA]
    **Diff file:** [DIFF_FILE]

    Read the diff file once. Do not re-run git commands.
    Your review is read-only. Do not mutate working tree, index, or HEAD.

    ## No Subagents

    Do all review yourself.

    ## Scope

    Your scope is the findings list and the fix diff. Do NOT re-review
    untouched code. Issues outside the fix diff go under Out-of-Scope
    Observations — they don't block this task.

    ## Tests

    Do not re-run the suite. Confirm the fix report names covering tests
    and shows output. Run a focused test only for a specific doubt.

    ## Output

    Begin directly with the first finding's verdict.

    ### Finding Verdicts
    For each finding:
    **[finding one-liner]** — ADDRESSED | NOT ADDRESSED (file:line evidence)

    ### New Breakage in Fix Diff
    (Critical/Important/Minor with file:line, or "None")

    ### Out-of-Scope Observations
    (Non-blocking, or "None")

    ### Verdict
    All findings addressed, no new breakage | Findings remain open — [list]
```

**占位符：**
- `[MODEL]` — 小修复用便宜-中档
- `[BRIEF_FILE]` — 同一份 brief
- `[FINDINGS]` — 上次审查的 Critical/Important findings，逐条
- `[REPORT_FILE]` — 实现者的报告（修复报告追加在末尾）
- `[FIX_BASE_SHA]` — 上次审查看到的 HEAD
- `[HEAD_SHA]` — 当前 HEAD
- `[DIFF_FILE]` — `scripts/review-package` 输出的路径
