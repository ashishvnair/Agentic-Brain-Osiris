#!/usr/bin/env python3
"""
Novel QA, one file, read top to bottom.

THE FLOW
                                 START
                                   |
                                   v
    +------------------------------------------------------------+
    |  load_chapters      in : json_file                          |
    |                     out: chapters                           |
    +------------------------------------------------------------+
                                   |
                                   v
    +------------------------------------------------------------+
    |  build_index        in : chapters                           |
    |                     out: collection                         |
    +------------------------------------------------------------+
                                   |
                                   v
    +------------------------------------------------------------+
    |  next_question      in : questions, qi                      |  <--+
    |                     out: question                           |     |
    +------------------------------------------------------------+     |
                                   |                                    |
                                   v                                    |
    +------------------------------------------------------------+     |
    |  retrieve           in : collection, question               |     |
    |                     out: candidates                         |     |
    +------------------------------------------------------------+     |
                    |                          |                        |
           candidates found            nothing retrieved                |
                    v                          |                        |
    +------------------------------------------+                       |
    |  synthesize         in : question, candidates                     |
    |                     out: answer, confidence, explanation          |
    +------------------------------------------+                       |
                    |                          |                        |
                    v                          v                        |
    +------------------------------------------------------------+     |
    |  report             in : question, answer, confidence       |     |
    |                     out: results, qi                        |     |
    +------------------------------------------------------------+     |
                                   |                                    |
                    more questions -+------------------------------------+
                                   |
                                   v
                                  END

HOW THE FILE IS LAID OUT
    SECTION 1  CORE          the original qa_agentic logic, copied. Only the
                             signatures changed: what were module constants and
                             module-level call_llm / embed_sync are now plain
                             arguments, so nothing reads a global.
    SECTION 2  SERVICES      the two things that talk to a server, built with
                             LangChain: an LLM callable and an embed callable.
    SECTION 3  TRACER        prints each stage, its declared in/out, and every
                             LLM and embedding call.
    SECTION 4  STAGES        one class per box in the diagram. Each declares
                             `expects` and `produces` and does nothing else.
    SECTION 5  ROUTING       the branch functions, one per diamond above.
    SECTION 6  ENGINE        turns a flow into a LangGraph. Generic; you should
                             never need to touch it.
    SECTION 7  FLOW + MAIN   build_flow() is the diagram written as code. main()
                             holds every setting and the index/ask switch.

Install:
    pip install langgraph langchain-openai chromadb

Run:
    python novel_qa.py
"""

import asyncio
import json
import os
import re
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, TypedDict

import chromadb
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.graph import END, StateGraph


# ==========================================================================
# SECTION 1 -- CORE
# The original logic, unchanged except that every setting arrives as an
# argument instead of being read from a module constant.
# ==========================================================================
def clean_llm_response(text: str) -> str:
    """Remove special tokens like <|...|> and extract the main content."""
    text = re.sub(r'<\|[^|]*\|>', '', text).strip()
    return text


def clean_chapter_text(raw: str) -> str:
    """Remove navigation/UI/comment junk, keep only story text."""
    lines = raw.split('\n')
    story_lines = []
    ui_markers = {
        "Prev Chapter", "Next Chapter", "Background", "Light Gray", "Light Blue",
        "Light Yellow", "Warm Ivory", "Pale Green", "Sepia", "Blue Gray", "White",
        "Night", "Font family", "Arial", "Open Sans", "Roboto", "Roboto Condensed",
        "Verdana", "Lora", "Noticia Text", "Times New Roman", "Patrick Hand",
        "OpenDyslexic", "Font size", "16", "18", "20", "22", "24", "26", "28",
        "30", "32", "34", "36", "38", "40", "Line height", "100%", "120%",
        "140%", "160%", "180%", "200%", "New", "Read mode", "Scroll", "Page",
        "Auto resume", "Yes", "No", "Reading width", "Wide", "Normal", "Narrow",
        "No line breaks", "Translate & Text to Speech", "Translate", "Original / English",
        "Spanish", "Portuguese", "French", "German", "Italian", "Indonesian",
        "Vietnamese", "Thai", "Turkish", "Arabic", "Hindi", "Russian", "Japanese",
        "Korean", "Chinese Simplified", "Chinese Traditional", "Default(en-US)",
        "[Translator - Clara]", "[Proofreader - Gun]", "Comments", "Add to Library",
        "Chapter Comments", "Posting Rules", "Spoiler", "Submit", "Best", "Newest",
        "Load More Comments", "Comment Rules", "Commenting Suspended", "View Comment Rules",
        "Home", "Info", "Library", "Use arrow keys", "Add", "Prev", "Next",
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"
    }
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
        if line_stripped in ui_markers or re.match(r'^\d+$', line_stripped):
            continue
        if re.match(r'^Chapter\s+\d+', line_stripped):
            continue
        if any(marker in line_stripped for marker in ["Prev Chapter", "Next Chapter", "Home", "Info"]):
            continue
        story_lines.append(line_stripped)
    return ' '.join(story_lines)


