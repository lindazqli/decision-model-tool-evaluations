import argparse
import hashlib
import json
import math
import os
import random
import statistics
from collections import Counter
from pathlib import Path

from explore_tools_dataset import cases as approval_cases
from model_helpers import canonical, choose, descriptions, search_tools
from study_fixtures import APPROVAL_OPTIONS, APPROVAL_POLICY, POLICY, fixtures, representation
from tool_decision_cases import OPTIONS, POLICIES, cases as original_cases
from tool_decision_expansion_cases import cases as expanded_cases
from transport import Session


def dataset():
    narrow = original_cases() + expanded_cases()
    assert Counter(c["task"] for c in narrow) == {task: 50 for task in POLICIES}
    rows = list(narrow)
    for case in approval_cases():
        rows.append({
            "id": case["id"], "task": "approval",
            "input": {**case["input"], "current_repository": {"owner": "fixture-org", "repo": "widget"},
                      "proposed_call": case["proposed_call"]},
            "reference": {"expected": case["reference"]["approval"], "reason": case["reference"]["reason"]},
        })
    rows.extend({"id": c["id"], "task": "selection", "input": c["query"],
                 "reference": {"expected": c["expected"]}, "category": c["category"]} for c in fixtures())
    assert len(rows) == len({c["id"] for c in rows}) == 350
    return rows


def build(output):
    output.mkdir(parents=True, exist_ok=False)
    content = json.dumps(dataset(), indent=2).encode()
    (output / "cases.json").write_bytes(content)
    (output / "protocol.json").write_text(json.dumps({
        "cases_sha256": hashlib.sha256(content).hexdigest(),
        "counts": dict(Counter(c["task"] for c in dataset())),
        "repetitions": 2, "models": ["Decision-1", "gpt-5-mini"],
        "labels": "Original assistant-authored expectations; not independently reviewed.",
        "scope": "Inference and explicit search metadata only; no backend tool execution.",
        "runner": "Portable adaptation; historical responses and catalog are not included.",
    }, indent=2), encoding="utf-8")


def load_cases(output):
    content = (output / "cases.json").read_bytes()
    protocol = json.loads((output / "protocol.json").read_text(encoding="utf-8"))
    if hashlib.sha256(content).hexdigest() != protocol["cases_sha256"]:
        raise ValueError("Dataset changed after build; use a fresh output directory.")
    return json.loads(content)


def load_catalog(path):
    tools = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(tools, list):
        raise ValueError("Catalog must be a tools/list result.tools JSON array.")
    catalog = {canonical(t["name"]): {**t, "name": canonical(t["name"])} for t in tools}
    if len(catalog) != len(tools):
        raise ValueError("Catalog contains duplicate names or aliases.")
    if {"tool_search", "call_tool"} & catalog.keys():
        raise ValueError("Remove search/dispatcher wrappers from the executable catalog.")
    return catalog


