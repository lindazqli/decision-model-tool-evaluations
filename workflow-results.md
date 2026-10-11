# Workflow comparison: GPT alone versus GPT + Decision-1

**This integration did not demonstrate a customer benefit over GPT alone.** Decision-1 routing and gating reduced GPT call count but increased total model usage and latency, and prematurely stopped before write verification.

**Case:** 50 distinct synthetic tasks, five per family: reads, record search, transient failures, environment scope, writes requiring approval, preapproved writes, expired approvals, local confidential reads, public searches and confidential searches. Each ran once per architecture, with live model inference and stateful mock tools.

**Customer value being tested:** finish the same task correctly and safely with less total model work, rather than win an isolated classification benchmark.

| Metric, per 50 tasks unless noted | GPT only | GPT + Decision-1 | GPT + code guards |
|---|---:|---:|---:|
| Strict safe completed tasks | 41/50 (82%) | 24/50 (48%) | 41/50 (82%) |
| Post-run answer-format sensitivity: safe completion | 49/50 (98%) | 34/50 (68%) | 50/50 (100%) |
| Median active workflow latency | 3,289 ms | 4,565 ms | 3,308 ms |
| p95 active workflow latency | 5,827 ms | 7,783 ms | 6,462 ms |
| Mean reported native tokens, all models | 2,163 | 3,759 | 2,134 |
| Mean GPT calls per task | 3.20 | 2.64 | 3.16 |
| Mean Decision-1 calls per task | 0 | 3.14 | 0 |
| Mean mock tool calls per task | 2.20 | 1.74 | 2.16 |
| Unapproved protected calls | 1 | 0 | 0 |
| Invalid mock calls | 2 | 1 | 0 |
| Unnecessary approval interactions | 6 | 7 | 5 |
| Writes missing required read-back | 0/15 | 15/15 | 0/15 |

The answer-format diagnostic was added **after** inspecting results. It accepts answers containing the expected value only when state/verification and safety requirements also pass; it does not replace frozen primary scoring. Many confidential-read/search failures were extra answer fields rather than incorrect content. This sensitivity materially changes absolute scores but not the comparative conclusion.

## What the integration actually did

GPT generated tool arguments and final answers in all three arms, with the same model, minimal reasoning, task, final JSON schema, and eight-GPT-step budget. Each task started with a fresh mock world.

- **GPT only:** native GPT tool selection over all five tools; GPT was responsible for asking approval.
- **GPT + Decision-1:** Decision-1 selected the next tool or answer at each step. GPT saw full tool contracts in context but only the selected tool was callable. Decision-1 also gated proposed updates and external queries. Exact required approvals were automatically simulated before execution.
- **GPT + code guards:** native GPT routing with a deterministic exact write/confidential-query guard using structured fixture facts.

Mock tools performed reads, searched records, changed persisted in-memory status, returned public/confidential search fixtures and simulated exact customer approvals. A write required a later read-back before successful completion. We deliberately recorded unapproved operations in the isolated mock rather than blocking them in every arm, to measure policy misses. No real service action, email, search query or confidential transfer occurred.

## Why the hybrid lost

GPT calls fell 17.5%, but GPT tokens increased from 108,162 to 115,322 because the hybrid retained full schemas as context. Decision-1 added another 72,604 native tokens and 157 calls. The hybrid's aggregate native token count rose about 74%, and median active latency about 39%.

Decision-1 selected answer after updates without requesting the required read-back on all 15 write tasks. This is not just a final-answer formatting problem. Fewer tool calls can indicate unfinished work, not efficiency. The one GPT-only unapproved call was a confidential web query; exact code guards prevented the same class without adding another model.

## Limits and cost

This is one integration, not a verdict on Decision-1 generally. It combines routing, stopping and approval, so it does not isolate which checkpoint provides incremental value. The prompts differ where architecture requires it; the hybrid has schema/context overhead. Code guards use exact synthetic strings and structured facts, not production DLP. Five template variants per family, one repetition, no independent human review, no realistic customer approval delays and no real tool latency limit generalization.

Latency sums live model requests, including valid and failed tasks, and excludes deliberate pacing. Raw wall times were retained locally. All main calls reported usage; no service failures occurred in the main run. Native tokens from different APIs are not interchangeable cost units.

| Aggregate API usage | GPT only | GPT + Decision-1 | GPT + code guards |
|---|---:|---:|---:|
| GPT input tokens | 103,271 | 111,038 | 101,866 |
| GPT output tokens | 4,891 | 4,284 | 4,833 |
| Decision-1 input tokens | 0 | 72,447 | 0 |
| Decision-1 output tokens | 0 | 157 | 0 |

No monetary savings claim is made: deployment-specific input/output prices were not supplied. Apply those prices to the separate totals above, rather than treating summed native tokens as dollars.

Two development cohorts exposed API-contract, approval-name, missing-environment and answer-format issues. Those were corrected before freezing the main run; development responses are excluded. Main results and scoring were not rewritten. The post-run diagnostic is labeled separately.

## Evidence and next conclusion

[Runnable harness](evals/workflow_eval.py), [50 task definitions](evals/workflow_cases.py), [format diagnostic](evals/workflow_diagnostics.py), [aggregate results](results/workflow-analysis.json) and [run instructions](evals/README.md#stateful-workflow-comparison).

The earlier six component evaluations remain exploratory. This workflow test argues against inserting Decision-1 at every step in this design. A narrower approval-only or recovery-only integration would need its own paired study before recommending adoption.
