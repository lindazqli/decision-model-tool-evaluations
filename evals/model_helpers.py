"""Original native-choice/JSON selector and search parsing helpers."""
import json
import os

DECISION_URL = os.environ.get("DECISION_ENDPOINT", "")
GPT_URL = os.environ.get("GPT_ENDPOINT", "")


def search_tools(row):
    if row["status"] != 200 or "error" in row["response"]:
        raise RuntimeError(f"Search failed: {row['status']}: {row['response']}")
    result = row["response"].get("result", {})
    if result.get("isError"):
        texts = [part.get("text", "") for part in result.get("content", [])]
        if texts and all(text.startswith("No tools matched query") for text in texts):
            return []
        raise RuntimeError(f"Tool search error: {texts}")
    tools = []
    for part in result.get("content", []):
        if part.get("type") == "text":
            parsed = json.loads(part["text"])
            tools.extend(parsed.get("tools", []))
    return tools

def canonical(name):
    return "web_search" if name.startswith("web_search") else name

def choose(session, model, state, policy, options):
    if model == "Decision-1":
        row = session.request(DECISION_URL, {
            "model": model, "state": state,
            "questions": {"route": {"type": "choice", "instructions": policy, "criteria": options}},
        })
    else:
        row = session.request(GPT_URL, {
            "model": model, "reasoning_effort": "minimal", "max_completion_tokens": 256,
            "messages": [
                {"role": "system", "content": policy + " Return exactly one route label in JSON."},
                {"role": "user", "content": json.dumps({"state": state, "options": options})},
            ],
            "response_format": {"type": "json_schema", "json_schema": {
                "name": "selection", "strict": True,
                "schema": {"type": "object", "properties": {"route": {"type": "string", "enum": list(options)}},
                           "required": ["route"], "additionalProperties": False},
            }},
        })
    if row["status"] == 200:
        try:
            if model == "Decision-1":
                answer = row["response"]["answers"]["route"]
                row["selected"] = answer["choice"]
                row["probabilities"] = answer["probabilities"]
            else:
                row["selected"] = json.loads(row["response"]["choices"][0]["message"]["content"])["route"]
            if row["selected"] not in options:
                raise ValueError("Output label not in options")
        except (KeyError, ValueError, TypeError) as error:
            row.pop("selected", None)
            row["parse_error"] = str(error)
    return row

def descriptions(tools):
    return {
        tool["name"]: tool.get("description", "").split("\n\n")[0]
        + "\nRequired arguments: " + json.dumps(tool.get("inputSchema", {}).get("required", []))
        for tool in tools
    }
