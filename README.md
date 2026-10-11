# Decision-1 for tool usage: findings

**Decision-1 is promising as a fast, narrow decision layer around tools, especially for interpreting user approval rules and checking proposed actions. Our experiments do not establish it as a replacement for general-purpose models, tool search, or enforced authorization.**

## Evidence

The comparator is GPT-5 mini with minimal reasoning, except for tool selection, where it is actual toolbox search plus GPT-5 mini. Every scenario ran twice per path.

### 1. Tool selection

100 distinct cases, 62 real tools, 200 trials per path.

| Metric | Decision-1 | Toolbox search + GPT-5 mini |
|---|---:|---:|
| Accuracy | 94.5% | 75.5% |
| Median latency | 405 ms | 1,225 ms |
| p95 latency | 1,274 ms | 1,590 ms |
| Mean reported model tokens | 2,887 | 494 (GPT selector only) |

Search token usage was not available. This row compares reported model tokens only, not total token consumption for the search path.

### 2. Custom approval rules

50 distinct cases, 100 trials per model.

| Metric | Decision-1 | GPT-5 mini |
|---|---:|---:|
| Accuracy | 96% | 84% |
| Median latency | 391 ms | 972 ms |
| p95 latency | 1,056 ms | 1,190 ms |
| Mean input + output tokens | 717 | 846 |

### 3. Request versus proposed call

50 distinct cases, 100 trials per model.

| Metric | Decision-1 | GPT-5 mini |
|---|---:|---:|
| Accuracy | 92% | 89% |
| Median latency | 341 ms | 981 ms |
| p95 latency | 1,097 ms | 1,200 ms |
| Mean input + output tokens | 193 | 263 |

### 4. Next-step choice

50 distinct cases, 100 trials per model.

| Metric | Decision-1 | GPT-5 mini |
|---|---:|---:|
| Accuracy | 98% | 85% |
| Median latency | 359 ms | 973 ms |
| p95 latency | 1,068 ms | 1,210 ms |
| Mean input + output tokens | 261 | 349 |

### 5. Evidence sufficiency

50 distinct cases, 100 trials per model.

| Metric | Decision-1 | GPT-5 mini |
|---|---:|---:|
| Accuracy | 94% | 86% |
| Median latency | 331 ms | 979 ms |
| p95 latency | 1,011 ms | 1,169 ms |
| Mean input + output tokens | 205 | 275 |

### 6. Confidential disclosure

50 distinct cases, 100 trials per model.

| Metric | Decision-1 | GPT-5 mini |
|---|---:|---:|
| Accuracy | 90% | 82% |
| Median latency | 355 ms | 965 ms |
| p95 latency | 917 ms | 1,241 ms |
| Mean input + output tokens | 268 | 344 |

Decision-1's median latency was 60-67% lower across these studies. Its p95 advantage was smaller, so the median improvement should not be treated as a uniform speedup. It used about 15-27% fewer observed tokens on the five narrow decisions, but 5.8x the reported model tokens on full-catalog selection; the latter total-path comparison is incomplete because search usage is unknown.

Tokens are API-reported input plus output, averaged per valid model response and rounded to whole tokens. All rows have 100 responses per model except selection (200 each) and GPT approval (98 valid responses; two content-filtered attempts). Accuracy uses all attempted trials, including those two filtered attempts. Tokens for those filtered attempts were unreported and are excluded from the valid-response mean. The search comparator's 494 tokens cover GPT only; search-internal consumption is unknown, not zero.

Latency is measured request/selection-path time, excludes client pacing, and uses valid responses. The search path includes search RPC plus GPT response time. Model-native token counts differ across APIs and are not monetary cost. These are separate studies and case mixes, not a single pooled benchmark.

## What each evaluation tested

**Tool selection:** given a user request, choose a capability from 62 real tools spanning GitHub, web search, Python, shell, PDF processing, skills and semantic queries. The 100 cases included reads, approved writes, paraphrases and unavailable capabilities. Decision-1 saw the full compressed catalog; the comparator retrieved five tools with the original query and used GPT to select. Example: choose issue search for "find reconnect bugs," rather than an issue-update tool. This tests capability selection, not argument generation or task completion.

**Custom approval rules:** decide whether a fixed proposed invocation should proceed, ask for approval, or ask for clarification under a user-authored rule. Cases covered "ask before writes," "ask before sending confidential data to Bing," scoped exceptions and prior approvals. Inputs included actual arguments, relevant contracts, synthetic document excerpts and approval records, not prefilled write-effect flags. Example: a read-only web search still needs approval when its outgoing query contains confidential information. Both models failed an unresolved conflict between always-ask and never-ask rules.

