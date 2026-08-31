"""
Osiris v1 - Infinite Autonomous Engine
- SearXNG Docker JSON Support (Aggregates surviving search engines automatically)
- True Infinite Loop (Runs until LLM satisfies checklist constraints)
- Full End-of-Run Telemetry & Token Tracking
"""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
import urllib.error

# Ensure Windows displays Unicode characters cleanly
if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        try: stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception: pass

# ============================================================
# CONFIGURATION
# ============================================================
BASE_URL = "http://127.0.0.1:8080"
SEARXNG_URL = "http://localhost:8888/search"
TEMPERATURE = 0.2
MIN_P = 0.05

# ============================================================
# TELEMETRY TRACKER
# ============================================================
class TelemetryTracker:
    def __init__(self):
        self.start_time = time.time()
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.llm_time_sec = 0.0
        self.llm_calls = 0

    def record_call(self, usage, elapsed):
        if usage:
            self.prompt_tokens += usage.get("prompt_tokens", 0) or 0
            self.completion_tokens += usage.get("completion_tokens", 0) or 0
        self.llm_time_sec += elapsed
        self.llm_calls += 1

    def print_summary(self, model_name):
        total_time = time.time() - self.start_time
        total_tokens = self.prompt_tokens + self.completion_tokens
        avg_speed = self.completion_tokens / self.llm_time_sec if self.llm_time_sec > 0 else 0.0

        emit("\n" + "═" * 60)
        emit(" TELEMETRY & RUN SUMMARY")
        emit("═" * 60)
        emit(f" Model Name          : {model_name}")
        emit(f" Total Task Time     : {total_time:.2f} seconds")
        emit(f" LLM Generation Time : {self.llm_time_sec:.2f} seconds across {self.llm_calls} call(s)")
        emit(f" Prompt Tokens       : {self.prompt_tokens:,}")
        emit(f" Completion Tokens   : {self.completion_tokens:,}")
        emit(f" Total Tokens Used   : {total_tokens:,}")
        emit(f" Avg Generation Speed: {avg_speed:.2f} tokens/sec")
        emit("═" * 60)

# ============================================================
# STATE MANAGEMENT
# ============================================================
class OsirisState:
    def __init__(self, goal, constraints):
        self.goal = goal
        self.constraints = constraints
        self.dossier = {"verified_facts": {}, "dead_ends": []}
        self.round = 0
        self.consecutive_searches = 0
        self.searched_queries = set()
        self.final_answer = None

    def commit_finding(self, cid, fact, source):
        for c in self.constraints:
            if c["id"] == cid: c["status"] = "CONFIRMED"
        self.dossier["verified_facts"][str(cid)] = {"fact": fact, "source": source}
        self.consecutive_searches = 0

    def mark_unresolvable(self, cid, reason):
        for c in self.constraints:
            if c["id"] == cid: c["status"] = "UNRESOLVABLE"
        self.dossier["verified_facts"][str(cid)] = {"fact": "[UNRESOLVABLE]", "source": reason}
        self.consecutive_searches = 0

    def record_dead_end(self, path, reason):
        if "DUPLICATE" not in reason.upper() and "ERROR" not in reason.upper():
            self.consecutive_searches = 0
        self.dossier["dead_ends"].append({"path": path, "reason": reason})

    def all_questions_resolved(self):
        for c in self.constraints:
            if c["kind"] == "question" and c["status"] not in ["CONFIRMED", "UNRESOLVABLE"]: return False
        return True

    def get_missing_constraints(self):
        return [c["id"] for c in self.constraints if c["kind"] == "question" and c["status"] not in ["CONFIRMED", "UNRESOLVABLE"]]

    def to_prompt_context(self):
        lines = [
            f"GOAL: {self.goal}",
            "\n--- CUMULATIVE DOSSIER (Locked Conclusions) ---"
        ]
        if self.dossier["verified_facts"]:
            for cid, data in self.dossier["verified_facts"].items():
                lines.append(f"  [{cid}] {data['fact']} (Source/Reason: {data['source']})")
        else:
            lines.append("  (No facts locked yet)")

        if self.dossier["dead_ends"]:
            lines.append("\n--- DISPROVEN PATHS / DEAD ENDS ---")
            for de in self.dossier["dead_ends"][-4:]:
                lines.append(f"  [DEAD END] {de['path']} -> {de['reason']}")

        lines.append("\n--- ACTIVE CONSTRAINTS ---")
        for c in self.constraints:
            lines.append(f"  [{c['id']}] ({c['status'].upper()}) [{c['kind']}] {c['desc']}")
        return "\n".join(lines)