def load_novel_chapters(json_path: str) -> List[Dict]:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    chapters = []
    for item in data:
        ch_num = item["chapter"]
        raw = item.get("content", "")
        clean = clean_chapter_text(raw)
        if len(clean) > 100:
            chapters.append({"chapter": ch_num, "title": item.get("title", ""),
                             "content": clean})
        else:
            print(f"Chapter {ch_num} cleaned content too short ({len(clean)} chars), skipping.")
    return chapters


def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    text = re.sub(r'\s+', ' ', text).strip()
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            for br in ['. ', '! ', '? ']:
                pos = text.rfind(br, start, end)
                if pos > start + chunk_size // 2:
                    end = pos + 1
                    break
        chunks.append(text[start:end].strip())
        start = max(end - overlap, start + 1)
    return [c for c in chunks if len(c) > 50]


def get_or_build_collection(chapters: List[Dict], embed_fn: Callable, db_dir: str,
                            collection_name: str, chunk_size: int, overlap: int,
                            batch_size: int):
    client = chromadb.PersistentClient(path=db_dir)
    try:
        col = client.get_collection(collection_name)
        if col.count() > 0:
            print(f"Using existing collection with {col.count()} chunks.")
            return col
        else:
            print("Collection exists but empty. Rebuilding...")
            client.delete_collection(collection_name)
            col = client.create_collection(collection_name)
    except Exception:
        col = client.create_collection(collection_name)

    print("Building vector collection...")
    all_chunks = []
    all_metas = []
    for ch in chapters:
        ch_num = ch["chapter"]
        chunks = chunk_text(ch["content"], chunk_size, overlap)
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metas.append({"chapter": ch_num, "chunk_index": i})

    for i in range(0, len(all_chunks), batch_size):
        batch_texts = all_chunks[i:i + batch_size]
        batch_metas = all_metas[i:i + batch_size]
        batch_ids = [f"ch{meta['chapter']}_{meta['chunk_index']}" for meta in batch_metas]
        embeddings = embed_fn(batch_texts)
        if embeddings:
            col.add(ids=batch_ids, documents=batch_texts,
                    embeddings=embeddings, metadatas=batch_metas)
        else:
            col.add(ids=batch_ids, documents=batch_texts, metadatas=batch_metas)
        print(f"  Added {len(batch_texts)} chunks")
    return col


async def retrieve_relevant_chunks(col, question: str, embed_fn: Callable,
                                   top_k: int) -> List[Dict]:
    # Try embedding retrieval first
    try:
        q_embed = (await asyncio.to_thread(embed_fn, [question]))[0]
        if q_embed is not None:
            results = col.query(query_embeddings=[q_embed], n_results=top_k,
                                include=["documents", "metadatas", "distances"])
            candidates = []
            for doc, meta, dist in zip(results["documents"][0],
                                       results["metadatas"][0],
                                       results["distances"][0]):
                candidates.append({"text": doc, "chapter": meta["chapter"],
                                   "score": 1 - dist})
            return candidates
    except Exception as e:
        print(f"Embedding retrieval failed, falling back to keyword search: {e}")

    # Fallback: keyword search over all chunks
    print("Performing keyword search...")
    data = col.get(include=["documents", "metadatas"])
    if not data or not data.get("documents"):
        return []
    stopwords = {"what", "when", "where", "which", "who", "why", "how", "did", "does",
                 "was", "were", "the", "and", "for", "from", "with", "that", "this",
                 "are", "have", "has", "had", "its", "it's", "about", "into", "your",
                 "you", "they", "them", "their", "there"}
    keywords = [w for w in re.findall(r'[a-zA-Z]{3,}', question.lower())
                if w not in stopwords]
    candidates = []
    for doc, meta in zip(data["documents"], data["metadatas"]):
        doc_lower = doc.lower()
        score = 0
        for kw in keywords:
            score += doc_lower.count(kw)
        if score > 0:
            candidates.append({"text": doc, "chapter": meta["chapter"], "score": score})
    candidates.sort(key=lambda x: -x["score"])
    return candidates[:top_k]