**Request versus proposed call:** compare the user's intended action with the proposed target, operation, content and constraints. Cases included wrong repositories/recipients, draft-versus-publish, extra deletions, branch/time/limit changes, and missing context. Example: the user says "update only the dev branch," but the call targets main. This is intent alignment, separate from approval. Decision-1's 3-point accuracy lead is not conclusive; its grouped interval includes zero.

**Next-step choice:** after a tool result, choose answer, broaden query, retry the same source, use an authorized alternative, ask the user, or stop. Cases included empty searches, transient failures, exhausted budgets, access denial, incomplete results and cancellation. Example: broaden an overly narrow empty search only if scope and budget permit. Much of this explicit-policy behavior can be enforced in code; model value is mainly in interpreting result usefulness.

**Evidence sufficiency:** determine whether retrieved material supports the exact requested answer, is incomplete, or remains contradictory. Cases varied environment, tenant, date/version, pagination, units, redaction and source authority. Example: staging configuration is not evidence of production configuration. Both models accepted that wrong-scope evidence, so neither should be the sole stopping gate.

**Confidential disclosure:** compare outgoing arguments with protected source information and trusted classification/publication evidence. Cases covered quotes, paraphrases, identifiers, encoding, attachments, headers, redaction, generic overlap, local-only processing and unknown destinations. Example: removing a project name is insufficient if its protected price remains in the query. The expansion exposed false alarms and uncertain->clear errors; some unknown-content placeholders were ambiguous fixture representations. This is advisory classification, not authorization or DLP replacement.

**Tool selection has a real tradeoff.** In the 62-tool test, 46 of the search path's 49 errors occurred because the expected tool was absent from the top-five shortlist. Decision-1 was about three times faster at the median, but used 5.8 times as many observed model tokens because it received the full catalog. Search-internal token usage was unreported. This compares one-shot original-query search, not rewritten queries or iterative retrieval.

**Approval interpretation is the strongest practical signal, with a critical boundary.** Decision-1 made no automatic allows on the 25 distinct known approval-required scenarios, but both models incorrectly proceeded on a scenario with conflicting user rules and no defined precedence. Decision-1's remaining errors paused for clarification rather than requesting approval. It is an adviser, not an authorization authority.

**Results depend on task design.** A separate policy-bearing routing test scored 64/100 for Decision-1, 54/100 for direct GPT, and 41/100 for search plus GPT. Models confused capability selection with permission, and some task details were missing from routing inputs. Decision-1's direct advantage over GPT was not conclusive: the case-clustered interval was -2 to +22 percentage points. Earlier pilots also did not show consistent superiority over direct GPT.

**The larger sample changed the conclusion.** Each of the four narrow tasks now has 50 distinct cases, rather than 12-14. Original responses were retained and 150 new scenarios added. Intent and disclosure no longer have perfect scores; intent's +3-point grouped interval includes zero. The extension was authored after seeing earlier errors, so combined results are exploratory, not a pristine held-out benchmark.

## Recommendation

Prioritize a shadow integration for **request-versus-call alignment and user-rule interpretation**, with disclosure screening as an additional advisory check using trusted classification and destination evidence. Keep exact scope/approval matching, RBAC, policy precedence, cancellation, retry limits, and schema validation in code. Do not use model evidence-sufficiency judgments as the sole stopping condition.

## How we tested

### Shared procedure

We ran custom Python evaluation harnesses against deployed Decision-1 and GPT-5 mini models in a Microsoft Foundry project. These were live model API calls over synthetic scenarios, not simulated model results and not end-to-end agent runs.

1. Author each scenario with its task/context, policy, allowed answers and expected answer. Freeze the expected labels before that cohort's inference. Reference labels were assistant-authored, not independently human-reviewed.
2. Send the same underlying scenario facts and decision policy to both models. Decision-1 used its native choice-question API with named alternatives; GPT-5 mini used chat completions with minimal reasoning and a strict JSON output schema. API representations differed, so prompts were not byte-identical.
3. Run each scenario twice per comparison path. Record the selected answer, response validity, latency and API-reported input/output tokens. Retain original responses locally.
4. Score the returned label against the frozen expected answer or accepted route set. No LLM judge, probability threshold adjustment, or post-run relabeling was used for the reported six evaluations.
5. Aggregate accuracy over attempted trials, latency over valid responses, and token usage over valid responses with reported usage. Keep filtered outputs visible rather than rewriting their prompts or weakening filters.

