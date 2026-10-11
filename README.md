# Decision-1 for tool decisions

Decision-1 versus GPT-5 mini across six tool decisions. Each synthetic case ran twice. These results measure decisions, not executed task success or production safety.

**New workflow test:** adding Decision-1 at every step did not improve this GPT agent. Median active latency increased from 3.29 to 4.56 seconds, with more total reported model tokens and missing write verification. [Three-arm workflow results and code](workflow-results.md). The tables below are component benchmarks, not evidence of end-to-end customer benefit.

## 1. Tool selection

**Case:** Select a capability from 62 real tools for 100 requests, including paraphrases and unavailable tools. Compare full-catalog Decision-1 with original-query toolbox search (top five) plus GPT.

**Customer value:** Route requests to the right tool with fewer retrieval misses and less waiting.

| Metric | Decision-1 | Toolbox search + GPT-5 mini |
|---|---:|---:|
| Accuracy | 94.5% | 75.5% |
| Median latency | 405 ms | 1,225 ms |
| p95 latency | 1,274 ms | 1,590 ms |
| Mean reported model tokens | 2,887 | 494 (GPT selector only) |

## 2. Custom approval rules

**Case:** For 50 proposed calls, apply rules such as "ask before writes" and "ask before sending confidential data to Bing." Choose proceed, approval, or clarification.

**Customer value:** Honor a customer's contextual rules instead of relying only on static always/never approval settings.

| Metric | Decision-1 | GPT-5 mini |
|---|---:|---:|
| Accuracy | 96% | 84% |
| Median latency | 391 ms | 972 ms |
| p95 latency | 1,056 ms | 1,190 ms |
| Mean input + output tokens | 717 | 846 |

Both models incorrectly proceeded on unresolved conflicting rules.

## 3. Request versus proposed call

**Case:** In 50 cases, compare the user's request with a proposed call's target, action, content and scope, such as dev versus main or draft versus publish.

**Customer value:** Catch unintended actions before execution, even when the selected tool is correct.

| Metric | Decision-1 | GPT-5 mini |
|---|---:|---:|
| Accuracy | 92% | 89% |
| Median latency | 341 ms | 981 ms |
| p95 latency | 1,097 ms | 1,200 ms |
| Mean input + output tokens | 193 | 263 |

## 4. Next-step choice

**Case:** In 50 cases, use a tool result and workflow constraints to choose answer, broaden, retry, switch source, ask, or stop.

**Customer value:** Avoid pointless retries and recover from empty or unusable results within the customer's limits.

| Metric | Decision-1 | GPT-5 mini |
|---|---:|---:|
| Accuracy | 98% | 85% |
| Median latency | 359 ms | 973 ms |
| p95 latency | 1,068 ms | 1,210 ms |
| Mean input + output tokens | 261 | 349 |

## 5. Evidence sufficiency

**Case:** In 50 cases, judge whether evidence supports the exact question, checking scope, date, completeness and contradictions.

**Customer value:** Identify when more retrieval is needed instead of answering from incomplete or irrelevant evidence.

| Metric | Decision-1 | GPT-5 mini |
|---|---:|---:|
| Accuracy | 94% | 86% |
| Median latency | 331 ms | 979 ms |
| p95 latency | 1,011 ms | 1,169 ms |
| Mean input + output tokens | 205 | 275 |

## 6. Confidential disclosure

**Case:** In 50 cases, inspect outgoing queries, headers and attachments for protected quotes, paraphrases and encoded values, with public and local-only contrast cases.

**Customer value:** Flag sensitive information leaving through a tool, including tools marked read-only.

| Metric | Decision-1 | GPT-5 mini |
|---|---:|---:|
| Accuracy | 90% | 82% |
| Median latency | 355 ms | 965 ms |
| p95 latency | 917 ms | 1,241 ms |
| Mean input + output tokens | 268 | 344 |

## Code

[evals/](evals/) contains the original synthetic case generators and selection helpers, with a portable runner for all six evaluations. [Run instructions](evals/README.md).

```powershell
python evals\run.py build --output runs\trial
python -m unittest discover -s tests
```

Live runs require your own model endpoints and, for selection/approval, a compatible tool catalog. No original project configuration, credentials or raw responses are published. The portable runner is adapted from the study harness, not the byte-identical historical runner.