# ============================================================
# UTILITIES & LLM INTERFACE
# ============================================================
def emit(text):
    print(text)
    with open("osiris_v1_scratchpad.log", "a", encoding="utf-8") as f:
        f.write(text + "\n")

def fetch_model_name():
    try:
        req = urllib.request.Request(f"{BASE_URL}/props")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            path = data.get("model_path") or data.get("default_generation_settings", {}).get("model") or "llama.cpp"
            return os.path.basename(str(path))
    except Exception:
        return "llama.cpp Local Model"

def extract_text_and_reasoning(message_obj):
    content = message_obj.get("content") or ""
    reasoning = message_obj.get("reasoning_content") or message_obj.get("thought") or ""
    if "<think>" in content and "</think>" in content:
        parts = re.split(r"</think>", content, maxsplit=1)
        reasoning += " " + parts[0].replace("<think>", "").strip()
        content = parts[1].strip()
    return reasoning.strip(), content.strip()

def chat_completion(messages, tools=None):
    payload = {"messages": messages, "temperature": TEMPERATURE, "min_p": MIN_P, "max_tokens": 1500}
    if tools: payload["tools"] = tools
    req = urllib.request.Request(
        f"{BASE_URL}/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"], data.get("usage", {}), time.time() - t0

def execute_search(query, is_linkedin=False):
    # Using 'linkedin profile' instead of 'site:linkedin' gives SearXNG better hits across non-Google engines
    search_q = f"{query} linkedin profile" if is_linkedin else query
    params = {"q": search_q, "format": "json", "categories": "general", "language": "en"}
    
    try:
        url = f"{SEARXNG_URL}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        
        results = data.get("results", [])[:6]
        if not results: 
            return f"[NO RESULTS FOUND for query: '{search_q}'. SearXNG returned zero hits.]", False
            
        results_text = []
        for r in results:
            title = r.get("title", "").strip()
            href = r.get("url", "").strip()
            content = r.get("content", "").strip()
            if title or content: results_text.append(f"Title: {title}\nURL: {href}\nSnippet: {content}\n")
        return "\n".join(results_text), True
        
    except Exception as e:
        return f"[SEARCH ERROR] Connection failed. Is SearXNG running? Error: {e}", False

# ============================================================
# TOOL SCHEMAS
# ============================================================
SEARCH_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web via SearXNG.",
            "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "linkedin_search",
            "description": "Search for LinkedIn profiles and career histories.",
            "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
        }
    }
]

MUTATION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "commit_finding",
            "description": "Lock a verified fact into the dossier. Use this immediately when an observation answers a pending constraint.",
            "parameters": {
                "type": "object",
                "properties": {
                    "constraint_id": {"type": "integer"},
                    "fact": {"type": "string"},
                    "source": {"type": "string"}
                },
                "required": ["constraint_id", "fact", "source"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mark_unresolvable",
            "description": "Formally mark a constraint as UNRESOLVABLE (e.g. prompt mixes up disjoint people, or network keeps failing).",
            "parameters": {
                "type": "object",
                "properties": {
                    "constraint_id": {"type": "integer"},
                    "reason": {"type": "string"}
                },
                "required": ["constraint_id", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "record_dead_end",
            "description": "Record a failed search query, wrong profile, or empty result so you do not repeat it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "reason": {"type": "string"}
                },
                "required": ["path", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "finalize_answer",
            "description": "Synthesize final output. Call ONLY when all constraints have a corresponding checklist item.",
            "parameters": {
                "type": "object",
                "properties": {
                    "constraint_checklist": {
                        "type": "array",
                        "description": "Mandatory checklist verifying every constraint ID.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "constraint_id": {"type": "integer"},
                                "status": {"type": "string", "enum": ["CONFIRMED", "UNRESOLVABLE"]},
                                "proof_or_reason": {"type": "string"}
                            },
                            "required": ["constraint_id", "status", "proof_or_reason"]
                        }
                    },
                    "final_summary": {"type": "string"},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]}
                },
                "required": ["constraint_checklist", "final_summary", "confidence"]
            }
        }
    }
]