async def synthesize_answer(question: str, candidates: List[Dict], llm_fn: Callable,
                            snippet_chars: int, evidence_chars: int,
                            answer_tokens: int) -> Tuple[str, float, str]:
    """Ask the LLM for a plain-text answer with a confidence number."""
    evidence = "\n\n".join(
        [f"[Chapter {c['chapter']}]: {c['text'][:snippet_chars]}" for c in candidates])

    system = (
        "You are a research assistant. Answer the question concisely using the evidence. "
        "After your answer, write 'CONFIDENCE: <number between 0 and 100>'."
    )
    prompt = f"QUESTION: {question}\n\nEVIDENCE:\n{evidence[:evidence_chars]}\n\nAnswer:"

    raw = await llm_fn(prompt, system=system, max_tokens=answer_tokens)
    if raw:
        conf_match = re.search(r'CONFIDENCE:\s*(\d+(?:\.\d+)?)', raw, re.IGNORECASE)
        confidence = float(conf_match.group(1)) / 100.0 if conf_match else 0.5
        answer_text = re.sub(r'CONFIDENCE:\s*\d+(?:\.\d+)?\s*%?', '', raw,
                             flags=re.IGNORECASE).strip()
        answer_text = clean_llm_response(answer_text)
        if answer_text:
            return answer_text, confidence, "Plain-text LLM answer"

    # Fallback: return top evidence snippets
    if candidates:
        snippets = "\n\n".join(
            [f"Chapter {c['chapter']}: {c['text'][:300]}" for c in candidates[:3]])
        answer = ("LLM failed to generate a summary. Here are the most relevant "
                  f"passages:\n\n{snippets}")
        return answer, 0.3, "Evidence snippets fallback"
    else:
        return "No answer found.", 0.0, "No evidence available"


# ==========================================================================
# SECTION 2 -- SERVICES
# The only two things that touch a server. Both are built once in main() and
# handed to the stages through the state.
# ==========================================================================
def make_llm(config: dict, tracer: "Tracer") -> Callable:
    """
    in : prompt, system, max_tokens
    out: reply text ("" only if the server truly gave nothing)

    The budget floor and the retry are why answers stopped coming back empty.
    gpt-oss writes its analysis channel first; a 500-token cap on a 5000-char
    evidence prompt is cut mid-thought and no final channel is ever emitted,
    which arrives as content="" and reads downstream as "the LLM failed".
    """
    cache = {}

    def model_for(max_tokens, effort):
        key = (max_tokens, effort)
        if key not in cache:
            cache[key] = ChatOpenAI(
                base_url=config["llm_base_url"],
                api_key=config["api_key"],
                model=config["llm_model"],
                temperature=config["temperature"],
                max_tokens=max_tokens,
                timeout=config["timeout"],
                max_retries=1,
                extra_body={"chat_template_kwargs": {"reasoning_effort": effort}},
            )
        return cache[key]

    async def call_once(messages, cap, effort):
        start = time.time()
        try:
            msg = await model_for(cap, effort).ainvoke(messages)
        except Exception as exc:
            return "", f"error:{type(exc).__name__}", None, time.time() - start, exc
        secs = time.time() - start

        text = msg.content or ""
        if not str(text).strip():
            text = (msg.additional_kwargs or {}).get("reasoning_content") or ""

        meta = msg.response_metadata or {}
        usage = getattr(msg, "usage_metadata", None) or meta.get("token_usage") or {}
        gen = None
        if isinstance(usage, dict):
            gen = usage.get("output_tokens") or usage.get("completion_tokens")

        return clean_llm_response(str(text)), meta.get("finish_reason"), gen, secs, None

    async def llm_fn(prompt, system="", max_tokens=300):
        messages = []
        if system:
            messages.append(SystemMessage(content=system))
        messages.append(HumanMessage(content=prompt))

        effort = config["effort"]
        cap = max(max_tokens, config["token_floor"])

        text, finish, gen, secs, exc = await call_once(messages, cap, effort)
        ok = tracer.llm_call(prompt, text, secs, cap, effort, finish, gen, 1)
        if exc:
            tracer.note(f"[LLM Error] {exc}")

        starved = (not text.strip()) or finish == "length"
        if starved and config["retry_on_truncation"]:
            cap2 = min(cap * 2, config["token_ceiling"])
            tracer.retry(cap2, "low")
            text, finish, gen, secs, exc = await call_once(messages, cap2, "low")
            ok2 = tracer.llm_call(prompt, text, secs, cap2, "low", finish, gen, 2)
            if exc:
                tracer.note(f"[LLM Error] {exc}")
            if ok2 and not ok:
                tracer.rescue()

        return text

    return llm_fn