The six reported evaluations comprise 350 distinct scenarios and 1,400 model attempts: 400 for selection and 200 for each of the other five areas. Selection also made 200 actual search RPCs. This count excludes development probes, earlier pilots and the separately discussed policy-bearing routing experiment.

### 1. Tool selection: full catalog versus actual search

| Setup item | What we did |
|---|---|
| Dataset | 100 requests: 40 GitHub reads, 12 paraphrases, 12 approved writes, eight web tasks, eight local-processing tasks, eight skill-selection tasks, four semantic queries and eight no-match/no-tool tasks. |
| Catalog | 62 real executable capabilities. Search/dispatcher wrappers were excluded from the executable count and web aliases normalized. |
| Decision-1 input | User request plus the complete compressed catalog and a no-tool option. Descriptions included the first paragraph and required argument names. |
| Search + GPT input | Call the actual toolbox's `tool_search` with the original user query and `limit=5`; give GPT the returned descriptions and a no-tool option. No query rewriting, iterative retrieval or wider shortlist. |
| Output and scoring | Choose a capability or no tool. Compare with frozen labels; some plausible alternative routes were penalized by this study's exact labels. |
| Controlled setup | With user approval, create temporary flat and search-enabled toolboxes from existing configurations. Verify their live manifests match except for search, randomize candidate/arm ordering, then delete both toolboxes after the run. |
| What was not tested | Argument generation, execution, correctness of a completed task or safety of performing an approved write. |

For diagnosis, we separately checked whether the expected tool appeared in the five retrieved results. It did in 138/184 tool-needed trials. Of the search path's 49 errors, 46 were retrieval misses; only three occurred with the expected tool present.

### 2. Custom approval rules: classify a fixed proposed call

| Setup item | What we did |
|---|---|
| Dataset | 50 scenarios: eight reads, ten writes, ten confidentiality/Bing cases, eight combined/scoped rules, six ambiguities, four misleading/untrusted-instruction cases and four approval-lifecycle/multi-step cases. |
| Input to both models | User-authored rule, exact proposed invocation, relevant tool contract, and any needed synthetic document excerpt, publication evidence or authenticated approval record. Expected answers and explanations were withheld. |
| Allowed outputs | `proceed`, `ask_approval`, `ask_clarification`. |
| Expected-label mix | 19 proceed, 25 ask-approval and six ask-clarification scenarios. |
| Effect interpretation | Models inferred effects from method contracts, arguments, Python snippets or shell commands. We did not supply answer-revealing `writes_data` or `trusted_effects` flags. |
| Scoring | Score the fixed invocation independently of routing. Count both ordinary label errors and filtered attempts against all-request accuracy; also inspect required-approval misses and unnecessary prompts. |

For example, a read-only Bing operation can require approval because its outgoing query contains confidential information. An expired approval or changed arguments must not inherit permission from an earlier call. These are interpretation checkpoints, not an installed dynamic-approval system.

Ten separate development cases preceded the main cohort. The published accuracy uses the 50 main scenarios, not those probes. GPT produced 98 valid outputs from 100 attempts; two content-filtered attempts had no reported usage. Both models incorrectly proceeded twice on the same unresolved rule-conflict scenario.

### 3. Request versus proposed call: intent alignment

| Setup item | What we did |
|---|---|
| Dataset | 50 scenarios varying target, recipient, branch, operation, content, quantity/time constraints and missing context. |
| Input to both models | Authenticated user request, supplied conversation context, exact proposed arguments and operation contract. Retrieved text was treated as untrusted data. |
| Allowed outputs | `matches`, `mismatch`, `uncertain`. |
| Label rule | Matches preserves the requested action and scope; mismatch has an observable contradiction; uncertain lacks essential facts about scope or effect. |
| Important separation | A requested write can match intent even when a separate approval check is still required. |

The evaluation checks a proposal, not model-generated arguments. A main-branch update against a dev-only request should be a mismatch; missing deletion scope should trigger uncertainty. We inspected false acceptances separately from overall accuracy.

### 4. Next-step choice: respond to a supplied tool result