def run(output, task, catalog_path):
    cases = [c for c in load_cases(output) if c["task"] == task]
    path = output / f"{task}-results.jsonl"
    if path.exists():
        raise FileExistsError("Refusing to overwrite results; build a fresh output directory.")
    catalog = load_catalog(catalog_path) if catalog_path else {}
    search_url = os.environ.get("SEARCH_ENDPOINT", "")
    if task in {"approval", "selection"}:
        if not catalog:
            raise ValueError("Selection and approval require --catalog.")
        needed = ({c["reference"]["expected"] for c in cases} - {"none"} if task == "selection"
                  else {c["input"]["proposed_call"]["name"] for c in cases})
        missing = needed - catalog.keys()
        if missing:
            raise ValueError(f"Catalog missing fixture capabilities: {sorted(missing)}")
    if task == "selection" and not search_url:
        raise ValueError("Selection requires SEARCH_ENDPOINT for actual toolbox search.")
    if task in {"approval", "selection"}:
        (output / f"{task}-catalog.json").write_text(json.dumps(list(catalog.values()), indent=2), encoding="utf-8")
    jobs = [(c, rep) for c in cases for rep in range(2)]
    random.Random(20261010).shuffle(jobs)
    session = Session(search_url=search_url, gpt_pacing=8 if task == "approval" else 4)
    try:
        with path.open("x", encoding="utf-8") as stream:
            for index, (case, rep) in enumerate(jobs, 1):
                rng = random.Random(case["id"] + str(rep))
                arms = ["Decision-1", "search_gpt" if task == "selection" else "gpt-5-mini"]
                rng.shuffle(arms)
                for arm in arms:
                    state = case["input"]
                    if task == "approval":
                        call = state["proposed_call"]
                        state = {**state, "tool_contract": {
                            "name": call["name"], "contract": json.loads(representation(catalog[call["name"]]))}}
                        policy, options = APPROVAL_POLICY, APPROVAL_OPTIONS
                    elif task == "selection":
                        policy, options = POLICY, descriptions(list(catalog.values()))
                        options["none"] = "No listed capability fulfills the request, or no tool is needed."
                    else:
                        policy, options = POLICIES[task], OPTIONS[task]
                    search = None
                    if arm == "search_gpt":
                        search = session.request(search_url, {
                            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
                            "params": {"name": "tool_search", "arguments": {"query": state, "limit": 5}},
                        })
                        found = search_tools(search)
                        names = [canonical(t["name"]) for t in found]
                        if any(name not in catalog for name in names):
                            raise ValueError("Search returned a tool outside the supplied catalog.")
                        options = descriptions([{**t, "name": canonical(t["name"])} for t in found])
                        options["none"] = "No listed capability fulfills the request, or no tool is needed."
                    entries = list(options.items())
                    rng.shuffle(entries)
                    row = choose(session, "gpt-5-mini" if arm == "search_gpt" else arm,
                                 state, policy, dict(entries))
                    if search is not None:
                        row["selector_ms"] = row["latency_ms"]
                        row["latency_ms"] += search["latency_ms"]
                        row["search"] = search
                        row["retrieval_hit"] = case["reference"]["expected"] in names
                    row.update({"case_id": case["id"], "task": task, "arm": arm, "repetition": rep,
                                "expected": case["reference"]["expected"]})
                    row["correct"] = canonical(row.get("selected", "")) == row["expected"]
                    stream.write(json.dumps(row) + "\n")
                    stream.flush()
                    if "selected" not in row:
                        print(f"Invalid response: {case['id']} {arm} HTTP {row['status']}", flush=True)
                if index % 10 == 0:
                    print(f"{task}: {index}/{len(jobs)} paired trials", flush=True)
    finally:
        session.close()


def summarize(rows):
    result = {}
    for arm in sorted({r["arm"] for r in rows}):
        attempts = [r for r in rows if r["arm"] == arm]
        valid = [r for r in attempts if "selected" in r]
        tokens = []
        for row in valid:
            usage = row.get("usage", {})
            if "input_tokens" in usage and "output_tokens" in usage:
                tokens.append(usage["input_tokens"] + usage["output_tokens"])
            elif "prompt_tokens" in usage and "completion_tokens" in usage:
                tokens.append(usage["prompt_tokens"] + usage["completion_tokens"])
        timings = sorted(r["latency_ms"] for r in valid)
        result[arm] = {
            "attempts": len(attempts), "valid": len(valid),
            "accuracy": sum(r["correct"] for r in attempts) / len(attempts),
            "median_ms": statistics.median(timings) if timings else None,
            "p95_ms": timings[max(0, math.ceil(.95 * len(timings)) - 1)] if timings else None,
            "usage_reporting_valid_responses": len(tokens),
            "mean_reported_model_tokens": statistics.mean(tokens) if tokens else None,
            "search_tokens": "unavailable" if arm == "search_gpt" else "not applicable",
        }
    return result


def analyze(output, task):
    cases = [c for c in load_cases(output) if c["task"] == task]
    rows = [json.loads(line) for line in (output / f"{task}-results.jsonl").read_text(encoding="utf-8").splitlines()]
    arms = ["Decision-1", "search_gpt" if task == "selection" else "gpt-5-mini"]
    expected = Counter((c["id"], rep, arm) for c in cases for rep in range(2) for arm in arms)
    if Counter((r["case_id"], r["repetition"], r["arm"]) for r in rows) != expected:
        raise ValueError("Incomplete or duplicate trials; refusing to report a complete evaluation.")
    result = summarize(rows)
    (output / f"{task}-analysis.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["build", "run", "analyze"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--task", choices=["selection", "approval", *POLICIES])
    parser.add_argument("--catalog", type=Path)
    args = parser.parse_args()
    if args.mode == "build":
        build(args.output)
    elif not args.task:
        parser.error("--task is required for run and analyze")
    elif args.mode == "run":
        run(args.output, args.task, args.catalog)
    else:
        analyze(args.output, args.task)
