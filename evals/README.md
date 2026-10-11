# Run the evaluations

Python 3.10+ and Azure CLI are required; the Python code uses only the standard library. Run commands from the repository root.

## Offline

```powershell
python evals\run.py build --output runs\trial
python -m unittest discover -s tests
```

Build freezes 350 scenarios and their expected labels. The original fixture generators and choice/search helpers were extracted from the study code; transport and runner were adapted for portable configuration. Historical catalog snapshots and responses are not included. A fresh run is a new study, not a replay of the reported latency/accuracy.

## Live model calls

Sign in to your intended Azure tenant and set your own full endpoints:

```powershell
az login
$env:DECISION_ENDPOINT = 'https://YOUR-RESOURCE.services.ai.azure.com/providers/microsoft/v1/systemone'
$env:GPT_ENDPOINT = 'https://YOUR-RESOURCE.services.ai.azure.com/openai/v1/chat/completions'
python evals\run.py run --output runs\trial --task intent
python evals\run.py analyze --output runs\trial --task intent
```

Task names: `intent`, `next_step`, `evidence`, `disclosure`, `approval`, `selection`. Each run makes two calls per model per case and incurs model usage. GPT uses the `gpt-5-mini` deployment with minimal reasoning. Credentials are obtained via Azure CLI and never written to results.

## Selection and approval

Supply a local `catalog.json` containing the `result.tools` array from your flat toolbox's `tools/list` response. Each entry needs `name`, `description`, `inputSchema`, and optional `annotations`. The fixtures use the historical capability names; incompatible/missing capabilities fail before inference. Approval inputs require the relevant detailed operation contracts, not just tool names.

```powershell
python evals\run.py run --output runs\trial --task approval --catalog catalog.json
$env:SEARCH_ENDPOINT = 'https://YOUR-RESOURCE.services.ai.azure.com/api/projects/YOUR-PROJECT/toolboxes/YOUR-SEARCH-TOOLBOX/versions/1/mcp?api-version=v1'
python evals\run.py run --output runs\trial --task selection --catalog catalog.json
python evals\run.py analyze --output runs\trial --task selection
```

For a controlled selection comparison, configure your search toolbox with the same executable capabilities as the flat catalog; the runner rejects retrieved tools outside that catalog. It does not create/change toolboxes or verify live manifest equality. It calls only `tool_search` metadata, never a selected backend tool.

## Outputs

`cases.json` and `protocol.json` freeze the labels and dataset hash. Each task writes raw local JSONL responses and an analysis JSON with accuracy, median/p95 latency, and mean reported model tokens. Filter/invalid outputs remain failures; no model mistakes are retried. One authentication refresh on HTTP 401 is permitted. Partial runs cannot be scored as complete and are not automatically resumed.

The four narrow task datasets combine original and later expansion cohorts. Synthetic strings marked confidential are fixtures, not actual private data. Local catalog snapshots and responses can contain your own metadata: review them before sharing; `runs/` is ignored by Git.

## Stateful workflow comparison

```powershell
python evals\workflow_eval.py build --output runs\workflow
python evals\workflow_eval.py run --output runs\workflow
python evals\workflow_eval.py analyze --output runs\workflow
```

This uses the same model endpoints but no live toolbox. It runs 50 tasks through GPT-only native tool calling, GPT plus Decision-1 routing/approval, and GPT plus deterministic exact-rule guards. All tools are stateful local mocks; web search returns fixtures and approval is simulated. GPT generates arguments and final answers in every arm.

Each task has an eight-GPT-step budget and one trial per arm. The hybrid receives the full tool contracts as context while its callable tools are restricted by Decision-1; this avoids hiding argument schemas, but adds prompt overhead. A final answer is scored against expected values and mock state, with mandatory write read-back. The code guard uses structured facts and exact fixture matching, not a general-purpose DLP engine.

Workflow latency sums live model request durations and excludes pacing, simulated user time and real tool/network latency. Raw wall time is also retained. Token usage includes every GPT and Decision call, including failed tasks. Different native tokenizers are not a common cost unit; use deployment-specific input/output prices for monetary comparisons.