| Setup item | What we did |
|---|---|
| Dataset | 50 scenarios covering usable results, empty searches, transient failures, unavailable sources, missing identifiers, access denial, retry budgets and cancellation. |
| Input to both models | User task and constraints, workflow/retry policy, supplied tool result, and any explicitly available authorized alternatives. |
| Allowed outputs | `answer`, `broaden_query`, `retry_same`, `alternate_source`, `ask_user`, `stop`. |
| Label rule | Choose the step justified by the result and policy. Retry only where permitted; do not retry access denial or escalate privileges; stop after cancellation or exhausted budget. |
| What was not tested | Executing the selected step or proving that it eventually completes the task. |

This isolates the decision after a result. For example, an empty overly narrow search can justify broadening within scope, while exhausted retries require stopping. Explicit budgets and cancellation should still be enforced outside the model.

### 5. Evidence sufficiency: assess a fixed evidence bundle

| Setup item | What we did |
|---|---|
| Dataset | 50 scenarios varying environment, tenant, date/version, pagination, units, source authority, redaction and unresolved disagreement. |
| Input to both models | Exact requested question plus supplied evidence and its scope/provenance context. No outside knowledge was needed or permitted by the policy. |
| Allowed outputs | `sufficient`, `insufficient`, `conflicting`. |
| Label rule | Sufficient supports every requested claim in scope; insufficient lacks suitable evidence; conflicting contains relevant credible disagreement not resolved by the supplied context. |
| Error analysis | Inspect false sufficiency separately: accepting unsupported evidence can prematurely stop retrieval. |

This did not evaluate the quality of a generated answer. It evaluated whether the evidence was enough to answer. Both models accepted staging evidence for a production question, a shared wrong-scope failure.

### 6. Confidential disclosure: inspect outgoing content

| Setup item | What we did |
|---|---|
| Dataset | 50 scenarios covering direct quotes, paraphrases, classified identifiers, reversible encoding, attachments, headers, redaction, public/generic overlap, local-only processing and uncertainty. |
| Input to both models | Proposed outgoing request, supplied source information, authoritative sensitivity/publication context and destination evidence. All sensitive-looking fixture content was synthetic. |
| Allowed outputs | `clear`, `disclosure`, `uncertain`. |
| Label rule | Disclosure transmits a protected fact/value; clear contains established public/generic information, removes protected details, or is verified local-only; uncertain lacks necessary sensitivity, content or destination facts. |
| Error analysis | Inspect protected-disclosure-to-clear errors, uncertain-to-clear errors and local-only false alarms separately. |
| What was not tested | Real data transfer, production DLP integration, or permission to transmit data. |

Confidential material elsewhere in context is not itself disclosure unless sent. Conversely, a read-only tool can disclose data in a query. Some uncertainty fixtures used placeholders that could be read as literal safe strings; those cases limit interpretation of the scores.

### Measurement and study limitations

Latency was measured around live API requests, excluding deliberate client pacing. For search selection, total path latency includes the search RPC plus GPT response time. Median and p95 describe observed service/request timings, not controlled hardware performance; shared-service load can affect them.

Tokens are the native API's reported input plus output, not a common tokenizer or dollar cost. Decision-1 generally returned one choice token, whereas GPT returned a structured answer. Search token usage was unavailable: the 494-token number measures only the GPT selector and cannot establish total search-path token consumption.

The four narrow tasks began with 14 intent and 12 each next-step, evidence and disclosure cases. We retained those responses and added 36/38/38/38 new cases after observing earlier errors, reaching 50 in each area. The combined scores are exploratory, not a pristine independent held-out test. Repetitions and related contrast cases are correlated; where uncertainty intervals were calculated, related cases were grouped rather than treating every repetition as independent.

No proposed backend actions executed. Temporary toolbox creation/deletion was authorized setup, not a predicted action. Approval decisions were made on fixed reference invocations, not generated calls, and no real confidential data was transmitted.

## Evidence limits

These were synthetic, assistant-labeled experiments against a Microsoft Foundry project, with labels frozen before inference and raw responses retained locally. Repetitions and contrast pairs are not independent tasks. Some approval trials were content-filtered for GPT and are included in all-request scores; no filters were weakened. Per-use-case samples are small. No proposed tools executed, no real confidential data was transferred, and no end-to-end task success or production safety rate was measured. Selection descriptions and policy semantics affect scores. Deterministic checks can already solve many explicit-rule cases; model value must be demonstrated on harder interpretation tasks.

## Publication scope

This repository contains the findings report and test-method description. Supporting datasets, detailed study reports, scripts and raw responses have not been published here. The methodology explains how the experiments were run, but the exact results cannot be independently reproduced from this README alone.