def make_embedder(config: dict, tracer: "Tracer") -> Callable:
    """
    in : list of texts
    out: list of vectors, or None on failure (None is what triggers the
         keyword-search fallback inside retrieve_relevant_chunks)
    """
    client = OpenAIEmbeddings(
        base_url=config["embed_base_url"],
        api_key=config["api_key"],
        model=config["embed_model"],
        check_embedding_ctx_length=False,   # local servers reject token-id input
    )

    def embed_fn(texts: List[str]) -> Optional[List[List[float]]]:
        start = time.time()
        try:
            vectors = client.embed_documents(list(texts))
            tracer.embed_call(len(texts), time.time() - start, True)
            return vectors
        except Exception as exc:
            tracer.embed_call(len(texts), time.time() - start, False, exc)
            return None

    return embed_fn


# ==========================================================================
# SECTION 3 -- TRACER
# ==========================================================================
class Tracer:
    def __init__(self):
        self.step = 0
        self.stage = "-"
        self.llm_calls = 0
        self.embed_calls = 0
        self.empty = 0
        self.capped = 0
        self.retries = 0
        self.rescued = 0
        self.embed_failures = 0
        self.missing_outputs = 0
        self.llm_seconds = 0.0
        self.embed_seconds = 0.0
        self.started = time.time()

    @staticmethod
    def clip(text, n=320):
        s = str(text).replace("\n", " / ")
        return s if len(s) <= n else s[:n] + f" ...(+{len(s) - n})"

    @staticmethod
    def show(key, value):
        if key == "chapters":
            return f"{len(value)} chapters"
        if key == "candidates":
            if not value:
                return "0 chunks"
            top = ", ".join(f"ch{c['chapter']}={c['score']:.2f}" for c in value[:5])
            return f"{len(value)} chunks [{top}{' ...' if len(value) > 5 else ''}]"
        if key == "results":
            return f"{len(value)} question(s) done"
        if key == "collection":
            try:
                return f"chroma collection, {value.count()} chunks"
            except Exception:
                return "chroma collection"
        if key in ("answer", "question", "explanation"):
            return Tracer.clip(value, 160)
        return repr(value)

    # -- stage boundaries
    def stage_start(self, stage, state):
        self.step += 1
        self.stage = stage.name
        print(f"\n{'=' * 70}")
        print(f"step {self.step:>3}  STAGE  {stage.name}")
        print(f"        {stage.__doc__.strip().splitlines()[0] if stage.__doc__ else ''}")
        print(f"{'-' * 70}")
        for key in stage.expects:
            present = key in state and state[key] not in (None, "", [], {})
            mark = " " if present else "!"
            value = self.show(key, state[key]) if key in state else "<absent>"
            print(f"   {mark} in   {key:<12} = {self.clip(value, 200)}")

    def stage_end(self, stage, patch, secs):
        print(f"{'-' * 70}")
        for key in stage.produces:
            if key not in patch:
                self.missing_outputs += 1
                print(f"   ! out  {key:<12} = <not produced>")
        for key, value in patch.items():
            if key in ("phase", "last"):
                continue
            print(f"     out  {key:<12} = {self.clip(self.show(key, value), 200)}")
        print(f"     took {secs:.2f}s")

    def route(self, frm, to):
        print(f"\n   route  {frm} -> {to}")

    def note(self, msg):
        print(f"     . {msg}")

    # -- service calls
    def llm_call(self, prompt, reply, secs, cap, effort, finish, gen, attempt):
        self.llm_calls += 1
        self.llm_seconds += secs
        bad = []
        if not reply.strip():
            self.empty += 1
            bad.append("EMPTY REPLY")
        if finish == "length" or (gen is not None and gen >= cap):
            self.capped += 1
            bad.append(f"HIT max_tokens={cap}")

        tag = f"llm#{self.llm_calls}" + (f" retry{attempt - 1}" if attempt > 1 else "")
        print(f"     {tag}  {secs:.1f}s  effort={effort}  cap={cap}"
              + (f"  gen={gen}" if gen else "")
              + (f"  finish={finish}" if finish else ""))
        print(f"       prompt: {self.clip(prompt, 200)}")
        print(f"       reply : {self.clip(reply)}")
        for b in bad:
            print(f"       !! {b}")
        return bool(reply.strip())

    def retry(self, cap, effort):
        self.retries += 1
        print(f"       -> retrying at cap={cap} effort={effort}")

    def rescue(self):
        self.rescued += 1
        print(f"       -> retry recovered a usable reply")

    def embed_call(self, count, secs, ok, err=None):
        self.embed_calls += 1
        self.embed_seconds += secs
        if ok:
            print(f"     embed#{self.embed_calls}  {secs:.1f}s  {count} text(s)")
        else:
            self.embed_failures += 1
            print(f"     embed#{self.embed_calls}  FAILED after {secs:.1f}s -- {err}")
            print(f"       !! falling back to keyword search")

    def summary(self):
        wall = time.time() - self.started
        print("\n" + "=" * 70)
        print("TRACE SUMMARY")
        print("=" * 70)
        print(f"  stages run       : {self.step}")
        print(f"  llm calls        : {self.llm_calls}  ({self.llm_seconds:.1f}s)")
        print(f"  embed calls      : {self.embed_calls}  ({self.embed_seconds:.1f}s)")
        print(f"  wall clock       : {wall:.1f}s")
        print(f"  empty replies    : {self.empty}")
        print(f"  hit token cap    : {self.capped}")
        print(f"  retries fired    : {self.retries}  (recovered {self.rescued})")
        print(f"  embed failures   : {self.embed_failures}")
        print(f"  missing outputs  : {self.missing_outputs}")
        if self.capped:
            print("\n  Still hitting the cap. Raise config['token_floor'].")