ALL_TOOLS = SEARCH_TOOLS + MUTATION_TOOLS

def simple_planner(query, telemetry):
    emit("[Planning] Decomposing task into actionable constraints...")
    sys_prompt = "You are a research planner. Break the user query into a JSON list of constraints. Schema: { 'constraints': [ {'id': 1, 'desc': '...', 'kind': 'given|question'} ] }"
    try:
        msg, usage, elapsed = chat_completion([{"role": "system", "content": sys_prompt}, {"role": "user", "content": query}])
        telemetry.record_call(usage, elapsed)
        _, content = extract_text_and_reasoning(msg)
        match = re.search(r"\{.*\}", content, re.DOTALL)
        data = json.loads(match.group(0))
        constraints = data.get("constraints", [])
        for c in constraints: c["status"] = "PENDING"
        if constraints: return constraints
    except Exception: pass
    return [
        {"id": 1, "desc": "Identify and isolate the correct single entity matching the background.", "kind": "given", "status": "PENDING"},
        {"id": 2, "desc": query, "kind": "question", "status": "PENDING"}
    ]

def check_finalize(state, args):
    checklist = args.get("constraint_checklist", [])
    checklist_map = {item["constraint_id"]: item for item in checklist if isinstance(item, dict)}
    missing_ids = [c["id"] for c in state.constraints if c["id"] not in checklist_map]
    if missing_ids: return False, f"Checklist incomplete. Missing IDs: {missing_ids}. You MUST include an item for every constraint ID."
    if not state.all_questions_resolved(): return False, f"Question constraints {state.get_missing_constraints()} are still PENDING. Call `commit_finding` or `mark_unresolvable` first."
    return True, "Accepted"


