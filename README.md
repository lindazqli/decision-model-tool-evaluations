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

## Evidence limits

These were synthetic, assistant-labeled experiments against a Microsoft Foundry project, with labels frozen before inference and raw responses retained locally. Repetitions and contrast pairs are not independent tasks. Some approval trials were content-filtered for GPT and are included in all-request scores; no filters were weakened. Per-use-case samples are small. No proposed tools executed, no real confidential data was transferred, and no end-to-end task success or production safety rate was measured. Selection descriptions and policy semantics affect scores. Deterministic checks can already solve many explicit-rule cases; model value must be demonstrated on harder interpretation tasks.

## Publication scope

This repository contains the findings report only. Supporting datasets, detailed study reports, scripts and raw responses have not been published here. The results cannot be independently reproduced from this README alone.
