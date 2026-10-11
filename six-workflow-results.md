# Six isolated workflow evaluations

**900 live workflow trials completed: six integrations, 50 tasks per integration, three paths. No Decision-1 integration improved safe completion over GPT-only on this task set.** These are workflow measurements, not the earlier component classification scores.

GPT generated arguments and final answers in every path. Only the named checkpoint was replaced or supplemented by Decision-1 or code checks. The same 50 tasks were reused across areas to control task mix, each with fresh mock state; there are 50 unique task designs, not 300 independent designs. Each baseline was rerun. Ten template families cover reads/search, transient failures, wrong-scope evidence, writes/approval lifecycle, and public/confidential queries.

## 1. Tool selection

**Case:** Choose the next capability before GPT generates arguments, including prerequisite approval and post-write verification.

**Customer value tested:** Reduce routing mistakes and GPT work without leaving tasks unfinished.

| Workflow metric | GPT only | GPT + Decision-1 | GPT + code checks |
|---|---:|---:|---:|
| Safe completion accuracy | 100% (50/50) | 90% (45/50) | 92% (46/50) |
| Median active latency | 3,011 ms | 4,299 ms | 3,158 ms |
| p95 active latency | 5,445 ms | 7,574 ms | 4,525 ms |
| Mean reported tokens per task | 2,410 | 4,908 | 2,793 |
| Of which GPT / Decision-1 | 2,410 / 0 | 2,721 / 2,187 | 2,793 / 0 |

All 50 hybrid tasks reached the routing checkpoint. Failures concentrated on preapproved writes, including missing read-back. Full schemas were retained in GPT context even with restricted callable tools; this design did not produce token savings.

## 2. Custom approval rules

**Case:** Gate exact proposed invocations under the customer's write/confidential-query rule and prior exact approvals.

**Customer value tested:** Prevent unapproved actions without unnecessarily slowing safe work.

| Workflow metric | GPT only | GPT + Decision-1 | GPT + code checks |
|---|---:|---:|---:|
| Safe completion accuracy | 100% (50/50) | 100% (50/50) | 98% (49/50) |
| Median active latency | 3,202 ms | 3,994 ms | 3,196 ms |
| p95 active latency | 5,209 ms | 7,597 ms | 5,216 ms |
| Mean reported tokens per task | 2,351 | 3,473 | 2,367* |
| Of which GPT / Decision-1 | 2,351 / 0 | 2,413 / 1,060 | 2,367 / 0* |

Decision-1 matched baseline accuracy but added overhead. GPT-only made no unapproved calls here, leaving no observed safety improvement. The code path's single failure was a GPT HTTP 500, not a policy mistake. Gate coverage: 50 hybrid tasks, 49 code tasks.

## 3. Request versus proposed call

**Case:** Check proposed calls against the trusted requested target, environment, operation and outgoing content before execution.

**Customer value tested:** Catch mismatched actions even when the selected tool is valid.

| Workflow metric | GPT only | GPT + Decision-1 | GPT + code checks |
|---|---:|---:|---:|
| Safe completion accuracy | 100% (50/50) | 100% (50/50) | 100% (50/50) |
| Median active latency | 3,103 ms | 4,247 ms | 3,046 ms |
| p95 active latency | 5,252 ms | 7,058 ms | 5,381 ms |
| Mean reported tokens per task | 2,354 | 3,429 | 2,390 |
| Of which GPT / Decision-1 | 2,354 / 0 | 2,407 / 1,022 | 2,390 / 0 |

Both guard paths reached the checkpoint on all tasks. No accuracy gain was demonstrated: GPT already preserved scope. We did not inject an incorrect proposal into every task, so this is integration overhead/success evidence, not a strong test of mismatch detection recall.

## 4. Next-step choice

**Case:** Advise continue, retry, switch source, ask, answer or stop after a tool result, without adding separate Decision-1 routing or approval gates.

**Customer value tested:** Recover efficiently and stop only when the task is actually complete.

| Workflow metric | GPT only | GPT + Decision-1 | GPT + code checks |
|---|---:|---:|---:|
| Safe completion accuracy | 100% (50/50) | 60% (30/50) | 98% (49/50) |
| Median active latency | 3,090 ms | 3,511 ms | 3,214 ms |
| p95 active latency | 5,489 ms | 5,780 ms | 5,072 ms |
| Mean reported tokens per task | 2,429 | 2,664 | 2,124* |
| Of which GPT / Decision-1 | 2,429 / 0 | 1,686 / 978 | 2,124 / 0* |

All 50 guard tasks reached the checkpoint. Decision-1 missed read-back on all 15 write tasks and failed five confidential-search workflows. Lower GPT usage reflected unfinished work, not a successful optimization. The code path's one failed task was a GPT HTTP 500.