def run_agent(query):
    telemetry = TelemetryTracker()
    model_name = fetch_model_name()
    constraints = simple_planner(query, telemetry)
    state = OsirisState(query, constraints)
    
    emit("\n" + "═" * 60)
    emit(" OSIRIS v1 - INFINITE AUTONOMOUS ENGINE")
    emit(f" Model    : {model_name}")
    emit(f" Search   : SearXNG Backend ({SEARXNG_URL})")
    emit(f" Task     : {query}")
    emit("═" * 60 + "\n")
    
    latest_observation = ""
    
    # INFINITE LOOP - Runs until LLM finalizes successfully
    while True:
        state.round += 1
        emit(f"\n+--- ROUND {state.round} (Autonomous) ---+")
        
        # Reflection Harness - Forces LLM to evaluate if it spams searches without locking facts
        if state.consecutive_searches >= 3:
            emit(f"  [HARNESS GATE] {state.consecutive_searches} searches executed without state update.")
            active_tools = MUTATION_TOOLS
            reflection_notice = "\n\n*** HARNESS OVERRIDE: SEARCH TOOLS DISABLED THIS TURN ***\nYou MUST evaluate your findings: use `commit_finding` if you found a fact, or `mark_unresolvable` if the entity is fake/disjoint, or `record_dead_end`."
        else:
            active_tools = ALL_TOOLS
            reflection_notice = ""

        system_instructions = f"""You are Osiris v1, a stateful investigative research engine.
OPERATIONAL DIRECTIVES:
1. DO NOT RE-SEARCH facts already CONFIRMED or UNRESOLVABLE.
2. EVALUATE LATEST OBSERVATION: If it answers a constraint, call `commit_finding`.
3. ENTITY DISAMBIGUATION: If search results show facts belong to DIFFERENT people, recognize the conflict. Call `mark_unresolvable`.
4. If a search query fails, call `record_dead_end`. If searches continually yield nothing, call `mark_unresolvable`.
5. Call `finalize_answer` as soon as all constraints are accounted for.
6. Issue EXACTLY ONE tool call per turn.{reflection_notice}"""

        prompt_context = state.to_prompt_context()
        if latest_observation: prompt_context += f"\n\n--- LATEST OBSERVATION ---\n{latest_observation}"

        try:
            message, usage, elapsed = chat_completion([{"role": "system", "content": system_instructions}, {"role": "user", "content": prompt_context}], tools=active_tools)
            telemetry.record_call(usage, elapsed)
        except Exception as e:
            emit(f"[SERVER ERROR] {e}")
            time.sleep(5)
            continue
            
        reasoning, _ = extract_text_and_reasoning(message)
        if reasoning: emit(f"[Thought]\n{reasoning}")
            
        tool_calls = message.get("tool_calls", [])
        if not tool_calls:
            latest_observation = "[ERROR] No tool called. You MUST call exactly one tool to advance the investigation."
            emit(latest_observation)
            continue
            
        tc = tool_calls[0]
        func_name = tc["function"]["name"]
        try: args = json.loads(tc["function"]["arguments"])
        except Exception: args = {}
            
        emit(f"[Action] {func_name}({json.dumps(args)})")
        
        if func_name in ["web_search", "linkedin_search"]:
            query_key = args.get("query", "").strip().lower()
            
            # Anti-Loop: Blocks exact identical search strings being spammed
            if query_key in state.searched_queries:
                latest_observation = f"[SYSTEM BLOCK] DUPLICATE QUERY: '{query_key}'. HARNESS BLOCKED THIS. You MUST alter keywords or use `record_dead_end`/`mark_unresolvable`."
                emit(f"  -> {latest_observation}")
                state.consecutive_searches += 1
                continue
                
            state.searched_queries.add(query_key)
            obs_text, success = execute_search(args.get("query", ""), is_linkedin=(func_name=="linkedin_search"))
            state.consecutive_searches += 1
            latest_observation = obs_text
            
            emit(f"  -> SearXNG search {'succeeded' if success else 'failed'}. Returned {len(obs_text)} chars.")
            
        elif func_name == "commit_finding":
            state.commit_finding(args.get("constraint_id"), args.get("fact"), args.get("source"))
            latest_observation = f"[SUCCESS] Fact locked."
            emit(f"  -> {latest_observation}")

        elif func_name == "mark_unresolvable":
            state.mark_unresolvable(args.get("constraint_id"), args.get("reason"))
            latest_observation = f"[SUCCESS] Marked UNRESOLVABLE."
            emit(f"  -> {latest_observation}")
            
        elif func_name == "record_dead_end":
            state.record_dead_end(args.get("path"), args.get("reason"))
            latest_observation = "[SUCCESS] Dead end recorded."
            emit(f"  -> {latest_observation}")
            
        elif func_name == "finalize_answer":
            valid, msg = check_finalize(state, args)
            if not valid:
                latest_observation = f"[REJECTED BY HARNESS GATE] {msg}"
                emit(f"  -> {latest_observation}")
            else:
                state.final_answer = args.get("final_summary")
                emit("\n" + "═" * 60 + "\n FINAL DOSSIER COMPILED\n" + "═" * 60)
                for cid, data in state.dossier["verified_facts"].items():
                    emit(f" [{cid}] {data['fact']}\n     Source/Reason: {data['source']}")
                emit("\n>>> FINAL ANSWER:\n" + state.final_answer)
                break

    # Loop has broken cleanly, print Telemetry
    telemetry.print_summary(model_name)

if __name__ == "__main__":
    if len(sys.argv) > 1: run_agent(" ".join(sys.argv[1:]))
    else: print('Usage: python osiris_v1_core.py "<task>"')