# ==========================================================================
# SECTION 4 -- STAGES
# One class per box in the diagram. A stage declares what it needs and what
# it hands on, and does nothing else. It never decides what runs next.
# ==========================================================================
class Stage:
    name = "stage"
    expects: Tuple[str, ...] = ()
    produces: Tuple[str, ...] = ()

    async def run(self, state, config, tracer) -> dict:
        raise NotImplementedError


class LoadChapters(Stage):
    """Read the novel file and strip the site furniture out of every chapter."""
    name = "load_chapters"
    expects = ()
    produces = ("chapters",)

    async def run(self, state, config, tracer):
        chapters = await asyncio.to_thread(load_novel_chapters, config["json_file"])
        print(f"Loaded {len(chapters)} chapters after cleaning.")
        return {"chapters": chapters}


class BuildIndex(Stage):
    """Open the Chroma collection, building and embedding it if it is empty."""
    name = "build_index"
    expects = ("chapters",)
    produces = ("collection",)

    async def run(self, state, config, tracer):
        col = await asyncio.to_thread(
            get_or_build_collection,
            state["chapters"], state["embed_fn"], config["db_dir"],
            config["collection_name"], config["chunk_size"],
            config["chunk_overlap"], config["embed_batch"])
        return {"collection": col}


class NextQuestion(Stage):
    """Take the next question off the list and clear the previous answer."""
    name = "next_question"
    expects = ("questions", "qi")
    produces = ("question",)

    async def run(self, state, config, tracer):
        question = state["questions"][state["qi"]]
        print(f"\nQUESTION {state['qi'] + 1}/{len(state['questions'])}: {question}")
        return {"question": question, "candidates": [], "answer": "",
                "confidence": 0.0, "explanation": ""}


class Retrieve(Stage):
    """Embed the question and pull the closest chunks, keyword search if that fails."""
    name = "retrieve"
    expects = ("collection", "question")
    produces = ("candidates",)

    async def run(self, state, config, tracer):
        candidates = await retrieve_relevant_chunks(
            state["collection"], state["question"], state["embed_fn"],
            config["top_k"])
        for i, c in enumerate(candidates[:5], 1):
            tracer.note(f"{i}. ch{c['chapter']} score={c['score']:.2f} "
                        f"{tracer.clip(c['text'], 90)}")
        return {"candidates": candidates}