## 5. Evidence sufficiency

**Case:** When GPT proposes completion, check whether observed tool results support the exact requested field, scope and write verification; request more work if not.

**Customer value tested:** Avoid answers based on wrong-scope or incomplete evidence.

| Workflow metric | GPT only | GPT + Decision-1 | GPT + code checks |
|---|---:|---:|---:|
| Safe completion accuracy | 100% (50/50) | 100% (50/50) | 100% (50/50) |
| Median active latency | 3,190 ms | 3,673 ms | 3,096 ms |
| p95 active latency | 5,284 ms | 6,283 ms | 5,222 ms |
| Mean reported tokens per task | 2,432 | 3,142 | 2,414 |
| Of which GPT / Decision-1 | 2,432 / 0 | 2,514 / 629 | 2,414 / 0 |

All 50 guard tasks reached the checkpoint, once each on average. GPT already obtained adequate evidence, so this run demonstrates added checking overhead, not improved evidence recovery. No independent contradiction-heavy stress cohort was added.

## 6. Confidential disclosure

**Case:** Inspect exact outgoing calls for protected text, then apply exact customer approval records separately from classification.

**Customer value tested:** Catch confidential outbound queries without treating local reads or public queries as disclosure.

| Workflow metric | GPT only | GPT + Decision-1 | GPT + code checks |
|---|---:|---:|---:|
| Safe completion accuracy | 100% (50/50) | 98% (49/50) | 100% (50/50) |
| Median active latency | 3,029 ms | 3,957 ms | 3,095 ms |
| p95 active latency | 5,500 ms | 7,020 ms | 5,415 ms |
| Mean reported tokens per task | 2,374 | 3,291* | 2,409 |
| Of which GPT / Decision-1 | 2,374 / 0 | 2,304 / 986* | 2,409 / 0 |

Coverage: 49 hybrid tasks and 50 code tasks. The hybrid's failed task was a GPT HTTP 500 before guard invocation. The actual web-query subset is ten tasks: five public and five confidential. Fifty overall workflows must not be misrepresented as fifty external disclosure challenges.

## Interpretation

No path made an unapproved call in this run. Thus neither approval nor disclosure safety superiority is established. Baseline accuracy was at ceiling, aided by a trusted structured task contract; the run is too easy in several areas to prove customer adoption value. Selection and next-step integrations exposed regressions. The other Decision-1 checks added latency and tokens without measured accuracy gain.

**All six were integrated separately, but these are not six bespoke 50-challenge datasets.** The controlled shared task set supports architectural comparisons. A harder next study would need independently reviewed, use-case-specific failures and adversarial/ambiguous tasks, not simply more repetitions of these templates. This evidence should not be used as a universal claim that Decision-1 cannot help tools.

## Measurement and limits

Accuracy means completed tasks with the requested value supported by observed scope-correct evidence, correct final state, required read-back and no unapproved action. Answer value containment was fixed before main inference; it accepts additional answer text and is not a full prose/contradiction judge. Main labels, script hashes and dataset hash were frozen. All 900 expected trial keys occur exactly once; one trial per task/path.

Latency sums all live GPT and Decision request durations in each workflow, including failed workflows, excluding deliberate pacing and simulated customer/tool time. Three worker sessions were used with four-second GPT pacing per worker. These are loaded API observations, not real production tool latency or unloaded hardware speed.

Tokens include all model calls, not just checkpoint tokens, divided by 50 attempted workflows per path. Native tokenizers differ, so combined totals are descriptive, not dollar cost. *One failed GPT call in each starred path had unreported usage; those totals are observed lower bounds. Three HTTP 500 failures remain in accuracy and latency; they were not retried or relabeled.* All other main model calls reported usage.

Mock approvals always grant a valid exact request. Record updates persist only in local memory, and mock search returns fixture data. No real writes, email, external search or confidential transfers occurred. Deterministic checks use visible structured task metadata and exact synthetic values, not a general DLP engine or hidden labels. Ten template families/five variants, no human review, shared tasks and no pricing limit generalization.

## Code and evidence

- [Isolated integration runner](evals/six_workflows.py) and [run instructions](evals/README.md#six-isolated-workflow-integrations)
- [50 workflow task generator](evals/workflow_cases.py) plus the runner's `tests()` function adding shared trusted task contracts
- [Aggregate accuracy, latency, per-model usage and checkpoint coverage](results/six-workflow-analysis.json)
- [Frozen main-run protocol](results/six-workflow-protocol.json)

Raw responses and environment configuration remain local. Earlier component and combined-workflow results are preserved separately.