class Synthesize(Stage):
    """Hand the chunks to the LLM and pull an answer and a confidence out of it."""
    name = "synthesize"
    expects = ("question", "candidates")
    produces = ("answer", "confidence", "explanation")

    async def run(self, state, config, tracer):
        answer, confidence, explanation = await synthesize_answer(
            state["question"], state["candidates"], state["llm_fn"],
            config["snippet_chars"], config["evidence_chars"],
            config["answer_tokens"])
        if explanation == "Evidence snippets fallback":
            tracer.note("fallback fired: the LLM returned nothing usable")
        return {"answer": answer, "confidence": confidence,
                "explanation": explanation}


class Report(Stage):
    """Print the answer and move the question cursor on by one."""
    name = "report"
    expects = ("question", "answer", "confidence")
    produces = ("results", "qi")

    async def run(self, state, config, tracer):
        print("\n" + "-" * 70)
        print(f"ANSWER: {state['question']}")
        print("-" * 70)
        print(state["answer"] or "No answer found.")
        print(f"\nConfidence: {state['confidence']:.0%}")
        print(f"Explanation: {state['explanation'] or 'No evidence available'}")
        print(f"Chunks used: {len(state['candidates'])}")

        results = list(state["results"])
        results.append({"question": state["question"], "answer": state["answer"],
                        "confidence": state["confidence"],
                        "explanation": state["explanation"],
                        "chunks": len(state["candidates"])})
        return {"results": results, "qi": state["qi"] + 1}


class ReportIndex(Stage):
    """Print how big the collection ended up. Terminal stage of the index flow."""
    name = "report_index"
    expects = ("collection",)
    produces = ()

    async def run(self, state, config, tracer):
        try:
            print(f"\nCollection ready: {state['collection'].count()} chunks.")
        except Exception as exc:
            print(f"\nCollection built but could not be counted: {exc}")
        return {}


# ==========================================================================
# SECTION 5 -- ROUTING
# One function per diamond in the diagram. These are the only places where
# the flow can branch.
# ==========================================================================
def more_questions(state) -> str:
    """After build_index and after report: another question, or stop."""
    return "next_question" if state["qi"] < len(state["questions"]) else "end"


def after_retrieval(state) -> str:
    """Nothing retrieved means there is nothing for the LLM to read."""
    return "synthesize" if state["candidates"] else "report"


# ==========================================================================
# SECTION 6 -- ENGINE
# Turns a flow into a LangGraph: one hub node holds every routing decision,
# every stage returns to it. Generic; nothing here knows about novels.
# ==========================================================================
class Step:
    """One box in the diagram plus the arrow leaving it."""

    def __init__(self, stage: Stage, goes_to):
        self.stage = stage
        self.name = stage.name
        self.goes_to = goes_to          # a stage name, "end", or f(state) -> name

    def destination(self, state) -> str:
        return self.goes_to(state) if callable(self.goes_to) else self.goes_to


class Flow:
    """An ordered list of steps with a named entry point."""

    def __init__(self, start: str, steps: List[Step]):
        self.start = start
        self.steps = {s.name: s for s in steps}

    def next_after(self, state) -> str:
        last = state.get("last")
        return self.start if last is None else self.steps[last].destination(state)


class PipelineState(TypedDict, total=False):
    config: dict
    tracer: Any
    llm_fn: Callable
    embed_fn: Callable

    questions: List[str]
    qi: int
    question: Optional[str]
    last: Optional[str]
    next: str

    chapters: List[dict]
    collection: Any
    candidates: List[dict]
    answer: str
    confidence: float
    explanation: str
    results: List[dict]


def compile_flow(flow: Flow):
    async def control(state):
        destination = flow.next_after(state)
        state["tracer"].route(state.get("last") or "START", destination)
        return {"next": destination}

    def make_node(step: Step):
        async def node(state):
            tracer, config = state["tracer"], state["config"]
            tracer.stage_start(step.stage, state)
            start = time.time()
            patch = await step.stage.run(state, config, tracer) or {}
            tracer.stage_end(step.stage, patch, time.time() - start)
            return {**patch, "last": step.name}
        node.__name__ = f"stage_{step.name}"
        return node

    graph = StateGraph(PipelineState)
    graph.add_node("control", control)
    for name, step in flow.steps.items():
        graph.add_node(name, make_node(step))

    graph.set_entry_point("control")
    graph.add_conditional_edges(
        "control",
        lambda state: state["next"],
        {**{name: name for name in flow.steps}, "end": END},
    )
    for name in flow.steps:
        graph.add_edge(name, "control")

    return graph.compile()


async def run_flow(flow: Flow, config: dict, tracer: Tracer,
                   questions: List[str]) -> dict:
    state: PipelineState = {
        "config": config,
        "tracer": tracer,
        "llm_fn": make_llm(config, tracer),
        "embed_fn": make_embedder(config, tracer),
        "questions": questions,
        "qi": 0,
        "question": None,
        "last": None,
        "next": flow.start,
        "chapters": [],
        "collection": None,
        "candidates": [],
        "answer": "",
        "confidence": 0.0,
        "explanation": "",
        "results": [],
    }
    app = compile_flow(flow)
    return await app.ainvoke(state, config={"recursion_limit": 1_000_000})


# ==========================================================================
# SECTION 7 -- FLOW + MAIN
# The diagram at the top of this file, written as code. Read this and you
# know what the program does.
# ==========================================================================
def build_flow(mode: str) -> Flow:
    if mode == "index":
        return Flow(
            start="load_chapters",
            steps=[
                Step(LoadChapters(), goes_to="build_index"),
                Step(BuildIndex(),   goes_to="report_index"),
                Step(ReportIndex(),  goes_to="end"),
            ],
        )

    if mode == "ask":
        return Flow(
            start="load_chapters",
            steps=[
                Step(LoadChapters(), goes_to="build_index"),
                Step(BuildIndex(),   goes_to=more_questions),
                Step(NextQuestion(), goes_to="retrieve"),
                Step(Retrieve(),     goes_to=after_retrieval),
                Step(Synthesize(),   goes_to="report"),
                Step(Report(),       goes_to=more_questions),
            ],
        )

    raise ValueError(f"unknown mode: {mode}")


def print_final(results: List[dict], tracer: Tracer) -> None:
    print("\n" + "=" * 70)
    print("ALL QUESTIONS")
    print("=" * 70)
    for r in results:
        print(f"  [{r['confidence']:.0%}] {r['question']}")
#        print(f"        {tracer.clip(r['answer'], 160)}")
        print(f"        {r['answer']}")
        print(f"        via {r['explanation']} over {r['chunks']} chunks")
    tracer.summary()


def main():
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    config = {
        # servers
        "llm_base_url": "http://127.0.0.1:8080/v1",
        "embed_base_url": "http://127.0.0.1:1234/v1",
        "api_key": "sk-no-key-required",
        "llm_model": "local-model",
        "embed_model": "text-embedding-mxbai-embed-large-v1",
        "timeout": 300,

        # data
        "json_file": "the-problematic-child-of-the-magic-tower_chapters.json",
        "db_dir": "osiris_db",
        "collection_name": "novel_chunks",
        "chunk_size": 800,
        "chunk_overlap": 100,
        "embed_batch": 100,

        # retrieval and synthesis
        "top_k": 15,
        "snippet_chars": 600,
        "evidence_chars": 5000,
        "answer_tokens": 500,

        # generation budget: the floor and the retry are what stop the
        # "LLM failed to generate a summary" fallback from firing
        "temperature": 0.1,
        "effort": "low",
        "token_floor": 1024,
        "token_ceiling": 3072,
        "retry_on_truncation": True,
    }

    questions = [
        "who is oscar sage ?",
        "what's true identity of mad fiend?",
        "what's fran's special power?",
        "why fran couldn't grow stronger?",
        "What's nosfela ?",
        "Who discovered that Zephyr-01 could do better?",
        "What did the King try to name the flying Bikes ?"
    ]

    tracer = Tracer()

    type = "ask"

    if type == "index":
        asyncio.run(run_flow(build_flow("index"), config, tracer, questions))
        tracer.summary()
    elif type == "ask":
        final = asyncio.run(run_flow(build_flow("ask"), config, tracer, questions))
        print_final(final["results"], tracer)
    else:
        print(f"unknown type: {type}")


if __name__ == "__main__":
    main()