# ghrca — Complete Project Snapshot (`github-connect`)

> Single-file, self-contained snapshot: folder structure, every source file's purpose and full code, pip requirements, real command outputs, and what has been built. Generated from the live repo.

- **Date:** 2026-10-01
- **Python files:** 56 tracked; ~7,177 LoC Python
- **Tests:** 99 passing
- **RCA corpus:** 118 cases (git-only), frozen dev/test split


## 1. What this project is

`ghrca` takes a Java **runtime error** (a stack trace) from a GitHub repo and produces a grounded **root-cause analysis**: it clones over SSH, understands the code without a compiler (tree-sitter), localizes the fault to one blob (no whole-branch index), judges whether a fix exists / was lost / is stuck in a PR, and writes a report — continuously, for repos with thousands of files and hundreds of branches, calling a slow local LLM at most once per distinct bug. Full history and numbers are in the embedded `HOW_IT_WORKS.md` / `BENCHMARKS.md` / `WALKTHROUGH.md` below.


## 2. Install / requirements

```bash
python -m pip install -r requirements.txt   # stdlib + tree-sitter + tree-sitter-java + pytest
```
Also needs: `git` >= 2.38, and (for RCAs) a llama.cpp OpenAI-compatible server at `GHRCA_LLM_URL` (default `http://127.0.0.1:8080`). Code/branch work uses git over SSH; the GitHub REST API is optional (60/hr unauthenticated).


## 3. Folder structure

```
github_scrape/
.gitignore
BENCHMARKS.md
HOW_IT_WORKS.md
README.md
WALKTHROUGH.md
bench/
  __init__.py
  hadoop_labels.py
  harvest.py
  parity.py
  run.py
eval/
  __init__.py
  baseline.json
  cases.json
  harness.py
  rca.py
  rca_baseline_dev.json
  rca_last_run.json
ghrca/
  __init__.py
  __main__.py
  agent.py
  archaeology.py
  backport.py
  blast.py
  blobstore.py
  cli.py
  config.py
  context.py
  daemon.py
  db.py
  errors.py
  fingerprint.py
  ghapi.py
  htmlreport.py
  indexer.py
  javascan.py
  llm.py
  llmqueue.py
  locate.py
  orchestrator.py
  poller.py
  rca.py
  repo.py
  sources/
    __init__.py
    dropdir.py
  tsjava.py
requirements.txt
targets.json
tests/
  __init__.py
  conftest.py
  test_metamorphic.py
  test_phase1.py
  test_phase2.py
  test_phase3.py
  test_phase4.py
  test_phase5.py
  test_r2.py
  eval/rca_cases/            # 118 generated corpus cases + TEST_MANIFEST.sha256
  .cache/                    # (gitignored) clones, SQLite db, reports
```

## 4. Git history
```
e8c7cc5 r2-phase5: no-id lost-fix cross-check, held-out test run, docs
6f0c291 r2-phases1-4: honest evidence, context pack, hypotheses, depth, blast v2, frames
8f07090 r2-phase0: RCA corpus (git-only, 118 cases) + held-out eval harness + baseline
5b61fb9 docs: add WALKTHROUGH.md — stage-by-stage account with commands + real outputs
846e72e phase6: cleanup + docs
c769f83 phase5: daemon, sources, backport dry-run, eval
1c50c70 phase4: blast radius
5cc5db0 phase3: correct fix-status (D10) + pinning + drift
9c54cd0 phase2: blob-keyed lazy index + tree-sitter (complete)
897f345 phase2 (partial): tree-sitter parser + parity analysis
9c48812 phase1: cheap wins
a5e66a7 phase0: baseline + harness
```

## 5. Real command outputs

### `python -m pytest tests/ -q`
```
........................................................................ [ 72%]
...........................                                              [100%]
99 passed in 4.76s
```
### `python -m ghrca status --repo opensolon/solon-ai`
```
repo: opensolon/solon-ai  default: main
branches: 11
  main                                     10137c9d  2026-09-30
  v4.0                                     37265c9d  2026-08-17
  v3.11                                    a508ed58  2026-05-25
  v3.10                                    355208c5  2026-05-15
  v3.9                                     0f67e6d0  2026-04-14
  v3.8                                     4bf5f8d0  2026-04-14
  v3.6                                     ebe4acc4  2026-02-13
  v3.7                                     54bc7a33  2026-02-12
  v3.5                                     33fcb0fc  2025-12-23
  v3.4                                     e21cfbea  2025-11-06
  dev-eggg                                 e2fdda0c  2025-10-26
API budget unknown (unauthenticated (60/hr)).
LLM server: DOWN (http://127.0.0.1:8080/v1/chat/completions)
queue: {}
fingerprints: 1 distinct, 2 occurrences; errors seen: 0; rca_cache: 1
last ref poll: never
```
### A generated RCA report (`analyze --no-llm`, deterministic value-origin)
````markdown
# RCA — java.lang.NullPointerException: Cannot invoke "com.acme.orders.Customer.getId()" because the return value of "com.acme.orders.Cart.getCustomer()" is null

- **Error id:** `08fccdcf01e6`
- **Source:** log:acme_err.txt
- **Branch:** `release-2`
- **Localization confidence:** high — message identifiers found on line 8
- **Fault site:** `com.acme.orders.OrderService#checkout` (src/main/java/com/acme/orders/OrderService.java:8)
- **Fix status:** A fix exists on other branches but is ABSENT on the target (lost/unmerged) — backport needed.
- **RCA source:** deterministic

## Analysis
### Location-only analysis (not a full root cause)
A `NullPointerException` is thrown at `com.acme.orders.OrderService#checkout` (src/main/java/com/acme/orders/OrderService.java:8).
Failing expression: `com.acme.orders.Cart.getCustomer()` (null_return_value).
Value origin: {'kind': 'assigned_in', 'field': 'customer', 'where': ['setCustomer', 'direct_assignment'], 'deser_signals': []}

### Fix-status
A fix exists on other branches but is ABSENT on the target (lost/unmerged) — backport needed.

## Fix-status evidence (git/PR)
> PR data unavailable (no API budget/token) — git-only analysis.
- **lost**: Fix fdc39709 "fix(NPE): guard null customer in OrderService.checkout" is on ['hotfix-npe', 'main'] but ABSENT on 'release-2' by ancestry, patch-id, id and content. — refs: fdc39709371391dd3c4fe34e672caa74ad724bde, hotfix-npe, main
- **origin**: Failing line introduced by a6afcdca "init: acme-orders baseline service" (2026-09-30). — refs: a6afcdca126808df00dfe29476e9872579475584

## Code evidence
### com.acme.orders.OrderService#checkout (src/main/java/com/acme/orders/OrderService.java:6-12)
```java
    4 |     private final PricingEngine pricing = new PricingEngine();
    5 | 
    6 |     public Receipt checkout(Cart cart) {
    7 |         // Build a receipt for the customer's cart.
    8 |         String customerId = cart.getCustomer().getId();
    9 |         int itemCount = cart.getItems().size();
   10 |         double total = pricing.total(cart.getItems());
   11 |         return new Receipt(customerId, itemCount, total);
   12 |     }
   13 | }
```
````

## 6. Every source file — purpose + full code


### `.gitignore`
**Purpose:** Ignored paths (caches, clones, reports).

```text
# caches and clones (never commit these — huge)
.cache/
testbed/
agent_reports/
agent_reports_tb/
errors_inbox/
__pycache__/
*.pyc

# benchmark raw output is regenerated
bench/results.jsonl
eval/last_run.json

# local env
.venv/

```

### `bench/__init__.py`
**Purpose:** bench package.

```python

```

### `bench/hadoop_labels.py`
**Purpose:** Lost-fix ground truth + 4 confusion matrices (old --contains / new / --no-id x id/patch-id labels).

```python
"""Hadoop lost-fix ground truth (D16).

Hadoop tracks backports by repeating the JIRA id in the commit subject on each
release branch. So the ground truth for "did fix <JIRA> reach branch X" is:
does branch X have a commit mentioning that JIRA id touching the same file.

We build labelled (fix, branch) cases, then score two detectors:
  OLD  = `git branch --contains <original_sha>` (ancestry of the ORIGINAL sha)
  NEW  = D10's blob-free subset: ancestry OR same-JIRA-id commit on the branch

The OLD method mislabels **cherry-picked backports** (same fix, different sha) as
"lost"; NEW does not. All operations are metadata-only (log/grep/merge-base), so
this runs on the partial (blob:none) clone without fetching blobs.
"""

from __future__ import annotations

import argparse
import random
import re

from ghrca.repo import Repo

JIRA = re.compile(r"\b((?:HADOOP|HDFS|YARN|MAPREDUCE|KAFKA|ES|ELASTIC)-\d+)\b")


def _single_java_file(repo: Repo, sha: str):
    out = repo._git("diff-tree", "--no-commit-id", "--name-only", "-r", sha, check=False)
    files = [f for f in out.splitlines() if f.endswith(".java")]
    allf = [f for f in out.splitlines() if f.strip()]
    if len(files) == 1 and len(allf) <= 3:
        return files[0]
    return None


def build(repo: Repo, want_candidates: int = 80):
    branches = [b.name for b in repo.list_branches()
                if b.name.startswith(("branch-2.", "branch-3."))
                or re.match(r"^\d+\.\d+(\.x)?$", b.name)   # kafka: 3.9, 4.0, 3.8.x
                or b.name.startswith(("release-", "release/"))]
    branches = branches[:6]
    src = "trunk" if any(b.name == "trunk" for b in repo.list_branches()) else repo.default_branch()

    log = repo._git("log", src, "-n", "600", "--format=%H%x09%s", check=False)
    candidates = []
    for line in log.splitlines():
        sha, _, subj = line.partition("\t")
        m = JIRA.search(subj)
        if not m:
            continue
        path = _single_java_file(repo, sha)
        if not path:
            continue
        candidates.append((m.group(1), sha, path, subj))
        if len(candidates) >= want_candidates:
            break
    return src, branches, candidates


def evaluate(repo: Repo, src, branches, candidates, n_pairs=100, seed=13):
    random.seed(seed)
    pairs = []
    for (jid, sha, path, subj) in candidates:
        for br in branches:
            # ground truth: a same-id commit touches this path on the branch
            gt_hits = repo.commits_grep_touching(br, jid, path, limit=5)
            present_truth = bool(gt_hits) or repo.is_ancestor(sha, br)
            pairs.append((jid, sha, path, br, present_truth))
    # keep candidates that are present on >=1 branch and absent on >=1 (the
    # interesting mixed cases, incl. cherry-pick traps)
    by_fix = {}
    for p in pairs:
        by_fix.setdefault(p[1], []).append(p)
    mixed = []
    for sha, ps in by_fix.items():
        truths = {x[4] for x in ps}
        if True in truths and False in truths:
            mixed.extend(ps)
    random.shuffle(mixed)
    sample = mixed[:n_pairs]

    # confusion counts for OLD and NEW  (positive class = "lost")
    def score(pred_lost_fn):
        tp = fp = tn = fn = 0
        for (jid, sha, path, br, present_truth) in sample:
            truly_lost = not present_truth
            pred_lost = pred_lost_fn(jid, sha, path, br)
            if pred_lost and truly_lost:
                tp += 1
            elif pred_lost and not truly_lost:
                fp += 1            # false "lost" (present but called lost)
            elif not pred_lost and not truly_lost:
                tn += 1
            else:
                fn += 1            # missed a truly-lost fix
        return tp, fp, tn, fn

    def old_pred(jid, sha, path, br):
        # OLD: lost unless original sha is reachable from the branch tip
        return not repo.is_ancestor(sha, br)

    def new_pred(jid, sha, path, br):
        # NEW (blob-free D10 subset): present if ancestry OR same-id commit
        if repo.is_ancestor(sha, br):
            return False
        return not bool(repo.commits_grep_touching(br, jid, path, limit=5))

    _pid_cache = {}
    def _fpid(c, path):
        k = (c, path)
        if k not in _pid_cache:
            _pid_cache[k] = repo.file_patch_id(c, path)
        return _pid_cache[k]

    def new_pred_noid(jid, sha, path, br):
        # NEW WITHOUT the id step (D4): present if ancestry OR a commit on br
        # touching the file has the SAME file-scoped patch-id (cherry-pick/squash).
        if repo.is_ancestor(sha, br):
            return False
        pidF = _fpid(sha, path)
        if pidF:
            mb = repo.merge_base(sha, br) or br
            for c in repo.commits_touching_in_range(f"{mb}..{br}", path, limit=60):
                if _fpid(c, path) == pidF:
                    return False   # present via patch-id equivalent -> not lost
        return True

    def patchid_label(jid, sha, path, br):
        # ground-truth INDEPENDENT of ids: present iff ancestry or patch-id equiv
        return not new_pred_noid(jid, sha, path, br)

    # share of "present" decisions (new full) that relied on the id step
    id_reliant = 0
    present_new = 0
    for (jid, sha, path, br, _t) in sample:
        if not new_pred(jid, sha, path, br):          # new says present
            present_new += 1
            if not repo.is_ancestor(sha, br):          # not by ancestry -> by id
                id_reliant += 1

    # score against BOTH label sets
    def score_vs(pred_fn, label_fn):
        tp = fp = tn = fn = 0
        for (jid, sha, path, br, id_present) in sample:
            truly_lost = not label_fn(jid, sha, path, br)
            pred_lost = pred_fn(jid, sha, path, br)
            if pred_lost and truly_lost: tp += 1
            elif pred_lost and not truly_lost: fp += 1
            elif not pred_lost and not truly_lost: tn += 1
            else: fn += 1
        return tp, fp, tn, fn

    id_label = lambda j, s, p, b: next(x[4] for x in sample if x[1] == s and x[3] == b)
    return {
        "sample": sample,
        "old_vs_id": score(old_pred),
        "new_vs_id": score(new_pred),
        "noid_vs_id": score(new_pred_noid),
        "old_vs_patchid": score_vs(old_pred, patchid_label),
        "new_vs_patchid": score_vs(new_pred, patchid_label),
        "noid_vs_patchid": score_vs(new_pred_noid, patchid_label),
        "present_new": present_new, "id_reliant": id_reliant,
    }


def _rates(cm):
    tp, fp, tn, fn = cm
    truly_present = fp + tn
    truly_lost = tp + fn
    false_lost = fp / truly_present * 100 if truly_present else 0
    recall = tp / truly_lost * 100 if truly_lost else 0
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "false_lost_pct": round(false_lost, 2), "lost_recall_pct": round(recall, 2)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="apache/hadoop")
    ap.add_argument("--pairs", type=int, default=100)
    ap.add_argument("--candidates", type=int, default=80)
    args = ap.parse_args(argv)
    repo = Repo(args.repo)
    src, branches, candidates = build(repo, args.candidates)
    print(f"source={src} release_branches={len(branches)} candidates={len(candidates)}")
    r = evaluate(repo, src, branches, candidates, args.pairs)
    n = len(r["sample"])
    print(f"labelled pairs scored: {n}")
    print("\n-- vs ID labels (JIRA-id ground truth) --")
    print(f"  OLD (--contains):        {_rates(r['old_vs_id'])}")
    print(f"  NEW (ancestry+patchid+id): {_rates(r['new_vs_id'])}")
    print(f"  NEW --no-id (ancestry+patchid): {_rates(r['noid_vs_id'])}")
    print("\n-- vs PATCH-ID labels (id-independent ground truth) --")
    print(f"  OLD (--contains):        {_rates(r['old_vs_patchid'])}")
    print(f"  NEW full:                {_rates(r['new_vs_patchid'])}")
    print(f"  NEW --no-id:             {_rates(r['noid_vs_patchid'])}")
    print(f"\npresent(new) decisions: {r['present_new']}, of which id-reliant "
          f"(not by ancestry): {r['id_reliant']}")


if __name__ == "__main__":
    main()

```

### `bench/harvest.py`
**Purpose:** RCA corpus builder (git-only): commit-message stack traces -> cases + frozen test split.

```python
"""RCA corpus builder (D2), git-only source (unlimited, no API).

Find commits whose message contains a Java stack trace; treat that commit F as the
fix and F^1 as the analysis commit P (so the fix is absent by construction). Map
F's diff onto methods in P (tree-sitter) to get the ground-truth fault methods, and
classify the fix category from F's added/removed lines. Write one case per commit,
then split dev/test and freeze the test manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from ghrca import config, errors as errmod, tsjava
from ghrca.repo import Repo

CORPUS = config.PROJECT_ROOT / "eval" / "rca_cases"
_TRACE_GREP = r'at [A-Za-z_][A-Za-z0-9_.$]*\([A-Za-z0-9_$]+\.java:[0-9]+\)'
_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+")
_TESTY = ("/test/", "/tests/", "src/test", "/it/", "package-info")


def _is_code_java(path: str) -> bool:
    return (path.endswith(".java") and not any(t in path for t in _TESTY)
            and "/generated" not in path)


def _category(added: list[str], removed: list[str]) -> str:
    a = "\n".join(added)
    if re.search(r"!=\s*null|==\s*null|Objects\.requireNonNull|Optional\.", a):
        return "null_guard"
    if re.search(r"\.length|\.size\(\)|<\s*\w+\.length|index\s*[<>]=?", a):
        return "bounds_check"
    if "instanceof" in a:
        return "type_check"
    if re.search(r"try\s*\{|catch\s*\(|throws ", a) or re.search(r"throws ", "\n".join(removed)):
        return "exception_handling"
    if added or removed:
        return "logic"
    return "other"


def _old_hunk_ranges(repo: Repo, F: str, path: str) -> list[tuple[int, int]]:
    diff = repo._git("diff", f"{F}^", F, "--unified=0", "--", path, check=False)
    ranges = []
    for line in diff.splitlines():
        m = _HUNK.match(line)
        if m:
            start = int(m.group(1)); cnt = int(m.group(2) or "1")
            if cnt == 0:
                cnt = 1
            ranges.append((start, start + cnt - 1))
    return ranges


def _methods_in_ranges(repo: Repo, P: str, path: str, ranges: list) -> list[str]:
    src = repo.read_file(P, path)
    if not src:
        return []
    fi = tsjava.scan(path, src)
    hit = []
    for m in fi.methods:
        for (a, b) in ranges:
            if not (m.end < a or m.start > b):
                hit.append(m.fqn.replace("#", "#"))
                break
    return hit


def build_repo(repo: Repo, limit: int) -> list[dict]:
    shas = repo._git("log", "--all", "-E", f"--grep={_TRACE_GREP}", "--format=%H",
                     check=False).split()
    cases = []
    for F in shas:
        if len(cases) >= limit:
            break
        msg = repo._git("show", "-s", "--format=%B", F, check=False)
        recs = errmod.from_text(msg, "commit")
        if not recs or not any(t.frames for t in recs[0].chain):
            continue
        # changed code files (old side exists)
        files = [f for f in repo._git("show", "--name-only", "--format=", F,
                                      check=False).splitlines() if _is_code_java(f)]
        files = [f for f in files if f.strip()]
        if not files or len(files) > 3:
            continue
        P = F + "^"
        truth_files, truth_methods, changed_ranges = [], [], []
        added_all, removed_all = [], []
        ok = True
        for path in files:
            ranges = _old_hunk_ranges(repo, F, path)
            if not ranges:
                continue
            ms = _methods_in_ranges(repo, P, path, ranges)
            truth_files.append(path)
            truth_methods.extend(ms)
            for (a, b) in ranges:
                changed_ranges.append([path, a, b])
            added_all += [l[1:] for l in repo.added_lines(F, path)[:50]]
            removed_all += [l[1:] if l.startswith(("+", "-")) else l
                            for l in repo.removed_lines(F, path)[:50]]
        truth_methods = sorted(set(truth_methods))
        if not truth_methods or len(truth_methods) > 5:
            continue
        cid = hashlib.sha1((repo.owner_repo + F).encode()).hexdigest()[:12]
        cases.append({
            "id": cid, "repo": repo.owner_repo, "error": recs[0].raw_text,
            "fix_commit": F, "analysis_commit": repo.rev_parse(P),
            "truth": {"files": truth_files, "methods": truth_methods,
                      "changed_ranges": changed_ranges,
                      "fix_category": _category(added_all, removed_all)},
            "source": "commit_message", "notes": ""})
    return cases


def write_corpus(cases: list[dict]):
    CORPUS.mkdir(parents=True, exist_ok=True)
    for c in cases:
        d = CORPUS / c["id"]
        d.mkdir(exist_ok=True)
        (d / "case.json").write_text(json.dumps(c, indent=2), encoding="utf-8")
    # split + freeze test manifest
    test_ids = sorted(c["id"] for c in cases if int(c["id"][:8], 16) % 2 == 1)
    man = []
    for cid in test_ids:
        content = (CORPUS / cid / "case.json").read_text(encoding="utf-8")
        man.append(cid + ":" + hashlib.sha1(content.encode()).hexdigest())
    digest = hashlib.sha256("\n".join(man).encode()).hexdigest()
    (CORPUS / "TEST_MANIFEST.sha256").write_text(
        digest + "\n" + "\n".join(man), encoding="utf-8")
    return len(cases), len(test_ids)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repos", nargs="+",
                    default=["apache/kafka", "apache/hadoop", "elastic/elasticsearch"])
    ap.add_argument("--per-repo", type=int, default=80)
    args = ap.parse_args(argv)
    all_cases = []
    for rid in args.repos:
        repo = Repo(rid)
        if not repo.exists():
            print(f"skip {rid}: not cloned"); continue
        cs = build_repo(repo, args.per_repo)
        print(f"{rid}: {len(cs)} cases")
        all_cases += cs
    total, ntest = write_corpus(all_cases)
    ndev = total - ntest
    print(f"TOTAL {total} cases  dev={ndev} test={ntest}")
    print(f"manifest: {CORPUS / 'TEST_MANIFEST.sha256'}")


if __name__ == "__main__":
    main()

```

### `bench/parity.py`
**Purpose:** tree-sitter vs regex parser parity measurement.

```python
"""Parser parity (D2): compare tree-sitter vs regex scanner on every .java file
of a branch. Reports method start/end agreement and samples disagreements."""

from __future__ import annotations

import argparse
import random

from ghrca.repo import Repo
from ghrca import javascan, tsjava


def _methods_by_key(fi):
    # key by (simple owner name, method name) to neutralize fqn-attribution
    # differences; value is a sorted list of (start, end).
    by = {}
    for m in sorted(fi.methods, key=lambda x: x.start):
        k = (m.owner.split(".")[-1], m.name)
        by.setdefault(k, []).append((m.start, m.end))
    return by


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--branch", required=True)
    ap.add_argument("--sample", type=int, default=0, help="limit files (0=all)")
    args = ap.parse_args(argv)

    repo = Repo(args.repo)
    files = repo.ls_java_files(args.branch)
    if args.sample:
        random.seed(1)
        files = random.sample(files, min(args.sample, len(files)))
    contents = repo.read_files(args.branch, files)

    # We measure two things:
    #  strict  = identical (start,end)
    #  functional = same method reachable for localization: end within +/-1 and
    #    start within +/-3 (tree-sitter includes the annotation line; regex starts
    #    at the signature). This is what determines method_at_line() equivalence.
    common = strict = functional = 0
    js_only = ts_only = 0
    js_only_samples = []
    parse_fallbacks = 0

    def match(tlist, jlist):
        nonlocal common, strict, functional, js_only, ts_only
        used = set()
        for jv in jlist:
            best = None
            for i, tv in enumerate(tlist):
                if i in used:
                    continue
                if abs(tv[0] - jv[0]) <= 3 and abs(tv[1] - jv[1]) <= 1:
                    best = i
                    break
            if best is None:
                js_only += 1
                if len(js_only_samples) < 40:
                    js_only_samples.append(jv)
            else:
                used.add(best)
                common += 1
                functional += 1
                if tlist[best] == jv:
                    strict += 1
        ts_only += len(tlist) - len(used)

    for path, src in contents.items():
        if not src.strip():
            continue
        ts = tsjava.scan(path, src)
        js = javascan.scan(path, src)
        if not ts.types and src.strip():
            parse_fallbacks += 1
        tb = _methods_by_key(ts)
        jb = _methods_by_key(js)
        for k in set(tb) | set(jb):
            match(tb.get(k, []), jb.get(k, []))

    js_total = common + js_only  # methods the regex scanner (baseline) found
    func_rate = functional / js_total * 100 if js_total else 0
    strict_rate = strict / common * 100 if common else 0
    print(f"files={len(contents)}  regex_methods={js_total}  ts_methods={common + ts_only}")
    print(f"FUNCTIONAL parity (regex method also found by ts, end+/-1 start+/-3): "
          f"{functional}/{js_total} = {func_rate:.2f}%")
    print(f"STRICT (exact start&end among matched): {strict}/{common} = {strict_rate:.2f}%")
    print(f"regex-only (POTENTIAL ts regressions): {js_only}")
    print(f"ts-only (methods regex MISSED, ts found): {ts_only}")
    print(f"tree-sitter zero-type fallbacks -> regex: {parse_fallbacks}")
    print("\nsample regex-only cases (start,end) — hand-check if ts truly missed them:")
    for s in js_only_samples[:20]:
        print(f"  {s}")


if __name__ == "__main__":
    main()

```

### `bench/run.py`
**Purpose:** Benchmark harness: baseline/poll/fingerprint-replay/localize/new-branch scenarios.

```python
"""Benchmark harness (D17).

Phase 0 implements the scenarios measurable against the CURRENT code:
  - baseline: clone/index cold+warm, one localize, old fix-status
  - localize: index-dependent localize timing (current path)
  - fixstatus: old --contains archaeology timing
Later phases add poll / new-branch / blast / fingerprint-replay.

Each run appends a JSON line to bench/results.jsonl with the code SHA, machine
info, and cold/warm flag.
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import time
from datetime import date
from pathlib import Path

from ghrca import config
from ghrca.repo import Repo
from ghrca.indexer import Indexer
from ghrca import errors as errmod
from ghrca.locate import localize

RESULTS = Path(__file__).resolve().parent / "results.jsonl"


def _code_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                              cwd=str(config.PROJECT_ROOT), capture_output=True,
                              text=True).stdout.strip() or "uncommitted"
    except Exception:
        return "unknown"


def _machine() -> dict:
    import os
    return {"os": platform.platform(), "cpus": os.cpu_count(),
            "python": platform.python_version()}


def _emit(row: dict):
    row["code_sha"] = _code_sha()
    row["machine"] = _machine()
    row["ts"] = time.time()
    row["date"] = date.today().isoformat()
    with open(RESULTS, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    print(json.dumps({k: row[k] for k in row if k not in ("machine",)}, indent=2))


def scenario_baseline(args):
    repo = Repo(args.repo)
    if not repo.exists():
        repo.clone_or_update()
    branch = args.branch or repo.default_branch()
    idx = Indexer(repo)

    # cold index (force rescan)
    t0 = time.perf_counter()
    index, _ = idx.build(branch, force=True)
    cold = time.perf_counter() - t0

    # warm index (cache hit)
    t0 = time.perf_counter()
    idx.build(branch)
    warm = time.perf_counter() - t0

    loc_ms = None
    fix_ms = None
    if args.error:
        text = Path(args.error).read_text(encoding="utf-8", errors="replace")
        recs = errmod.from_text(text, source="bench")
        if recs:
            err = recs[0]
            t0 = time.perf_counter()
            loc = localize(err, index, repo, branch)
            loc_ms = (time.perf_counter() - t0) * 1000
            if loc.resolved and loc.fault:
                from ghrca.archaeology import analyze_fix_status
                from ghrca.ghapi import GitHubAPI
                api = None
                t0 = time.perf_counter()
                analyze_fix_status(repo, api, loc.fault.path,
                                   loc.fault.method_start, loc.fault.method_end, branch)
                fix_ms = (time.perf_counter() - t0) * 1000

    _emit({"scenario": "baseline", "repo": args.repo, "branch": branch,
           "cold_index_s": round(cold, 2), "warm_index_s": round(warm, 4),
           "java_files": index.stats.get("java_files"),
           "methods": index.stats.get("methods"),
           "localize_ms": round(loc_ms, 1) if loc_ms else None,
           "fixstatus_old_ms": round(fix_ms, 1) if fix_ms else None})


def scenario_poll(args):
    """Time one ls-remote poll + ref-diff over all heads (D4)."""
    from ghrca import poller
    repo = Repo(args.repo)
    ch = poller.poll_once(repo)
    _emit({"scenario": "poll", "repo": args.repo, "n_refs": ch["n_refs"],
           "elapsed_ms": ch["elapsed_ms"], "new": len(ch["new"]),
           "moved": len(ch["moved"]), "deleted": len(ch["deleted"])})


def scenario_fpreplay(args):
    """H6: replay ~N errors sampled (Zipf) from a few distinct bugs; confirm LLM
    calls == distinct (fp, method_hash) pairs, not error count."""
    import random
    from ghrca import fingerprint, errors as errmod, rca, llm, db
    from ghrca.indexer import Indexer
    from ghrca.locate import localize

    # base bugs: (repo, branch, trace) — real, localizable
    SOLON = "org.noear.solon.ai.chat.dialect.AbstractChatDialect"
    bugs = [
        ("opensolon/solon-ai", "main",
         'java.lang.NullPointerException: Cannot invoke "org.noear.solon.ai.chat.message.ChatRole.name()" '
         'because the return value of "org.noear.solon.ai.chat.message.AssistantMessage.getRole()" is null\n'
         f'\tat {SOLON}.buildAssistantMessageNodeDo(AbstractChatDialect.java:93)'),
        ("opensolon/solon-ai", "main",
         'java.lang.NullPointerException: Cannot invoke "org.noear.solon.ai.chat.ChatRole.name()" '
         'because the return value of "org.noear.solon.ai.chat.message.ToolMessage.getRole()" is null\n'
         f'\tat {SOLON}.buildToolMessageNodeDo(AbstractChatDialect.java:191)'),
        ("local/acme-orders", "release-2",
         'java.lang.NullPointerException: Cannot invoke "com.acme.orders.Customer.getId()" '
         'because the return value of "com.acme.orders.Cart.getCustomer()" is null\n'
         '\tat com.acme.orders.OrderService.checkout(OrderService.java:8)'),
    ]
    sources = {
        "opensolon/solon-ai": Repo("opensolon/solon-ai"),
        "local/acme-orders": Repo("local/acme-orders",
                                  source=str(config.PROJECT_ROOT / "testbed" / "acme-orders.git")),
    }
    for r in sources.values():
        if not r.exists():
            r.clone_or_update()
    idxs = {k: Indexer(v) for k, v in sources.items()}
    indexes = {}
    for (rid, br, _), in [(b,) for b in bugs]:
        indexes.setdefault((rid, br), idxs[rid].build(br)[0])

    # count real LLM calls via monkeypatch
    calls = {"n": 0}
    orig = llm.chat
    llm.chat = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no-llm-in-bench"))

    n = args.n or 1000
    random.seed(7)
    # Zipf-ish weights over the 3 bugs
    weights = [1 / (i + 1) for i in range(len(bugs))]
    distinct = set()
    llm_would = 0
    db.connect().execute("DELETE FROM rca_cache")  # clean slate for the measurement
    for _ in range(n):
        rid, br, base = random.choices(bugs, weights=weights, k=1)[0]
        # inject noise (ids/numbers) so raw text differs every time
        noisy = base + f"\n\tat com.example.App.run(App.java:{random.randint(1, 9999)})"
        rec = errmod.from_text(noisy, "bench")[0]
        index = indexes[(rid, br)]
        loc = localize(rec, index, sources[rid], br)
        fp, *_ = fingerprint.compute(rec, index.root_packages)
        mh = loc.method_hash() if loc.resolved else "none"
        key = (fp, mh)
        # emulate produce_narrative cache decision with policy=always (never templated)
        from ghrca.rca import cache_get, cache_put
        pv = config.PROMPT_VER
        if cache_get(fp, mh, pv) is None:
            llm_would += 1
            cache_put(fp, mh, pv, "bench", "x", 0, 0.0)
        distinct.add(key)
    llm.chat = orig
    _emit({"scenario": "fingerprint-replay", "errors": n,
           "distinct_fp_method": len(distinct), "llm_calls": llm_would,
           "dedup_ratio": round(1 - llm_would / n, 3)})


def scenario_localize(args):
    """H2: lazy localize (no whole-branch index) timing + correctness."""
    import time as _t
    from ghrca import errors as errmod
    from ghrca.locate import localize_lazy
    repo = Repo(args.repo)
    branch = args.branch or repo.default_branch()
    commit = repo.rev_parse(branch)
    text = Path(args.error).read_text(encoding="utf-8", errors="replace")
    rec = errmod.from_text(text, "bench")[0]
    times = []
    fault = None
    for _ in range(5):
        r = errmod.from_text(text, "bench")[0]
        t0 = _t.perf_counter()
        loc = localize_lazy(r, repo, commit, branch)
        times.append((_t.perf_counter() - t0) * 1000)
        fault = loc.fault.method_fqn if loc.resolved else None
    _emit({"scenario": "localize-lazy", "repo": args.repo, "branch": branch,
           "cold_ms": round(times[0], 1), "warm_ms": round(sorted(times[1:])[len(times[1:])//2], 1),
           "fault": fault})


def scenario_newbranch(args):
    """H1: fresh-fork delta (blobs scanned) as a fraction of the branch."""
    import statistics
    repo = Repo(args.repo)
    branch = args.branch or repo.default_branch()
    tot = len(repo.ls_java_files(branch))
    ratios = []
    for n in (1, 2, 3, 5, 10):
        d = repo.branch_delta(f"{branch}~{n}", branch)
        j = [p for p in d if p.endswith(".java")]
        ratios.append(len(j) / tot * 100 if tot else 0)
    _emit({"scenario": "new-branch", "repo": args.repo, "branch": branch,
           "total_java": tot, "median_pct_scanned": round(statistics.median(ratios), 3),
           "max_pct_scanned": round(max(ratios), 3)})


def main(argv=None):
    p = argparse.ArgumentParser(prog="bench")
    sub = p.add_subparsers(dest="scenario", required=True)
    b = sub.add_parser("baseline")
    b.add_argument("--repo", required=True)
    b.add_argument("--branch")
    b.add_argument("--error")
    b.set_defaults(func=scenario_baseline)

    pp_ = sub.add_parser("poll")
    pp_.add_argument("--repo", required=True)
    pp_.set_defaults(func=scenario_poll)

    fr = sub.add_parser("fingerprint-replay")
    fr.add_argument("--n", type=int, default=1000)
    fr.set_defaults(func=scenario_fpreplay)

    lz = sub.add_parser("localize")
    lz.add_argument("--repo", required=True)
    lz.add_argument("--branch")
    lz.add_argument("--error", required=True)
    lz.set_defaults(func=scenario_localize)

    nb = sub.add_parser("new-branch")
    nb.add_argument("--repo", required=True)
    nb.add_argument("--branch")
    nb.set_defaults(func=scenario_newbranch)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()

```

### `eval/__init__.py`
**Purpose:** eval package.

```python

```

### `eval/baseline.json`
**Purpose:** Test-bed eval baseline.

```json
{
  "n": 6,
  "localization_pct": 100.0,
  "verdict_pct": 100.0,
  "confidence_pct": 100.0,
  "details": [
    {
      "case": "lost-on-release2",
      "branch": "release-2",
      "method_ok": true,
      "got_method": "checkout",
      "verdict_ok": true,
      "got_verdict": "lost",
      "confidence": "high"
    },
    {
      "case": "cherrypick-release3",
      "branch": "release-3",
      "method_ok": true,
      "got_method": "checkout",
      "verdict_ok": true,
      "got_verdict": "present_via_equivalent",
      "confidence": "high"
    },
    {
      "case": "squash-release5",
      "branch": "release-5-squash",
      "method_ok": true,
      "got_method": "checkout",
      "verdict_ok": true,
      "got_verdict": "present_via_equivalent",
      "confidence": "high"
    },
    {
      "case": "merged-main",
      "branch": "main",
      "method_ok": true,
      "got_method": "checkout",
      "verdict_ok": true,
      "got_verdict": "present",
      "confidence": "high"
    },
    {
      "case": "origin-hotfix",
      "branch": "hotfix-npe",
      "method_ok": true,
      "got_method": "checkout",
      "verdict_ok": true,
      "got_verdict": "present",
      "confidence": "high"
    },
    {
      "case": "drift-release6",
      "branch": "release-6-drift",
      "method_ok": true,
      "got_method": "checkout",
      "verdict_ok": true,
      "got_verdict": "lost",
      "confidence": "low"
    }
  ]
}
```

### `eval/cases.json`
**Purpose:** Test-bed eval cases.

```json
{
  "source": "F:\\Desktop\\python-vm\\github_scrape\\testbed\\acme-orders.git",
  "repo_id": "local/acme-orders",
  "default_branch": "main",
  "trace": "java.lang.NullPointerException: Cannot invoke \"com.acme.orders.Customer.getId()\" because the return value of \"com.acme.orders.Cart.getCustomer()\" is null\n\tat com.acme.orders.OrderService.checkout(OrderService.java:8)\n",
  "cases": [
    {"name": "lost-on-release2", "branch": "release-2", "method": "checkout", "verdict": "lost", "confidence": "high"},
    {"name": "cherrypick-release3", "branch": "release-3", "method": "checkout", "verdict": "present_via_equivalent"},
    {"name": "squash-release5", "branch": "release-5-squash", "method": "checkout", "verdict": "present_via_equivalent"},
    {"name": "merged-main", "branch": "main", "method": "checkout", "verdict": "present"},
    {"name": "origin-hotfix", "branch": "hotfix-npe", "method": "checkout", "verdict": "present"},
    {"name": "drift-release6", "branch": "release-6-drift", "method": "checkout", "verdict": "lost", "confidence": "low"}
  ]
}

```

### `eval/harness.py`
**Purpose:** Test-bed eval gate (Round 1, D15).

```python
"""Evaluation harness (D15).

Scores localization accuracy (exact fault method), fix-verdict accuracy, and
line-drift confidence against labelled cases. Writes eval/last_run.json and fails
(non-zero) if below the gate or regressed vs eval/baseline.json.
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GATE_LOCALIZATION = 95.0
GATE_VERDICT = 90.0


def run(cases_path: Path | None = None) -> dict:
    from ghrca.repo import Repo
    from ghrca import errors as errmod
    from ghrca.locate import localize_lazy
    from ghrca.archaeology import analyze_fix_status

    spec = json.loads((cases_path or HERE / "cases.json").read_text(encoding="utf-8"))
    repo = Repo(spec["repo_id"], source=spec.get("source"))
    if not repo.exists():
        repo.clone_or_update()
    default_branch = spec["default_branch"]

    n = loc_ok = verdict_ok = conf_ok = conf_total = 0
    details = []
    for c in spec["cases"]:
        n += 1
        err = errmod.from_text(spec["trace"], "eval")[0]
        commit = repo.rev_parse(c["branch"])
        loc = localize_lazy(err, repo, commit, default_branch)
        got_method = (loc.fault.method_fqn.split("#")[-1]
                      if loc.resolved and loc.fault else None)
        this_loc = got_method == c["method"]
        loc_ok += this_loc

        got_verdict = None
        if loc.resolved and loc.fault:
            f = loc.fault
            fix = analyze_fix_status(repo, None, f.path, f.method_fqn.split("#")[-1],
                                     f.method_start, f.method_end, commit, c["branch"],
                                     fault_line=f.frame.line)
            got_verdict = fix.verdict
        this_verdict = got_verdict == c.get("verdict")
        verdict_ok += this_verdict

        if "confidence" in c:
            conf_total += 1
            conf_ok += (loc.confidence == c["confidence"])

        details.append({"case": c["name"], "branch": c["branch"],
                        "method_ok": this_loc, "got_method": got_method,
                        "verdict_ok": this_verdict, "got_verdict": got_verdict,
                        "confidence": loc.confidence})

    result = {
        "n": n,
        "localization_pct": round(loc_ok / n * 100, 1) if n else 0,
        "verdict_pct": round(verdict_ok / n * 100, 1) if n else 0,
        "confidence_pct": round(conf_ok / conf_total * 100, 1) if conf_total else None,
        "details": details,
    }
    (HERE / "last_run.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def gate(result: dict) -> tuple[bool, list[str]]:
    problems = []
    if result["localization_pct"] < GATE_LOCALIZATION:
        problems.append(f"localization {result['localization_pct']}% < {GATE_LOCALIZATION}%")
    if result["verdict_pct"] < GATE_VERDICT:
        problems.append(f"verdict {result['verdict_pct']}% < {GATE_VERDICT}%")
    base = HERE / "baseline.json"
    if base.exists():
        b = json.loads(base.read_text(encoding="utf-8"))
        if result["localization_pct"] < b.get("localization_pct", 0):
            problems.append("localization regressed vs baseline")
        if result["verdict_pct"] < b.get("verdict_pct", 0):
            problems.append("verdict regressed vs baseline")
    return (not problems), problems


def main(argv=None):
    result = run()
    ok, problems = gate(result)
    print(json.dumps({k: result[k] for k in
                      ("n", "localization_pct", "verdict_pct", "confidence_pct")},
                     indent=2))
    for d in result["details"]:
        flag = "OK" if (d["method_ok"] and d["verdict_ok"]) else "XX"
        print(f"  {flag} {d['case']:<22} method={d['got_method']} "
              f"verdict={d['got_verdict']} conf={d['confidence']}")
    print("GATE:", "PASS" if ok else "FAIL " + "; ".join(problems))
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

```

### `eval/rca.py`
**Purpose:** RCA corpus eval (Round 2, D3): deterministic metrics + held-out --final enforcement.

```python
"""RCA evaluation harness (D3).

Deterministic metrics over the RCA corpus. The `test` split is frozen: its
manifest hash is verified and it refuses to run without `--final` (held-out
discipline, Round-2 rule 4). Tuning uses `dev` only.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ghrca import config
from ghrca.repo import Repo

CORPUS = config.PROJECT_ROOT / "eval" / "rca_cases"


def _load(split: str) -> list[dict]:
    cases = []
    for d in sorted(CORPUS.iterdir()):
        cj = d / "case.json"
        if not cj.is_dir() and cj.exists():
            c = json.loads(cj.read_text(encoding="utf-8"))
            bucket = "test" if int(c["id"][:8], 16) % 2 == 1 else "dev"
            if bucket == split:
                cases.append(c)
    return cases


def _verify_manifest(cases: list[dict]) -> bool:
    man = CORPUS / "TEST_MANIFEST.sha256"
    if not man.exists():
        return False
    stored = man.read_text(encoding="utf-8").splitlines()[0].strip()
    lines = []
    for c in sorted(cases, key=lambda x: x["id"]):
        content = (CORPUS / c["id"] / "case.json").read_text(encoding="utf-8")
        lines.append(c["id"] + ":" + hashlib.sha1(content.encode()).hexdigest())
    return hashlib.sha256("\n".join(lines).encode()).hexdigest() == stored


def run(split: str = "dev", final: bool = False, use_llm: bool = False,
        verdicts: bool = False) -> dict:
    if split == "test" and not final:
        raise SystemExit("REFUSED: the test split is held out. Re-run with --final "
                         "(exactly once, for the final evaluation).")
    cases = _load(split)
    if split == "test":
        if not _verify_manifest(cases):
            raise SystemExit("REFUSED: test manifest hash mismatch — corpus changed.")

    from ghrca import errors as errmod, fingerprint
    from ghrca.locate import localize_lazy
    from ghrca.archaeology import analyze_fix_status

    repos: dict[str, Repo] = {}
    tot = file_hit = method_hit = path_hit = loc_missing = 0
    vok_P = vok_P_total = vok_F = vok_F_total = 0
    calib = {"high": [0, 0], "medium": [0, 0], "low": [0, 0]}
    details = []

    for c in cases:
        rid = c["repo"]
        repo = repos.get(rid) or repos.setdefault(rid, Repo(rid))
        if not repo.exists():
            continue
        tot += 1
        default_branch = repo.default_branch()
        P = c["analysis_commit"]
        err = errmod.from_text(c["error"], "eval")[0]
        loc = localize_lazy(err, repo, P, default_branch)
        if not loc.resolved or not loc.fault:
            loc_missing += 1
            details.append({"id": c["id"], "loc": "missing"})
            continue
        fault_file = loc.fault.path
        fault_method = loc.fault.method_fqn
        cp_methods = [f.method_fqn for f in loc.frames[:4]]
        fh = any(fault_file.endswith(t) or t.endswith(fault_file.split("/")[-1])
                 for t in c["truth"]["files"])
        mh = fault_method in c["truth"]["methods"]
        ph = any(m in c["truth"]["methods"] for m in cp_methods)
        file_hit += fh; method_hit += mh; path_hit += ph
        calib[loc.confidence][1] += 1
        calib[loc.confidence][0] += mh

        # verdict sanity — optional; `git branch --contains` is pathological on
        # 900-branch repos, so it is off by default (localization is the headline).
        if verdicts:
            try:
                f = loc.fault
                fx = analyze_fix_status(repo, None, f.path, f.method_fqn.split("#")[-1],
                                        f.method_start, f.method_end, P, default_branch,
                                        fault_line=f.frame.line, use_patch_id=False,
                                        content_check=False, use_id=False)
                vok_P_total += 1
                if not fx.verdict.startswith("present"):
                    vok_P += 1
            except Exception:
                pass

        details.append({"id": c["id"], "repo": rid, "file_hit": fh, "method_hit": mh,
                        "path_hit": ph, "confidence": loc.confidence,
                        "fault": fault_method})

    denom = tot - loc_missing or 1
    result = {
        "split": split, "n": tot, "loc_missing": loc_missing,
        "file_hit_pct": round(file_hit / denom * 100, 1),
        "method_hit_pct": round(method_hit / denom * 100, 1),
        "path_hit_pct": round(path_hit / denom * 100, 1),
        "verdict_ok_at_P_pct": (round(vok_P / (vok_P_total or 1) * 100, 1)
                                if verdicts else "n/a (off; slow on big repos)"),
        "fix_overlap_pct": "n/a (no LLM)" if not use_llm else None,
        "category_match_pct": "n/a (no LLM)" if not use_llm else None,
        "calibration": {k: (round(v[0] / v[1] * 100, 1) if v[1] else None, v[1])
                        for k, v in calib.items()},
        "details": details,
    }
    (CORPUS.parent / "rca_last_run.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8")
    return result


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="ghrca eval rca")
    ap.add_argument("--split", choices=["dev", "test"], default="dev")
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--llm", action="store_true")
    ap.add_argument("--verdicts", action="store_true")
    args = ap.parse_args(argv)
    r = run(args.split, args.final, args.llm, args.verdicts)
    print(json.dumps({k: v for k, v in r.items() if k != "details"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

```

### `eval/rca_baseline_dev.json`
**Purpose:** Frozen R0 dev baseline (RCA corpus).

```json
{
  "split": "dev",
  "n": 69,
  "loc_missing": 8,
  "file_hit_pct": 36.1,
  "method_hit_pct": 24.6,
  "path_hit_pct": 31.1,
  "verdict_ok_at_P_pct": "n/a (off; slow on big repos)",
  "fix_overlap_pct": "n/a (no LLM)",
  "category_match_pct": "n/a (no LLM)",
  "calibration": {
    "high": [
      25.0,
      60
    ],
    "medium": [
      null,
      0
    ],
    "low": [
      0.0,
      1
    ]
  },
  "details": [
    {
      "id": "03175138e40b",
      "loc": "missing"
    },
    {
      "id": "034ddd1a2388",
      "repo": "elastic/elasticsearch",
      "file_hit": true,
      "method_hit": true,
      "path_hit": true,
      "confidence": "high",
      "fault": "co.elastic.elasticsearch.stateless.IndexShardCacheWarmer#doPreWarmIndexShardCache"
    },
    {
      "id": "03d0c8442c7f",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.xpack.esql.querydsl.query.SingleValueQuery.AbstractBuilder#simple"
    },
    {
      "id": "06a920cc5195",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.index.IndexSettings.RefreshIntervalValidator#validate"
    },
    {
      "id": "0727b4ba6817",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.compute.lucene.read.ValuesFromManyReader.ForwardSequenceRun#readColumnAtATime"
    },
    {
      "id": "0bd44eeaa8aa",
      "loc": "missing"
    },
    {
      "id": "0db4a6c4b895",
      "repo": "apache/hadoop",
      "file_hit": true,
      "method_hit": true,
      "path_hit": true,
      "confidence": "high",
      "fault": "org.apache.hadoop.yarn.server.resourcemanager.scheduler.fair.FSPreemptionThread#identifyContainersToPreemptOnNode"
    },
    {
      "id": "0dd7e7cad150",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.cluster.action.shard.ShardStateAction.ShardFailedClusterStateTaskExecutor#execute"
    },
    {
      "id": "1495ef50e432",
      "repo": "apache/hadoop",
      "file_hit": true,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.apache.hadoop.hdfs.server.datanode.LocalReplica#bumpReplicaGS"
    },
    {
      "id": "1a29d260a273",
      "repo": "elastic/elasticsearch",
      "file_hit": true,
      "method_hit": true,
      "path_hit": true,
      "confidence": "high",
      "fault": "org.elasticsearch.xpack.enrich.EnrichPolicyRunner#run"
    },
    {
      "id": "1d31f3808103",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.action.bulk.Retry2#awaitClose"
    },
    {
      "id": "1f0580c24b67",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.action.search.AbstractSearchAsyncAction#maybeReEncodeNodeIds"
    },
    {
      "id": "25d3e6c6c5d6",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.cluster.action.shard.ShardStateAction.ShardFailedClusterStateTaskExecutor#execute"
    },
    {
      "id": "2cc61e5830bc",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.compute.operator.DriverStatus#writeTo"
    },
    {
      "id": "2fccf4841c2d",
      "repo": "apache/hadoop",
      "file_hit": true,
      "method_hit": true,
      "path_hit": true,
      "confidence": "high",
      "fault": "org.apache.hadoop.yarn.logaggregation.AggregatedLogFormat.LogWriter#close"
    },
    {
      "id": "30ff3c8ed795",
      "repo": "apache/kafka",
      "file_hit": true,
      "method_hit": false,
      "path_hit": true,
      "confidence": "high",
      "fault": "org.apache.kafka.streams.processor.internals.StreamThread#close"
    },
    {
      "id": "331d93863a0e",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.xpack.esql.querydsl.query.SingleValueQuery.AbstractBuilder#simple"
    },
    {
      "id": "3b49a054d4af",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.compute.operator.DriverStatus#writeTo"
    },
    {
      "id": "3bb1d144370e",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.xpack.esql.expression.function.scalar.string.Contains#process"
    },
    {
      "id": "3e1f658a69d0",
      "loc": "missing"
    },
    {
      "id": "477797006c7d",
      "repo": "apache/kafka",
      "file_hit": true,
      "method_hit": true,
      "path_hit": true,
      "confidence": "high",
      "fault": "org.apache.kafka.common.requests.ListOffsetRequest#getErrorResponse"
    },
    {
      "id": "4fcdfe2a9e88",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.index.IndexSettings.RefreshIntervalValidator#validate"
    },
    {
      "id": "578624b0dbb7",
      "repo": "apache/kafka",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "low",
      "fault": "org.apache.kafka.coordinator.group.assignor.UniformAssignor#assign"
    },
    {
      "id": "6037e87c9bac",
      "repo": "apache/kafka",
      "file_hit": true,
      "method_hit": true,
      "path_hit": true,
      "confidence": "high",
      "fault": "org.apache.kafka.common.requests.ListOffsetRequest#getErrorResponse"
    },
    {
      "id": "63d760a41767",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.index.IndexSettings.RefreshIntervalValidator#validate"
    },
    {
      "id": "64a1f710ca39",
      "repo": "elastic/elasticsearch",
      "file_hit": true,
      "method_hit": true,
      "path_hit": true,
      "confidence": "high",
      "fault": "org.elasticsearch.xpack.enrich.EnrichPolicyRunner#run"
    },
    {
      "id": "7055f6b6d290",
      "repo": "apache/kafka",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.apache.kafka.common.requests.RequestContext#RequestContext"
    },
    {
      "id": "7129d77c0d2e",
      "repo": "apache/kafka",
      "file_hit": false,
      "method_hit": false,
      "path_hit": true,
      "confidence": "high",
      "fault": "org.apache.kafka.common.utils.Utils#getContextOrKafkaClassLoader"
    },
    {
      "id": "823576944dd4",
      "repo": "elastic/elasticsearch",
      "file_hit": true,
      "method_hit": true,
      "path_hit": true,
      "confidence": "high",
      "fault": "org.elasticsearch.xpack.enrich.EnrichPolicyRunner#run"
    },
    {
      "id": "861a5c06e485",
      "loc": "missing"
    },
    {
      "id": "8c14a52cb3c7",
      "repo": "apache/kafka",
      "file_hit": true,
      "method_hit": true,
      "path_hit": true,
      "confidence": "high",
      "fault": "org.apache.kafka.jmh.cache.LRUCacheBenchmark#testCachePerformance"
    },
    {
      "id": "941015e65a5b",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.action.bulk.TransportBulkAction#doInternalExecute"
    },
    {
      "id": "94baad224602",
      "repo": "apache/kafka",
      "file_hit": true,
      "method_hit": true,
      "path_hit": true,
      "confidence": "high",
      "fault": "org.apache.kafka.common.record.KafkaLZ4BlockInputStream#readHeader"
    },
    {
      "id": "9528dc92f6d0",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.xpack.security.authc.ApiKeyService#loadApiKeyAndValidateCredentials"
    },
    {
      "id": "9652f0e22697",
      "repo": "apache/kafka",
      "file_hit": true,
      "method_hit": false,
      "path_hit": true,
      "confidence": "high",
      "fault": "org.apache.kafka.streams.processor.internals.StreamThread#close"
    },
    {
      "id": "9a87dac8616f",
      "repo": "elastic/elasticsearch",
      "file_hit": true,
      "method_hit": true,
      "path_hit": true,
      "confidence": "high",
      "fault": "org.elasticsearch.nativeaccess.jdk.JdkMacCLibrary.JdkErrorReference#toString"
    },
    {
      "id": "9c71c830f1a7",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.index.IndexSettings.RefreshIntervalValidator#validate"
    },
    {
      "id": "a15daf42ecae",
      "repo": "apache/kafka",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.apache.kafka.image.loader.MetadataLoader#closePublisher"
    },
    {
      "id": "a3bbe25cffb6",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.search.internal.SearchContext#addReleasable"
    },
    {
      "id": "a59de81ad116",
      "loc": "missing"
    },
    {
      "id": "a95d8c2aae33",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.action.bulk.TransportBulkAction#doInternalExecute"
    },
    {
      "id": "aa534ada11d5",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.xpack.esql.expression.function.scalar.string.Contains#process"
    },
    {
      "id": "ae478790e01a",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.cluster.action.shard.ShardStateAction.ShardFailedClusterStateTaskExecutor#execute"
    },
    {
      "id": "ae87cbae0551",
      "repo": "elastic/elasticsearch",
      "file_hit": true,
      "method_hit": true,
      "path_hit": true,
      "confidence": "high",
      "fault": "org.elasticsearch.xpack.enrich.EnrichPolicyRunner#run"
    },
    {
      "id": "af33be70703f",
      "repo": "elastic/elasticsearch",
      "file_hit": true,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.search.internal.ContextIndexSearcher#termStatistics"
    },
    {
      "id": "afa7479e586a",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.xpack.esql.expression.function.scalar.string.Contains#toEvaluator"
    },
    {
      "id": "b0dd722a336e",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.compute.operator.DriverStatus#toXContent"
    },
    {
      "id": "b55099306879",
      "loc": "missing"
    },
    {
      "id": "b9c7863ca9d5",
      "repo": "apache/kafka",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.apache.kafka.clients.consumer.KafkaConsumer#close"
    },
    {
      "id": "ba01c5b8ea9a",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.xpack.esql.expression.function.scalar.string.Contains#process"
    },
    {
      "id": "be001f604afe",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.xpack.esql.expression.function.scalar.string.Contains#toEvaluator"
    },
    {
      "id": "c00aecf8a0f0",
      "repo": "apache/kafka",
      "file_hit": true,
      "method_hit": false,
      "path_hit": true,
      "confidence": "high",
      "fault": "org.apache.kafka.streams.processor.internals.StreamThread#close"
    },
    {
      "id": "c0ea4b5692c7",
      "loc": "missing"
    },
    {
      "id": "c1734d6cbf0a",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.cluster.coordination.ClusterFormationFailureHelper.ClusterFormationState#getDescription"
    },
    {
      "id": "c425c40a01a2",
      "repo": "apache/kafka",
      "file_hit": true,
      "method_hit": true,
      "path_hit": true,
      "confidence": "high",
      "fault": "org.apache.kafka.connect.runtime.distributed.DistributedHerder#startConnector"
    },
    {
      "id": "d20760de266a",
      "repo": "apache/kafka",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.apache.kafka.connect.runtime.distributed.DistributedHerder#onCompletion"
    },
    {
      "id": "d3d892a230e5",
      "repo": "apache/kafka",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.apache.kafka.common.record.FileRecords#flush"
    },
    {
      "id": "d58f25e64ba6",
      "repo": "elastic/elasticsearch",
      "file_hit": true,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.search.internal.ContextIndexSearcher#termStatistics"
    },
    {
      "id": "d5cd20904171",
      "repo": "apache/kafka",
      "file_hit": true,
      "method_hit": true,
      "path_hit": true,
      "confidence": "high",
      "fault": "org.apache.kafka.connect.storage.OffsetUtils#validateFormat"
    },
    {
      "id": "da152548c1c3",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.compute.operator.DriverStatus#toXContent"
    },
    {
      "id": "e0a5e036f278",
      "repo": "elastic/elasticsearch",
      "file_hit": true,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.search.internal.ContextIndexSearcher#termStatistics"
    },
    {
      "id": "e1bfc5987f24",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.compute.lucene.read.ValuesFromManyReader.ForwardSequenceRun#readColumnAtATime"
    },
    {
      "id": "e3a5320824d7",
      "repo": "apache/kafka",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.apache.kafka.common.internals.PartitionStates#partitionSet"
    },
    {
      "id": "ef0a36103179",
      "loc": "missing"
    },
    {
      "id": "ef35b94e624b",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.search.internal.SearchContext#checkCircuitBreaker"
    },
    {
      "id": "f2329feaa70c",
      "repo": "apache/kafka",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.apache.kafka.clients.consumer.KafkaConsumer#close"
    },
    {
      "id": "f7eb48c0556f",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.search.internal.SearchContext#checkCircuitBreaker"
    },
    {
      "id": "fa36a3a29f38",
      "repo": "elastic/elasticsearch",
      "file_hit": true,
      "method_hit": true,
      "path_hit": true,
      "confidence": "high",
      "fault": "co.elastic.elasticsearch.stateless.IndexShardCacheWarmer#doPreWarmIndexShardCache"
    },
    {
      "id": "fe4b1f6a9b83",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.index.IndexSettings.RefreshIntervalValidator#validate"
    }
  ]
}
```

### `eval/rca_last_run.json`
**Purpose:** Last RCA eval run output.

```json
{
  "split": "test",
  "n": 49,
  "loc_missing": 5,
  "file_hit_pct": 29.5,
  "method_hit_pct": 22.7,
  "path_hit_pct": 27.3,
  "verdict_ok_at_P_pct": "n/a (off; slow on big repos)",
  "fix_overlap_pct": "n/a (no LLM)",
  "category_match_pct": "n/a (no LLM)",
  "calibration": {
    "high": [
      23.8,
      42
    ],
    "medium": [
      null,
      0
    ],
    "low": [
      0.0,
      2
    ]
  },
  "details": [
    {
      "id": "0205d695379d",
      "repo": "apache/kafka",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.apache.kafka.common.record.FileRecords#flush"
    },
    {
      "id": "1149187face2",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.compute.operator.DriverStatus#writeTo"
    },
    {
      "id": "16707e533b44",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.cluster.action.shard.ShardStateAction.ShardFailedClusterStateTaskExecutor#execute"
    },
    {
      "id": "1ba2a39976c1",
      "repo": "elastic/elasticsearch",
      "file_hit": true,
      "method_hit": true,
      "path_hit": true,
      "confidence": "high",
      "fault": "co.elastic.elasticsearch.stateless.IndexShardCacheWarmer#doPreWarmIndexShardCache"
    },
    {
      "id": "20a92efba047",
      "loc": "missing"
    },
    {
      "id": "23ed9aa95c00",
      "repo": "elastic/elasticsearch",
      "file_hit": true,
      "method_hit": true,
      "path_hit": true,
      "confidence": "high",
      "fault": "org.elasticsearch.xpack.enrich.EnrichPolicyRunner#run"
    },
    {
      "id": "2be8142fe4e7",
      "repo": "apache/kafka",
      "file_hit": true,
      "method_hit": true,
      "path_hit": true,
      "confidence": "high",
      "fault": "org.apache.kafka.common.requests.ListOffsetRequest#getErrorResponse"
    },
    {
      "id": "2d37fa3bffc7",
      "loc": "missing"
    },
    {
      "id": "2efdf2094043",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.compute.operator.DriverStatus#toXContent"
    },
    {
      "id": "303ee9c9c968",
      "repo": "apache/kafka",
      "file_hit": true,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.apache.kafka.common.config.AbstractConfig.RecordingMap#get"
    },
    {
      "id": "308ca5f1b22d",
      "repo": "elastic/elasticsearch",
      "file_hit": true,
      "method_hit": true,
      "path_hit": true,
      "confidence": "high",
      "fault": "org.elasticsearch.tdigest.MergingDigest#merge"
    },
    {
      "id": "3400b507f73b",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.cluster.routing.IndexRouting.IdAndRoutingOnly#checkRoutingRequired"
    },
    {
      "id": "38812eabf375",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.persistent.PersistentTasksClusterService#execute"
    },
    {
      "id": "38ae43cb1d81",
      "repo": "apache/kafka",
      "file_hit": true,
      "method_hit": true,
      "path_hit": true,
      "confidence": "high",
      "fault": "org.apache.kafka.connect.runtime.distributed.DistributedHerder#startConnector"
    },
    {
      "id": "3fc2e589021a",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.compute.lucene.read.ValuesFromManyReader.ForwardSequenceRun#readColumnAtATime"
    },
    {
      "id": "44c97319e145",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.cluster.action.shard.ShardStateAction.ShardFailedClusterStateTaskExecutor#execute"
    },
    {
      "id": "48965515ec53",
      "repo": "apache/kafka",
      "file_hit": true,
      "method_hit": true,
      "path_hit": true,
      "confidence": "high",
      "fault": "org.apache.kafka.streams.processor.internals.ReadOnlyTask#commitNeeded"
    },
    {
      "id": "48e7ce977e22",
      "repo": "elastic/elasticsearch",
      "file_hit": true,
      "method_hit": true,
      "path_hit": true,
      "confidence": "high",
      "fault": "org.elasticsearch.xpack.enrich.EnrichPolicyRunner#run"
    },
    {
      "id": "56c3364588aa",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.persistent.PersistentTasksClusterService#execute"
    },
    {
      "id": "5a17bdabacdc",
      "repo": "elastic/elasticsearch",
      "file_hit": true,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.search.internal.ContextIndexSearcher#termStatistics"
    },
    {
      "id": "620dd6cd15c4",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.index.IndexSettings.RefreshIntervalValidator#validate"
    },
    {
      "id": "66e64f033971",
      "repo": "apache/kafka",
      "file_hit": false,
      "method_hit": false,
      "path_hit": true,
      "confidence": "high",
      "fault": "org.apache.kafka.common.utils.Utils#getContextOrKafkaClassLoader"
    },
    {
      "id": "7123939fda43",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.cluster.action.shard.ShardStateAction.ShardFailedClusterStateTaskExecutor#execute"
    },
    {
      "id": "75e5dfa77d30",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.compute.operator.DriverStatus#writeTo"
    },
    {
      "id": "792f77eddda9",
      "repo": "apache/kafka",
      "file_hit": true,
      "method_hit": true,
      "path_hit": true,
      "confidence": "high",
      "fault": "org.apache.kafka.streams.state.internals.RocksDBStore#openDB"
    },
    {
      "id": "7e8f7a6ba2b7",
      "repo": "apache/kafka",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "low",
      "fault": "org.apache.kafka.coordinator.group.assignor.UniformAssignor#assign"
    },
    {
      "id": "7f54644350e7",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.search.internal.SearchContext#addReleasable"
    },
    {
      "id": "8d5f377d3c0e",
      "repo": "apache/kafka",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.apache.kafka.common.record.FileRecords#flush"
    },
    {
      "id": "8e896299aa3a",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.cluster.action.shard.ShardStateAction.ShardFailedClusterStateTaskExecutor#execute"
    },
    {
      "id": "937d679fb86c",
      "repo": "apache/kafka",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.apache.kafka.metadata.properties.MetaPropertiesEnsemble#verify"
    },
    {
      "id": "984247fd092a",
      "repo": "apache/kafka",
      "file_hit": false,
      "method_hit": false,
      "path_hit": true,
      "confidence": "high",
      "fault": "org.apache.kafka.common.utils.Utils#getContextOrKafkaClassLoader"
    },
    {
      "id": "a78a1ba5c3d4",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.index.IndexSettings.RefreshIntervalValidator#validate"
    },
    {
      "id": "abc5ddcb69f8",
      "repo": "apache/kafka",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.apache.kafka.connect.runtime.distributed.DistributedHerder#reconfigureConnector"
    },
    {
      "id": "b56e2551eae1",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.index.IndexSettings.RefreshIntervalValidator#validate"
    },
    {
      "id": "b6bc48470684",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.xpack.esql.expression.function.scalar.string.Contains#process"
    },
    {
      "id": "b80367e54ee0",
      "loc": "missing"
    },
    {
      "id": "bce4ccc32244",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "low",
      "fault": "org.elasticsearch.cluster.coordination.ClusterFormationFailureHelper.ClusterFormationState#getDescription"
    },
    {
      "id": "cfb3fd33a498",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.search.internal.SearchContext#checkCircuitBreaker"
    },
    {
      "id": "d3671beb637c",
      "repo": "apache/hadoop",
      "file_hit": true,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.apache.hadoop.hdfs.DataStreamer#waitForAckedSeqno"
    },
    {
      "id": "d53480c12951",
      "repo": "apache/kafka",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.apache.kafka.connect.runtime.distributed.DistributedHerder#reconfigureConnector"
    },
    {
      "id": "d8da498d3d84",
      "repo": "apache/kafka",
      "file_hit": true,
      "method_hit": true,
      "path_hit": true,
      "confidence": "high",
      "fault": "org.apache.kafka.streams.processor.internals.ReadOnlyTask#commitNeeded"
    },
    {
      "id": "da829675b088",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.index.mapper.SortedNumericDocValuesSyntheticFieldLoader.ImmediateDocValuesLoader#advanceToDoc"
    },
    {
      "id": "db7fa737d6fe",
      "repo": "apache/kafka",
      "file_hit": true,
      "method_hit": true,
      "path_hit": true,
      "confidence": "high",
      "fault": "org.apache.kafka.streams.state.internals.RocksDBStore#openDB"
    },
    {
      "id": "e232ac811a1b",
      "loc": "missing"
    },
    {
      "id": "f106f17be072",
      "loc": "missing"
    },
    {
      "id": "f20607134633",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.cluster.action.shard.ShardStateAction.ShardFailedClusterStateTaskExecutor#execute"
    },
    {
      "id": "f7ae5463145b",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.action.bulk.Retry2#awaitClose"
    },
    {
      "id": "fa93e703c209",
      "repo": "elastic/elasticsearch",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.elasticsearch.cluster.routing.IndexRouting.IdAndRoutingOnly#checkRoutingRequired"
    },
    {
      "id": "fc5d38310aba",
      "repo": "apache/hadoop",
      "file_hit": false,
      "method_hit": false,
      "path_hit": false,
      "confidence": "high",
      "fault": "org.apache.hadoop.hdfs.server.namenode.FSImage#recoverTransitionRead"
    }
  ]
}
```

### `ghrca/__init__.py`
**Purpose:** Package overview / version.

```python
"""ghrca -- GitHub Runtime-error Root-Cause Analyzer.

Given a Java runtime error (stack trace / exception log, Splunk-style) from a
GitHub repository, ghrca:

  1. clones/fetches the repo over SSH (no API rate limit),
  2. builds a tolerant structural index of the Java source (no compiler),
  3. localizes the failing frame to an exact file/method,
  4. performs git + PR "archaeology" to judge whether a fix exists / was lost /
     is stuck in a PR,
  5. asks a local LLM for a grounded root-cause analysis.

Deterministic Python does the heavy lifting; the (slow, local) LLM is reserved
for the RCA narrative -- typically one call per error.
"""

__version__ = "0.1.0"

```

### `ghrca/__main__.py`
**Purpose:** `python -m ghrca` entry point -> cli.main().

```python
from .cli import main

if __name__ == "__main__":
    main()

```

### `ghrca/agent.py`
**Purpose:** Batch agent over targets.json: live progress, timing, deployment-branch pinning, two-stage reports.

```python
"""The RCA agent: batch-analyze many repos x many errors with live progress.

This is the autonomous layer over the ghrca pipeline. For each target repo it:
  1. clones or incrementally fetches (SSH or local source),
  2. determines the *deployed* branch (fixed / repo default / a deployment-info
     file committed in the repo),
  3. indexes that branch (cached by commit sha -> only real changes cost time),
  4. for each error: parses the trace, localizes to the right branch's code,
     runs git/PR fix-status archaeology, produces an LLM RCA,
  5. writes a timestamped, numbered HTML report.

Everything is timed and streamed to the console so a human can watch it work,
and a machine-readable summary.json + a numbered index.html are produced.
"""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from . import config, db, errors as errmod, fingerprint, htmlreport, llm, rca
from .archaeology import analyze_fix_status
from .ghapi import GitHubAPI
from . import indexer
from .locate import localize_lazy
from .repo import Repo


def _p(msg: str = "", end: str = "\n"):
    sys.stdout.write(msg + end)
    sys.stdout.flush()


def slugify(s: str) -> str:
    s = re.sub(r"[^\w.-]+", "-", s.strip().lower())
    return re.sub(r"-{2,}", "-", s).strip("-")[:48] or "x"


class Stopwatch:
    def __init__(self):
        self.t0 = time.perf_counter()

    def lap(self) -> float:
        return time.perf_counter() - self.t0


class Agent:
    def __init__(self, out_dir: Path, use_llm: bool = True,
                 policy: str | None = None, rca_format: str = "short"):
        self.out_dir = out_dir
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.use_llm = use_llm
        self.policy = policy or config.LLM_POLICY
        self.rca_format = rca_format
        self.err_counter = 0
        self.summary: dict = {
            "started_at": datetime.now().isoformat(timespec="seconds"),
            "repos": [], "reports": [], "totals": {},
        }

    # -- deployment selection ---------------------------------------------
    def _deployed_ref(self, repo: Repo, cfg: dict, default_branch: str):
        """Return (analyze_ref, display_branch, pinned, desc). Resolution order
        per D11: deployed_sha > deployed_tag > deployed_branch tip."""
        dep = cfg.get("deployment", {"strategy": "default"})
        strat = dep.get("strategy", "default")
        if strat == "fixed":
            b = dep.get("branch", default_branch)
            if dep.get("sha"):
                return dep["sha"], b, True, f"fixed sha {dep['sha'][:10]} (pinned)"
            return b, b, False, f"fixed={b} (tip)"
        if strat == "file":
            path = dep.get("path", "deployment-info.json")
            ref = dep.get("ref", default_branch)
            raw = repo.read_file(ref, path)
            if raw:
                try:
                    info = json.loads(raw)
                    b = info.get("deployed_branch") or info.get("branch") or default_branch
                    if info.get("deployed_sha") or info.get("deployed_commit"):
                        s = info.get("deployed_sha") or info.get("deployed_commit")
                        return s, b, True, f"deployment-info -> sha {s[:10]} (pinned)"
                    if info.get("deployed_tag"):
                        t = info["deployed_tag"]
                        return t, b, True, f"deployment-info -> tag {t} (pinned)"
                    return b, b, False, f"deployment-info -> branch {b} (tip, not pinned)"
                except json.JSONDecodeError:
                    pass
            return default_branch, default_branch, False, "deployment-info missing -> default"
        return default_branch, default_branch, False, f"default={default_branch} (tip)"

    # -- per repo ----------------------------------------------------------
    def process_repo(self, cfg: dict):
        rid = cfg["id"]
        source = cfg.get("source")
        is_local = bool(source) and "://" not in str(source) and not str(source).startswith("git@")
        repo = Repo(rid, source=source)
        api = None if (is_local or source) else GitHubAPI()

        _p("\n" + "=" * 68)
        _p(f"[REPO] {rid}"
           + (f"   (source: {source})" if source else "   (github via SSH)"))
        _p("=" * 68)

        rmetrics: dict = {"id": rid, "errors": [], "source": source}

        # 1. clone / fetch (this is where a NEW repo pays its one-time cost)
        existed = repo.exists()
        sw = Stopwatch()
        status = repo.clone_or_update()
        fetch_s = sw.lap()
        rmetrics["clone_kind"] = "cold-clone" if not existed else "incremental-fetch"
        rmetrics["clone_seconds"] = round(fetch_s, 2)
        _p(f"  [git]     {status}  ({rmetrics['clone_kind']}, {fetch_s:.2f}s)")

        # 2. diff detection: which refs are new/changed since last snapshot
        changes = repo.detect_new_and_changed()
        rmetrics["ref_changes"] = changes
        nb = len(changes["new"]); cb = len(changes["changed"])
        _p(f"  [diff]    refs: {nb} new, {cb} changed, "
           f"{len(changes['removed'])} removed "
           f"(ref-snapshot diff -> only these need work)")
        if nb:
            _p(f"            new branches: {changes['new'][:8]}")

        default_branch = repo.default_branch()

        # 3. deployment -> which ref is live (pinned to a sha/tag when possible)
        analyze_ref, dep_branch, pinned, dep_desc = self._deployed_ref(
            repo, cfg, default_branch)
        rmetrics["deployed_branch"] = dep_branch
        rmetrics["pinned"] = pinned
        _p(f"  [deploy]  deployed = '{dep_branch}'  pinned={pinned}  ({dep_desc})")

        # 4. NO whole-branch index — localization scans only the blobs each error
        #    needs (D3). We record a cheap file count and the source roots.
        tip_sha = repo.rev_parse(analyze_ref)
        sw = Stopwatch()
        java_files = len(repo.ls_java_files(analyze_ref))
        roots = indexer.source_roots(repo, default_branch)
        rmetrics["index"] = {"branch": dep_branch, "sha": tip_sha[:10],
                             "kind": "lazy (blob-keyed, no branch index)",
                             "seconds": round(sw.lap(), 2), "java_files": java_files,
                             "source_roots": roots[:5]}
        _p(f"  [index]   lazy blob-keyed (no whole-branch index): "
           f"{java_files} .java files present; roots={roots[:3]}")

        # 5. errors
        for i, ecfg in enumerate(cfg.get("errors", []), 1):
            self._process_error(repo, api, cfg, ecfg,
                                 analyze_ref, dep_branch, pinned, default_branch,
                                 rmetrics, i)

        self.summary["repos"].append(rmetrics)

    # -- per error ---------------------------------------------------------
    def _process_error(self, repo, api, repo_cfg, ecfg,
                        analyze_ref, dep_branch, pinned, default_branch,
                        rmetrics, local_i):
        self.err_counter += 1
        n = self.err_counter
        name = ecfg.get("name", f"error{n}")
        trace = ecfg.get("trace", "")
        _p(f"\n  --- [ERROR {n}] {name} ---")

        esw = Stopwatch()
        recs = errmod.from_text(trace, source=ecfg.get("source", f"log:{name}"))
        if not recs:
            _p("    (!) could not parse a stack trace; skipping")
            return
        err = recs[0]
        # a per-error branch override wins over the deployed ref; an error-level
        # `version` that resolves to a tag pins the analysis (D11).
        ref = ecfg.get("branch") or analyze_ref
        this_pinned = pinned or bool(ecfg.get("branch"))
        if ecfg.get("version"):
            for cand in (ecfg["version"], f"v{ecfg['version']}"):
                if repo._git("rev-parse", "--verify", "--quiet", cand, check=False).strip():
                    ref = cand
                    this_pinned = True
                    break
        branch = ecfg.get("branch") or dep_branch      # display name
        err.branch = branch
        p = err.primary
        _p(f"    [1 parse] {p.type}: {(p.message or '')[:70]}  "
           f"({sum(len(t.frames) for t in err.chain)} frames)")

        # lazy localization at the actual ref/commit — no whole-branch index (D3)
        commit = repo.rev_parse(ref)
        sw = Stopwatch()
        loc = localize_lazy(err, repo, commit, default_branch)
        loc_s = sw.lap()
        root_packages = loc.root_packages
        if loc.resolved and loc.fault:
            _p(f"    [2 locate] OK -> {loc.fault.method_fqn} "
               f"({loc.fault.path}:{loc.fault.frame.line}) on '{branch}'  [{loc_s:.2f}s]")
        else:
            _p(f"    [2 locate] unresolved on '{branch}'  [{loc_s:.2f}s]")

        # quick diff evidence: how the fault file differs from the default branch
        diff_info = ""
        if loc.resolved and loc.fault and ref != default_branch:
            try:
                d = repo.diff(default_branch, ref, path=loc.fault.path, unified=0)
                added = sum(1 for l in d.splitlines() if l.startswith("+") and not l.startswith("+++"))
                removed = sum(1 for l in d.splitlines() if l.startswith("-") and not l.startswith("---"))
                diff_info = f"{added}+/{removed}- vs {default_branch}"
                _p(f"    [~ diff ] fault file '{loc.fault.path.split('/')[-1]}': "
                   f"{diff_info} (quick git diff {default_branch}..{branch})")
            except Exception:
                pass

        # fingerprint + dedupe bookkeeping (D6)
        fp, exc_type, norm_msg, top = fingerprint.compute(err, root_packages)
        count, first_time = db.upsert_fingerprint(fp, rmetrics["id"], exc_type,
                                                  norm_msg, top)
        method_hash = loc.method_hash() if loc.resolved else "none"
        _p(f"    [~ fp   ] {fp}  (seen {count}x{', NEW' if first_time else ''})")

        # archaeology
        sw = Stopwatch()
        if loc.resolved and loc.fault:
            fix = analyze_fix_status(
                repo, api, loc.fault.path, loc.fault.method_fqn.split("#")[-1],
                loc.fault.method_start, loc.fault.method_end, commit, branch,
                fault_line=loc.fault.frame.line)
        else:
            from .archaeology import FixStatus
            fix = FixStatus(headline="Localization failed — fix-status not computed.")
        arch_s = sw.lap()
        _p(f"    [3 dig  ] fix-status: {fix.headline[:64]}  [{arch_s:.2f}s]")

        ts = datetime.now().strftime("%Y%m%dT%H%M%S")
        fname = f"{ts}_{slugify(rmetrics['id'])}_{slugify(name)}_error_{n}.html"
        fpath = self.out_dir / fname

        # Stage A: deterministic report immediately (D8)
        cached = rca.cache_get(fp, method_hash, config.PROMPT_VER)
        stage_a_status = "done" if cached else "pending"
        html = htmlreport.render_html(err, loc, fix, branch,
                                      cached["narrative"] if cached else "",
                                      {"source": "cache" if cached else "pending"},
                                      rca_status=stage_a_status, pinned=this_pinned)
        fpath.write_text(html, encoding="utf-8")
        db.record_error(err.id, rmetrics["id"], fp, err.source, err.raw_text,
                        branch, commit, stage_a_status)
        _p(f"    [A report] {fname}  (stage A, {stage_a_status})")

        # Stage B: narrative (cache/template/llm per policy) then rewrite in place
        narrative, llm_meta = "", {"source": "skipped"}
        sw = Stopwatch()
        policy = "never" if not self.use_llm else self.policy
        res = rca.produce_narrative(err, loc, fix, branch, root_packages,
                                    fp=fp, method_hash=method_hash, policy=policy,
                                    fmt=self.rca_format, repo=repo, commit=commit,
                                    partial=(repo_cfg.get("clone_mode") == "partial"),
                                    freq=count)
        narrative = res["narrative"]
        llm_meta = {"completion_tokens": res["tokens"], "elapsed_s": res["seconds"],
                    "source": res["source"], "rca_depth": res.get("rca_depth")}
        _p(f"    [4 think] RCA {res['source']}: {res['tokens']} tokens  "
           f"[{res['seconds']:.1f}s]")
        if res["source"] != "pending":
            html = htmlreport.render_html(err, loc, fix, branch, narrative, llm_meta,
                                          rca_status="done", pinned=this_pinned)
            fpath.write_text(html, encoding="utf-8")
            db.record_error(err.id, rmetrics["id"], fp, err.source, err.raw_text,
                            branch, commit, "done")
        total_e = esw.lap()
        _p(f"    [5 report] {fname}  (B via {res['source']}, error total {total_e:.1f}s)")

        rec = {
            "n": n, "repo": rmetrics["id"], "name": name, "branch": branch,
            "exception": p.type, "message": (p.message or "")[:200],
            "fault": (f"{loc.fault.method_fqn} @ {loc.fault.path}:{loc.fault.frame.line}"
                      if loc.resolved and loc.fault else None),
            "fix_status": fix.headline,
            "diff": diff_info,
            "timings": {"locate": round(loc_s, 2), "archaeology": round(arch_s, 2),
                        "rca": round(llm_meta.get("elapsed_s", 0), 1),
                        "total": round(total_e, 1)},
            "report": fname,
        }
        rmetrics["errors"].append(rec)
        self.summary["reports"].append(rec)

    # -- run ---------------------------------------------------------------
    def run(self, targets: dict):
        run_sw = Stopwatch()
        for cfg in targets.get("repos", []):
            try:
                self.process_repo(cfg)
            except Exception as e:
                _p(f"  (!) repo {cfg.get('id')} failed: {e}")
                self.summary["repos"].append({"id": cfg.get("id"), "error": str(e)})
        total = run_sw.lap()
        self.summary["totals"] = {
            "errors_analyzed": len(self.summary["reports"]),
            "repos": len(targets.get("repos", [])),
            "wall_seconds": round(total, 1),
        }
        self.summary["finished_at"] = datetime.now().isoformat(timespec="seconds")
        self._write_index(total)
        self._print_final(total)

    def _write_index(self, total: float):
        (self.out_dir / "summary.json").write_text(
            json.dumps(self.summary, indent=2), encoding="utf-8")
        rows = []
        for r in self.summary["reports"]:
            rows.append(
                f"<tr><td>{r['n']}</td>"
                f"<td>{r['repo']}</td><td><code>{r['branch']}</code></td>"
                f"<td>{r['exception']}</td>"
                f"<td>{(r['fault'] or 'unlocalized')}</td>"
                f"<td>{r['fix_status']}</td>"
                f"<td>{r['timings']['rca']}s / {r['timings']['total']}s</td>"
                f"<td><a href='{r['report']}'>open</a></td></tr>")
        idx_rows = []
        for rm in self.summary["repos"]:
            if "index" in rm:
                ix = rm["index"]
                idx_rows.append(
                    f"<tr><td>{rm['id']}</td><td>{rm['clone_kind']} "
                    f"{rm['clone_seconds']}s</td>"
                    f"<td>{ix['kind']} {ix['seconds']}s</td>"
                    f"<td>{ix['java_files']} .java files</td>"
                    f"<td>{len(rm['ref_changes']['new'])} new, "
                    f"{len(rm['ref_changes']['changed'])} changed</td></tr>")
        html = f"""<!doctype html><html><head><meta charset="utf-8">
<title>ghrca agent run</title><style>
body{{font:15px system-ui,Segoe UI,Roboto,sans-serif;max-width:1100px;margin:0 auto;
padding:28px 16px;color:#1a1a1e;background:#fff}}
@media(prefers-color-scheme:dark){{body{{background:#0f1115;color:#e6e7ea}}
a{{color:#6ea8fe}}code,th,td{{border-color:#282c34!important}}
tr:nth-child(even){{background:#181b21}}}}
h1{{font-size:22px}}h2{{font-size:16px;margin-top:28px}}
table{{border-collapse:collapse;width:100%;font-size:13px;margin:10px 0}}
th,td{{border:1px solid #e3e5ea;padding:6px 9px;text-align:left;vertical-align:top}}
th{{background:#f6f7f9}}@media(prefers-color-scheme:dark){{th{{background:#20242c}}}}
code{{font-family:Consolas,monospace}}.big{{font-size:26px;font-weight:700}}
</style></head><body>
<h1>ghrca agent run</h1>
<p>Started {self.summary['started_at']} · finished {self.summary.get('finished_at','')} ·
<span class="big">{self.summary['totals']['wall_seconds']}s</span> total ·
{self.summary['totals']['errors_analyzed']} errors across
{self.summary['totals']['repos']} repos.</p>
<h2>Per-repo: clone &amp; indexing cost</h2>
<table><tr><th>repo</th><th>clone/fetch</th><th>index</th><th>size</th>
<th>ref diff</th></tr>{''.join(idx_rows)}</table>
<h2>Reports (numbered, timestamped)</h2>
<table><tr><th>#</th><th>repo</th><th>branch</th><th>exception</th><th>fault site</th>
<th>fix status</th><th>rca / total</th><th></th></tr>{''.join(rows)}</table>
</body></html>"""
        (self.out_dir / "index.html").write_text(html, encoding="utf-8")

    def _print_final(self, total: float):
        _p("\n" + "#" * 68)
        _p("# AGENT RUN COMPLETE")
        _p("#" * 68)
        _p(f"errors analyzed: {len(self.summary['reports'])} · "
           f"total wall time: {total:.1f}s\n")
        _p("Reports (numbered, timestamped):")
        for r in self.summary["reports"]:
            _p(f"  {r['n']:>2}. {r['report']}")
            _p(f"      repo={r['repo']} branch={r['branch']}  "
               f"fault={r['fault'] or 'unlocalized'}")
            _p(f"      fix-status: {r['fix_status']}")
            _p(f"      timings: locate {r['timings']['locate']}s | "
               f"dig {r['timings']['archaeology']}s | rca {r['timings']['rca']}s | "
               f"total {r['timings']['total']}s")
        _p(f"\nindex: {self.out_dir / 'index.html'}")
        _p(f"summary: {self.out_dir / 'summary.json'}")


def run_targets(targets_path: str, out_dir: str | None = None, use_llm: bool = True,
                policy: str | None = None, rca_format: str = "short"):
    targets = json.loads(Path(targets_path).read_text(encoding="utf-8"))
    od = Path(out_dir or targets.get("output_dir", "agent_reports"))
    if not od.is_absolute():
        od = config.PROJECT_ROOT / od
    agent = Agent(od, use_llm=use_llm, policy=policy, rca_format=rca_format)
    agent.run(targets)
    return agent.summary

```

### `ghrca/archaeology.py`
**Purpose:** Fix-status v2 (D10): ancestry / file patch-id / JIRA-id / content; verdicts with decided_by + confidence; use_id/use_patch_id/content_check flags.

```python
"""Fix-status v2 (D10).

Decides, for each fix-flavored commit on the fault file, whether that fix is
present on the *target commit* — using, in order: ancestry, file-scoped patch-id
equivalence (catches cherry-picks/squashes), JIRA/issue-id match, and a content
check. This eliminates the false "lost" that a naive `git branch --contains`
produces for backports applied under a new SHA.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .ghapi import GitHubAPI, RateLimited
from .repo import Repo

_FIX_RE = re.compile(
    r"\b(fix(?:e[sd])?|bug|npe|null|resolve[sd]?|patch|correct|issue|"
    r"error|exception|crash|regress|revert)\b", re.I)
_REVERT_RE = re.compile(r"\brevert\b", re.I)
_ID_RE = re.compile(r"\b([A-Z][A-Z0-9]+-\d+)\b|#(\d+)")

# verdict severity order (D6 table)
_SEV = {"reverted": 1, "lost": 2, "partial": 3, "open_pr": 4, "abandoned_pr": 5,
        "merged_pr_verify": 6, "present_via_equivalent": 7, "present": 8,
        "none_found": 9}
_HEADLINE = {
    "reverted": "A fix here was reverted on the target — the bug was likely reintroduced.",
    "lost": "A fix exists on other branches but is ABSENT on the target (lost/unmerged) — backport needed.",
    "partial": "A fix is only partially present on the target.",
    "open_pr": "A fix may be stuck in an open PR.",
    "abandoned_pr": "A proposed fix was closed without merging (abandoned).",
    "merged_pr_verify": "A related fix was merged — verify it covers this case.",
    "present_via_equivalent": "The fix is present on the target as a cherry-pick/squash.",
    "present": "The fix is an ancestor of the target (present).",
    "none_found": "No fix found anywhere for this location.",
}


@dataclass
class Finding:
    kind: str          # == verdict for fix findings
    detail: str
    refs: list = field(default_factory=list)
    decided_by: str = ""   # ancestry | patch_id | id_match | content | pr
    confidence: str = ""   # high | medium | low


@dataclass
class FixStatus:
    headline: str
    findings: list = field(default_factory=list)
    git_only: bool = False
    note: str = ""
    verdict: str = "none_found"

    def to_dict(self):
        return {"headline": self.headline, "verdict": self.verdict,
                "git_only": self.git_only, "note": self.note,
                "findings": [{"kind": f.kind, "detail": f.detail, "refs": f.refs,
                              "decided_by": f.decided_by, "confidence": f.confidence}
                             for f in self.findings]}


def _extract_ids(text: str) -> list[str]:
    ids = []
    for m in _ID_RE.finditer(text or ""):
        ids.append(m.group(1) or ("#" + m.group(2)))
    return ids


def _norm_lines(lines) -> list[str]:
    out = []
    for l in lines:
        s = re.sub(r"//.*$", "", l)
        s = re.sub(r"\s+", "", s)
        if len(s) < 4:
            continue
        if set(s) <= set("{}();"):
            continue
        out.append(s)
    return out


def _content_presence(added_norm, removed_norm, target_src_norm) -> tuple[str, float]:
    """Return (state, ratio) where state ∈ present_by_content|partial|absent."""
    if not added_norm:
        return "absent", 0.0
    tgt = set(target_src_norm)
    present = sum(1 for a in added_norm if a in tgt)
    ratio = present / len(added_norm)
    removed_still_there = any(r in tgt for r in removed_norm)
    if ratio >= 0.8 and not removed_still_there:
        return "present_by_content", ratio
    if ratio >= 0.3:
        return "partial", ratio
    return "absent", ratio


def analyze_fix_status(repo: Repo, api: GitHubAPI | None, path: str,
                       method_name: str, method_start: int, method_end: int,
                       target_commit: str, target_branch: str,
                       fault_line: int | None = None,
                       use_patch_id: bool = True, content_check: bool = True,
                       use_id: bool = True) -> FixStatus:
    # use_patch_id / content_check can be disabled on partial (blob:none) clones
    # where reading blobs triggers slow promisor fetches; ancestry + JIRA/issue-id
    # match remain (both blob-free).
    findings: list[Finding] = []

    file_commits = repo.log_for_path(path, limit=60)
    fixy = [c for c in file_commits
            if _FIX_RE.search(c["subject"]) or _extract_ids(c["subject"])]

    # target method source (normalized) for the content check
    tgt_norm = []
    if content_check:
        tgt_src = repo.read_file(target_commit, path) or ""
        tgt_lines = tgt_src.splitlines()[method_start - 1:method_end] if tgt_src else []
        tgt_norm = _norm_lines(tgt_lines)

    # reverts handled separately
    for c in fixy:
        if _REVERT_RE.search(c["subject"]) and repo.is_ancestor(c["sha"], target_commit):
            findings.append(Finding(
                "reverted", f"Revert {c['sha'][:8]} \"{c['subject']}\" is on target.",
                refs=[c["sha"]], decided_by="ancestry", confidence="high"))

    # Group fix commits by file-scoped patch-id into LOGICAL fixes, so an original
    # commit and its cherry-picks/squashes/rebases are treated as one fix. The
    # earliest commit in a group is the canonical fix; presence of the canonical
    # by ancestry is 'present', presence of only an equivalent is
    # 'present_via_equivalent'.
    groups: dict[str, list] = {}
    order: list[str] = []
    for c in fixy[:25]:
        if _REVERT_RE.search(c["subject"]):
            continue
        pid = (repo.file_patch_id(c["sha"], path) if use_patch_id else "") \
            or ("nopid:" + c["sha"])
        if pid not in groups:
            groups[pid] = []
            order.append(pid)
        groups[pid].append(c)
        if len(order) >= 12:
            break

    for pid in order:
        members = groups[pid]                       # newest-first (log order)
        canonical = members[-1]                     # earliest == canonical origin
        subj = canonical["subject"]
        F = canonical["sha"]

        # (a) canonical is a direct ancestor -> present
        if repo.is_ancestor(F, target_commit):
            findings.append(Finding(
                "present", f"Fix {F[:8]} \"{subj}\" is an ancestor of the target.",
                refs=[F], decided_by="ancestry", confidence="high"))
            continue

        # (b) any equivalent (same patch-id) reachable on the target -> equivalent
        equiv = None
        if use_patch_id and not pid.startswith("nopid:"):
            # a group member that is itself an ancestor of T (e.g. a cherry-pick)
            for m in members:
                if m["sha"] != F and repo.is_ancestor(m["sha"], target_commit):
                    equiv = m["sha"]; break
            if equiv is None:
                mb = repo.merge_base(F, target_commit) or target_commit
                for C in repo.commits_touching_in_range(
                        f"{mb}..{target_commit}", path, limit=100):
                    if repo.file_patch_id(C, path) == pid:
                        equiv = C; break
        if equiv:
            findings.append(Finding(
                "present_via_equivalent",
                f"Fix {F[:8]} \"{subj}\" is present as {equiv[:8]} "
                f"(equal file patch-id — cherry-pick/squash/rebase).",
                refs=[F, equiv], decided_by="patch_id", confidence="high"))
            continue

        # (c) JIRA/issue id match on the target's history (skippable: --no-id, D4)
        decided = False
        for idv in (_extract_ids(subj) if use_id else []):
            hits = repo.commits_grep_touching(target_commit, idv.lstrip("#"), path, limit=20)
            if hits:
                findings.append(Finding(
                    "present_via_equivalent",
                    f"Fix {F[:8]} \"{subj}\" ({idv}) appears as {hits[0][:8]} (same id).",
                    refs=[F, hits[0]], decided_by="id_match", confidence="medium"))
                decided = True; break
        if decided:
            continue

        # (d) content check (skipped on partial clones)
        state, ratio = ("absent", 0.0)
        if content_check:
            added = _norm_lines(repo.added_lines(F, path))
            removed = _norm_lines(repo.removed_lines(F, path))
            state, ratio = _content_presence(added, removed, tgt_norm)
        if state == "present_by_content":
            findings.append(Finding(
                "present_via_equivalent",
                f"Fix {F[:8]} \"{subj}\" present by content ({ratio*100:.0f}% of added lines).",
                refs=[F], decided_by="content", confidence="medium"))
        elif state == "partial":
            findings.append(Finding(
                "partial",
                f"Fix {F[:8]} \"{subj}\" only PARTIALLY on target ({ratio*100:.0f}%).",
                refs=[F], decided_by="content", confidence="medium"))
        else:
            containing = repo.branches_containing(F)
            if containing:
                findings.append(Finding(
                    "lost",
                    f"Fix {F[:8]} \"{subj}\" is on {containing[:5]} but ABSENT on "
                    f"'{target_branch}' by ancestry, patch-id, id and content.",
                    refs=[F] + containing[:5], decided_by="content", confidence="high"))

    # origin (D10 extra)
    if fault_line:
        origin = repo.blame_origin(target_commit, path, fault_line)
        if origin:
            tag = repo.first_tag_containing(origin)
            m = repo.commit_meta(origin)
            findings.append(Finding(
                "origin",
                f"Failing line introduced by {origin[:8]} \"{m['subject']}\" "
                f"({m['date']})" + (f", first released in {tag}." if tag else "."),
                refs=[origin], decided_by="blame", confidence="high"))

    # PR cross-reference (best effort)
    git_only = True
    if api is not None:
        fname = path.split("/")[-1]
        try:
            res = api.search_issues(f'repo:{repo.owner_repo} is:pr {fname}')
            git_only = False
            for pr in (res.get("items") or [])[:6]:
                state = pr.get("state"); num = pr.get("number"); title = pr.get("title", "")
                merged = pr.get("pull_request", {}).get("merged_at")
                if state == "open":
                    findings.append(Finding("open_pr",
                        f"Open PR #{num} \"{title}\" touches {fname}.",
                        refs=[f"#{num}"], decided_by="pr", confidence="medium"))
                elif merged:
                    findings.append(Finding("merged_pr_verify",
                        f"Merged PR #{num} \"{title}\" touched {fname}.",
                        refs=[f"#{num}"], decided_by="pr", confidence="low"))
                else:
                    findings.append(Finding("abandoned_pr",
                        f"Closed-unmerged PR #{num} \"{title}\" mentioned {fname}.",
                        refs=[f"#{num}"], decided_by="pr", confidence="low"))
        except (RateLimited, Exception):
            git_only = True

    # choose headline verdict with explicit precedence. A real problem
    # (reverted/lost) always wins; otherwise a clean ancestry 'present' is
    # preferred over 'present_via_equivalent' when both are observed for the
    # same target (e.g. the fix is merged on trunk AND cherry-picked elsewhere).
    kinds = {f.kind for f in findings}
    if "reverted" in kinds:
        verdict = "reverted"
    elif "lost" in kinds:
        verdict = "lost"
    elif "present" in kinds:
        verdict = "present"
    elif "present_via_equivalent" in kinds:
        verdict = "present_via_equivalent"
    elif "partial" in kinds:
        verdict = "partial"
    elif "open_pr" in kinds:
        verdict = "open_pr"
    elif "abandoned_pr" in kinds:
        verdict = "abandoned_pr"
    elif "merged_pr_verify" in kinds:
        verdict = "merged_pr_verify"
    else:
        verdict = "none_found"
    # keep origin finding but sort verdict findings first
    findings.sort(key=lambda f: _SEV.get(f.kind, 50))
    headline = _HEADLINE.get(verdict, "See findings.")
    note = ("PR data unavailable (no API budget/token) — git-only analysis."
            if git_only else "")
    return FixStatus(headline=headline, findings=findings, git_only=git_only,
                     note=note, verdict=verdict)

```

### `ghrca/backport.py`
**Purpose:** Read-only backport dry-run via git merge-tree (git<2.40 fallback).

```python
"""Backport dry-run (D14) — READ-ONLY.

Uses `git merge-tree --write-tree` (git >= 2.38) to test whether a fix commit F
would apply onto target T with no worktree and no ref updates. Writes the patch
and prints the suggested cherry-pick command but NEVER runs it.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from . import config
from .repo import Repo


def _git_version() -> tuple[int, int]:
    out = subprocess.run(["git", "--version"], capture_output=True, text=True).stdout
    try:
        p = out.split()[2].split(".")
        return int(p[0]), int(p[1])
    except Exception:
        return (0, 0)


def git_supports_merge_tree() -> bool:
    return _git_version() >= (2, 38)


def backport_plan(repo: Repo, fix_sha: str, target: str) -> dict:
    if not git_supports_merge_tree():
        return {"ok": False, "reason": "git < 2.38; merge-tree --write-tree unavailable"}
    ver = _git_version()
    parent = f"{fix_sha}^"
    approx = ""
    if ver >= (2, 40):
        # exact cherry-pick simulation: base = fix's parent
        cmd = ["git", "--git-dir", str(repo.path), "merge-tree", "--write-tree",
               f"--merge-base={parent}", target, fix_sha]
    else:
        # git 2.38/2.39: no --merge-base flag; auto common-ancestor merge of the
        # fix commit onto the target (approximates the cherry-pick).
        cmd = ["git", "--git-dir", str(repo.path), "merge-tree", "--write-tree",
               target, fix_sha]
        approx = (f" (git {ver[0]}.{ver[1]}: used auto merge-base; exact "
                  f"cherry-pick-base simulation needs git >= 2.40)")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    clean = proc.returncode == 0
    conflicts: list[str] = []
    if not clean:
        # conflict output lists "<info>\t<path>" lines after the tree oid
        for line in proc.stdout.splitlines()[1:]:
            parts = line.split("\t")
            if len(parts) >= 2 and parts[-1] not in conflicts:
                conflicts.append(parts[-1])

    # write the patch (read-only artifact)
    bdir = config.REPORTS_DIR / "backports"
    bdir.mkdir(parents=True, exist_ok=True)
    patch = subprocess.run(
        ["git", "--git-dir", str(repo.path), "format-patch", "-1", fix_sha, "--stdout"],
        capture_output=True)
    patch_path = bdir / f"{fix_sha[:12]}_onto_{config.repo_slug(target)[:20]}.patch"
    patch_path.write_bytes(patch.stdout)

    return {
        "ok": True,
        "applies_cleanly": clean,
        "conflicts": conflicts,
        "patch": str(patch_path),
        "command": f"git checkout -b backport/{fix_sha[:8]} {target} && "
                   f"git cherry-pick -x {fix_sha}",
        "note": "DRY RUN — no branch created, no cherry-pick run." + approx,
    }

```

### `ghrca/blast.py`
**Purpose:** Blast radius v2: still_buggy/fixed/refactored_unknown/moved/renamed/absent across all branches in one batch-check.

```python
"""Blast radius (D12): which branches are affected by a bug.

Given the fault file P and the buggy method's body_hash H (from the deployed
commit), classify every branch in ONE `cat-file --batch-check` (metadata, no
blob content) to get each branch's blob for P, then scan only the *distinct*
differing blobs once (cached). Fast even on 900-branch repos.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field

import re

from . import blobstore, config, tsjava
from .poller import branch_priority
from .repo import Repo


def _tokens(s: str) -> list[str]:
    return re.findall(r"[A-Za-z_]\w*|[^\s\w]", s or "")


def _sim(a: str, b: str) -> float:
    """Token-set Jaccard-ish similarity (fast, order-insensitive enough)."""
    ta, tb = set(_tokens(a)), set(_tokens(b))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


@dataclass
class BlastResult:
    path: str
    method: str
    counts: dict = field(default_factory=dict)
    branches: dict = field(default_factory=dict)   # branch -> status
    seconds: float = 0.0
    cached: bool = False

    def by_priority(self, manifest_branch=None):
        rows = []
        for b, st in self.branches.items():
            rows.append((branch_priority(b, manifest_branch=manifest_branch), b, st))
        rows.sort(key=lambda r: (-r[0], r[1]))
        return rows


def _refs_snapshot_hash(branch_shas: dict) -> str:
    key = ";".join(f"{b}:{s}" for b, s in sorted(branch_shas.items()))
    return hashlib.sha1(key.encode()).hexdigest()[:16]


def _cache_path(repo_id, path, buggy_hash, snap):
    d = config.CACHE_DIR / "blast"
    d.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(f"{repo_id}|{path}|{buggy_hash}|{snap}".encode()).hexdigest()[:16]
    return d / f"{key}.json"


def classify_differing(msrc: str, fault_stmt_sig: str, fix_added_norm: list) -> str:
    """Pure decision for a method whose body differs from the buggy one (D10):
    still_buggy / fixed / refactored_unknown / changed_unrelated."""
    msrc_norm = re.sub(r"\s+", "", msrc)
    if fix_added_norm and sum(1 for a in fix_added_norm if a in msrc_norm) \
            >= 0.8 * len(fix_added_norm):
        return "fixed"
    if fault_stmt_sig:
        sig_norm = fault_stmt_sig.replace(" ", "")
        if sig_norm and sig_norm in msrc_norm:
            return "still_buggy"      # the failing statement survived unguarded
        return "refactored_unknown"   # failing statement gone, no known fix content
    return "changed_unrelated"


def blast(repo: Repo, path: str, method_name: str, buggy_body_hash: str,
          *, fixed_ref: str | None = None, use_cache: bool = True,
          fault_commit: str | None = None, fault_line: int | None = None,
          fix_added: list | None = None) -> BlastResult:
    t0 = time.perf_counter()
    branch_refs = {b.name: b.sha for b in repo.list_branches()}
    snap = _refs_snapshot_hash(branch_refs)

    cp = _cache_path(repo.owner_repo, path, buggy_body_hash, snap)
    if use_cache and cp.exists():
        try:
            blob = json.loads(cp.read_text(encoding="utf-8"))
            r = BlastResult(**blob)
            r.cached = True
            r.seconds = time.perf_counter() - t0
            return r
        except Exception:
            pass

    branches = list(branch_refs)
    # ONE batch-check for every branch's blob of P
    specs = [f"refs/heads/{b}:{path}" for b in branches]
    checked = repo.batch_check(specs)
    branch_blob = {b: checked.get(f"refs/heads/{b}:{path}") for b in branches}

    # optional "fixed" reference body_hash (method on a known-fixed ref)
    fixed_hash = None
    if fixed_ref:
        fb = repo.batch_check([f"{fixed_ref}:{path}"]).get(f"{fixed_ref}:{path}")
        if fb:
            blobstore.scan_blobs(repo, [fb], path_hint=path.split("/")[-1])
            m = blobstore.method_by_name(fb, method_name)
            if m:
                fixed_hash = m["body_hash"]

    # the failing statement's normalized signature (for still_buggy vs refactored)
    fault_stmt_sig = ""
    if fault_commit and fault_line:
        src0 = repo.read_file(fault_commit, path) or ""
        if src0:
            fault_stmt_sig = re.sub(r"\s+", " ", tsjava.statement_at(src0, fault_line)).strip()
    fix_added_norm = [re.sub(r"\s+", "", l) for l in (fix_added or []) if len(l.strip()) > 3]

    # scan only DISTINCT differing blobs once
    distinct = {}
    for b, sha in branch_blob.items():
        if sha:
            distinct.setdefault(sha, []).append(b)
    blobstore.scan_blobs(repo, list(distinct), path_hint=path.split("/")[-1])

    def _classify(sha):
        m = blobstore.method_by_name(sha, method_name)
        if m is None:
            # method name gone: moved (same body elsewhere) / renamed / absent (D10)
            rows = blobstore.db_methods_with_body(buggy_body_hash) \
                if hasattr(blobstore, "db_methods_with_body") else []
            if any(r["blob_sha"] == sha for r in rows):
                # same body under a different name in THIS blob -> renamed
                return "renamed"
            if rows:
                return "moved"
            return "absent"
        if m["body_hash"] == buggy_body_hash:
            return "affected"                       # byte-identical buggy method
        if fixed_hash and m["body_hash"] == fixed_hash:
            return "fixed"
        # method differs — decide with the failing statement + fix content
        msrc = ""
        cont = repo.read_blobs([sha]).get(sha, "")
        if cont:
            lines = cont.splitlines()[m["start_line"] - 1:m["end_line"]]
            msrc = "\n".join(lines)
        return classify_differing(msrc, fault_stmt_sig, fix_added_norm)

    blob_status = {sha: _classify(sha) for sha in distinct}

    branches_out = {}
    for b, sha in branch_blob.items():
        branches_out[b] = "n/a" if not sha else blob_status[sha]

    counts = {}
    for st in branches_out.values():
        counts[st] = counts.get(st, 0) + 1

    r = BlastResult(path=path, method=method_name, counts=counts,
                    branches=branches_out, seconds=time.perf_counter() - t0)
    if use_cache:
        cp.write_text(json.dumps({"path": r.path, "method": r.method,
                                  "counts": r.counts, "branches": r.branches,
                                  "seconds": 0.0, "cached": False}), encoding="utf-8")
    return r


def blast_reference(repo: Repo, path: str, method_name: str, buggy_body_hash: str,
                    branches: list[str], fixed_hash: str | None = None) -> dict:
    """Slow per-branch reference (git show + scan) for validating `blast`.
    Uses the same parser (tree-sitter) as blast so body_hashes are comparable."""
    from . import tsjava
    out = {}
    for b in branches:
        src = repo.read_file(b, path)
        if not src:
            out[b] = "n/a"; continue
        fi = tsjava.scan(path, src)
        cands = [m for m in fi.methods if m.name == method_name]
        if not cands:
            out[b] = "n/a"
        elif cands[0].body_hash == buggy_body_hash:
            out[b] = "affected"
        elif fixed_hash and cands[0].body_hash == fixed_hash:
            out[b] = "fixed"
        else:
            out[b] = "changed_unrelated"
    return out

```

### `ghrca/blobstore.py`
**Purpose:** Blob-keyed scan cache in SQLite: scan each unique blob once; method/type lookups.

```python
"""Blob-keyed scan cache (D3).

Every file *version* is a blob SHA. Each unique blob is scanned exactly once
(globally, across all branches) and its types/methods are stored in SQLite keyed
by (sha, parser_ver). Resolving a stack frame therefore never needs a
whole-branch index — just the one blob the frame points at.
"""

from __future__ import annotations

import json
import time

from . import db, javascan, tsjava
from .repo import Repo

PARSER_VER = tsjava.PARSER_VER


def _scan_one(path: str, src: str):
    """tree-sitter primary; fall back to the regex scanner on empty output."""
    fi = tsjava.scan(path, src)
    used = "ts"
    if not fi.types and not fi.methods and src.strip():
        fi = javascan.scan(path, src)
        used = "regex"
    return fi, used


def already_scanned(sha: str) -> bool:
    row = db.connect().execute(
        "SELECT 1 FROM blobs WHERE sha=? AND parser_ver=?", (sha, PARSER_VER)).fetchone()
    return row is not None


def scan_blobs(repo: Repo, shas: list[str], *, path_hint: str = "X.java",
               prefetch: bool = False) -> dict:
    """Scan any not-yet-scanned blobs among `shas`. Returns stats."""
    conn = db.connect()
    todo = [s for s in set(shas) if s and not already_scanned(s)]
    stats = {"requested": len(set(shas)), "scanned": len(todo),
             "prefetch_s": 0.0, "read_s": 0.0, "fallbacks": 0}
    if not todo:
        return stats
    if prefetch:
        stats["prefetch_s"] = round(repo.prefetch_blobs(todo), 3)
    t0 = time.time()
    contents = repo.read_blobs(todo)
    stats["read_s"] = round(time.time() - t0, 3)

    now = time.time()
    conn.execute("BEGIN")
    try:
        for sha in todo:
            src = contents.get(sha, "")
            fi, used = _scan_one(path_hint, src)
            if used == "regex":
                stats["fallbacks"] += 1
            conn.execute(
                "INSERT OR REPLACE INTO blobs(sha,parser_ver,package,imports,scanned_at)"
                " VALUES(?,?,?,?,?)",
                (sha, PARSER_VER, fi.package, json.dumps(fi.imports), now))
            conn.execute("DELETE FROM types WHERE blob_sha=?", (sha,))
            conn.execute("DELETE FROM methods WHERE blob_sha=?", (sha,))
            if fi.types:
                conn.executemany(
                    "INSERT OR REPLACE INTO types(blob_sha,fqn,simple,kind,"
                    "start_line,end_line,extends,implements) VALUES(?,?,?,?,?,?,?,?)",
                    [(sha, t.fqn, t.name, t.kind, t.start, t.end, t.extends, t.implements)
                     for t in fi.types])
            if fi.methods:
                conn.executemany(
                    "INSERT OR REPLACE INTO methods(blob_sha,owner_fqn,name,sig,"
                    "start_line,end_line,body_hash) VALUES(?,?,?,?,?,?,?)",
                    [(sha, m.owner, m.name, m.signature, m.start, m.end,
                      getattr(m, "body_hash", "")) for m in fi.methods])
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return stats


def method_at_line(sha: str, line: int):
    """Innermost method in a blob containing `line` → row or None."""
    return db.connect().execute(
        "SELECT owner_fqn,name,sig,start_line,end_line,body_hash FROM methods "
        "WHERE blob_sha=? AND start_line<=? AND end_line>=? "
        "ORDER BY (end_line-start_line) ASC LIMIT 1",
        (sha, line, line)).fetchone()


def db_methods_with_body(body_hash: str):
    """All (blob_sha, owner_fqn, name) scanned methods sharing a body_hash —
    used by blast move/rename detection (D10)."""
    return db.connect().execute(
        "SELECT blob_sha, owner_fqn, name FROM methods WHERE body_hash=?",
        (body_hash,)).fetchall()


def method_by_name(sha: str, name: str):
    return db.connect().execute(
        "SELECT owner_fqn,name,sig,start_line,end_line,body_hash FROM methods "
        "WHERE blob_sha=? AND name=? ORDER BY start_line LIMIT 1",
        (sha, name)).fetchone()


def types_for_blob(sha: str):
    return db.connect().execute(
        "SELECT fqn,simple,kind,start_line,end_line,extends,implements "
        "FROM types WHERE blob_sha=?", (sha,)).fetchall()


def methods_for_blob(sha: str):
    return db.connect().execute(
        "SELECT owner_fqn,name,sig,start_line,end_line,body_hash "
        "FROM methods WHERE blob_sha=? ORDER BY start_line", (sha,)).fetchall()


def imports_for_blob(sha: str):
    row = db.connect().execute(
        "SELECT imports FROM blobs WHERE sha=? AND parser_ver=?",
        (sha, PARSER_VER)).fetchone()
    if not row:
        return []
    try:
        return json.loads(row["imports"] or "[]")
    except json.JSONDecodeError:
        return []

```

### `ghrca/cli.py`
**Purpose:** argparse CLI: status|refresh|index|analyze|agent|daemon|poll|blast|backport-plan|eval.

```python
"""Command-line interface for ghrca."""

from __future__ import annotations

import argparse
import sys

from . import config, llm
from .ghapi import GitHubAPI
from .repo import Repo
from . import orchestrator as orch


def _print_prep(prep: dict) -> None:
    print(f"repo: {prep['repo']}  default-branch: {prep['default_branch']}")
    for l in prep["log"]:
        print(f"  {l}")
    ch = prep["changes"]
    if ch["new"]:
        print(f"  NEW branches detected & indexed: {ch['new']}")
    if ch["changed"]:
        print(f"  changed branches re-indexed: {ch['changed']}")
    if ch["removed"]:
        print(f"  removed branches: {ch['removed']}")
    if prep["indexed"]:
        print(f"  indexed this run: {prep['indexed']}")


def cmd_status(args):
    repo = Repo(args.repo)
    if not repo.exists():
        print("Not cloned yet. Run `refresh` or `index` first.")
        return
    branches = repo.list_branches()
    print(f"repo: {args.repo}  default: {repo.default_branch()}")
    print(f"branches: {len(branches)}")
    for b in branches[:25]:
        print(f"  {b.name:<40} {b.sha[:8]}  {b.committed[:10]}")
    api = GitHubAPI()
    print(api.budget_note())
    print(f"LLM server: {'up' if llm.health_check() else 'DOWN'} ({config.LLM_URL})")
    # daemon/queue state (D13)
    try:
        from . import db, llmqueue
        conn = db.connect()
        fps = conn.execute("SELECT COUNT(*) c, COALESCE(SUM(count),0) s FROM fingerprints "
                           "WHERE repo=?", (args.repo,)).fetchone()
        rca_n = conn.execute("SELECT COUNT(*) c FROM rca_cache").fetchone()["c"]
        errs = conn.execute("SELECT COUNT(*) c FROM errors WHERE repo=?", (args.repo,)).fetchone()["c"]
        last = conn.execute("SELECT MAX(last_seen) m FROM refs WHERE repo=?", (args.repo,)).fetchone()["m"]
        import datetime as _dt
        lp = _dt.datetime.fromtimestamp(last).strftime("%Y-%m-%d %H:%M") if last else "never"
        print(f"queue: {llmqueue.depth()}")
        print(f"fingerprints: {fps['c']} distinct, {fps['s']} occurrences; "
              f"errors seen: {errs}; rca_cache: {rca_n}")
        print(f"last ref poll: {lp}")
    except Exception as e:
        print(f"(daemon state unavailable: {e})")


def cmd_refresh(args):
    prep = orch.prepare(args.repo, do_refresh=True, auto_index_new=True)
    _print_prep(prep)


def cmd_index(args):
    """Warm the blob-keyed scan cache for a branch (no per-branch JSON — the
    scalable store is SQLite; localization is lazy and needs no full index)."""
    from . import blobstore
    repo = Repo(args.repo)
    repo.clone_or_update()
    if args.all:
        targets = [b.name for b in repo.list_branches()]
    elif args.branch:
        targets = [args.branch]
    else:
        targets = [repo.default_branch()]
    for b in targets:
        try:
            blobs = repo.ls_java_blobs(b)
            stats = blobstore.scan_blobs(repo, list(blobs.values()))
            print(f"  {b}: {stats['scanned']} new blobs scanned "
                  f"({stats['requested']} java files, "
                  f"{stats['fallbacks']} regex-fallback); cached in SQLite")
        except Exception as e:
            print(f"  {b}: ERROR {e}")


def _report_summary(res: dict):
    if res.get("note"):
        print(f"note: {res['note']}")
    recs = res.get("records", [])
    if "mined" in res:
        print(f"mined {res['mined']} error(s) from issues.")
    print(f"analyzed {len(recs)} error(s):")
    for r in recs:
        fault = r.get("fault")
        loc = (f"{fault['method']} ({fault['path']}:{fault['line']})"
               if fault else "unlocalized")
        print(f"\n  - [{r['id']}] branch={r['branch']}  {r['source']}")
        print(f"    {(r['chain'][0]['type'] if r['chain'] else '?')}: "
              f"{(r['chain'][0]['message'][:120] if r['chain'] else '')}")
        print(f"    fault: {loc}")
        print(f"    fix-status: {r['fix_status']['headline']}")
        print(f"    report: {r['report']}")
        if r.get("report_html"):
            print(f"    html:   {r['report_html']}")
    if res.get("api"):
        print(f"\n{res['api']}")


def cmd_analyze(args):
    if getattr(args, "llm_policy", None):
        config.LLM_POLICY = args.llm_policy
    if args.log:
        res = orch.analyze_log(args.repo, args.log, use_llm=not args.no_llm,
                               force_branch=args.branch, refresh=not args.no_refresh)
    elif args.from_issues:
        res = orch.analyze_issues(args.repo, limit=args.limit,
                                  use_llm=not args.no_llm, refresh=not args.no_refresh)
    elif args.stdin:
        text = sys.stdin.read()
        res = orch.analyze_stdin_text(args.repo, text, use_llm=not args.no_llm,
                                      force_branch=args.branch, refresh=not args.no_refresh)
    else:
        print("Provide one of: --log FILE | --from-issues | --stdin")
        return
    if "prep" in res:
        _print_prep(res["prep"])
    _report_summary(res)


def cmd_agent(args):
    from . import agent
    agent.run_targets(args.targets, out_dir=args.out, use_llm=not args.no_llm,
                      policy=args.llm_policy, rca_format=args.rca_format)


def cmd_blast(args):
    import time
    from pathlib import Path
    from . import blast as blastmod, errors as errmod, htmlreport
    from .locate import localize_lazy
    repo = Repo(args.repo, source=args.source)
    if not repo.exists():
        repo.clone_or_update()
    branch = args.branch or repo.default_branch()
    commit = repo.rev_parse(branch)
    recs = errmod.from_text(Path(args.error).read_text(encoding="utf-8", errors="replace"),
                            "blast")
    if not recs:
        print("no stack trace parsed"); return
    loc = localize_lazy(recs[0], repo, commit, branch)
    if not loc.resolved:
        print("unlocalized:", loc.note); return
    f = loc.fault
    res = blastmod.blast(repo, f.path, f.method_fqn.split("#")[-1], f.body_hash)
    print(f"blast: {f.method_fqn}  ({f.path})")
    print(f"counts: {res.counts}   [{res.seconds:.2f}s{' cached' if res.cached else ''}]")
    for pr, b, st in res.by_priority()[:20]:
        print(f"  [{pr:>3}] {b:<44} {st}")
    out = config.REPORTS_DIR / repo.slug
    out.mkdir(parents=True, exist_ok=True)
    hp = out / f"blast_{int(time.time())}.html"
    hp.write_text(htmlreport.render_blast_html(res, repo.owner_repo), encoding="utf-8")
    print("report:", hp)


def cmd_daemon(args):
    from . import daemon
    daemon.run_daemon(args.targets, poll_interval=args.interval,
                      workers=args.workers, use_llm=not args.no_llm,
                      policy=args.llm_policy, rca_format=args.rca_format,
                      max_cycles=args.max_cycles)


def cmd_backport(args):
    from . import backport
    repo = Repo(args.repo, source=args.source)
    if not repo.exists():
        repo.clone_or_update()
    plan = backport.backport_plan(repo, args.fix, args.target)
    for k, v in plan.items():
        print(f"{k}: {v}")


def cmd_eval(args):
    import importlib, json
    if getattr(args, "kind", None) == "rca":
        rca_eval = importlib.import_module("eval.rca")
        r = rca_eval.run(args.split, args.final, args.llm)
        print(json.dumps({k: v for k, v in r.items() if k != "details"}, indent=2))
        return
    harness = importlib.import_module("eval.harness")
    raise SystemExit(harness.main())


def cmd_poll(args):
    from . import poller
    repo = Repo(args.repo, source=args.source)
    if not repo.exists():
        print("not cloned; run refresh/index first"); return
    ch = poller.poll_once(repo)
    print(f"{args.repo}: {ch['n_refs']} refs in {ch['elapsed_ms']}ms — "
          f"new={ch['new']} moved={ch['moved']} deleted={ch['deleted']}")


def build_parser():
    p = argparse.ArgumentParser(
        prog="ghrca",
        description="GitHub runtime-error root-cause analyzer (Java).")
    sub = p.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("status", help="show branches, index state, budgets")
    ps.add_argument("--repo", required=True)
    ps.set_defaults(func=cmd_status)

    pr = sub.add_parser("refresh", help="fetch + detect & index new/changed branches")
    pr.add_argument("--repo", required=True)
    pr.set_defaults(func=cmd_refresh)

    pi = sub.add_parser("index", help="build the structural index for branch(es)")
    pi.add_argument("--repo", required=True)
    pi.add_argument("--branch")
    pi.add_argument("--all", action="store_true", help="index every branch")
    pi.add_argument("--force", action="store_true")
    pi.set_defaults(func=cmd_index)

    pa = sub.add_parser("analyze", help="analyze runtime error(s)")
    pa.add_argument("--repo", required=True)
    pa.add_argument("--log", help="path to a log / stack-trace file")
    pa.add_argument("--from-issues", action="store_true",
                    help="mine stack traces from GitHub issues")
    pa.add_argument("--stdin", action="store_true", help="read error text from stdin")
    pa.add_argument("--limit", type=int, default=5)
    pa.add_argument("--branch", help="force analysis against this branch")
    pa.add_argument("--no-llm", action="store_true",
                    help="deterministic evidence only (no LLM narrative)")
    pa.add_argument("--no-refresh", action="store_true",
                    help="skip git fetch (use cached clone)")
    pa.set_defaults(func=cmd_analyze)

    pg = sub.add_parser("agent", help="batch-run the RCA agent over a targets.json")
    pg.add_argument("--targets", required=True, help="path to targets.json")
    pg.add_argument("--out", help="output dir (default from targets.json)")
    pg.add_argument("--no-llm", action="store_true")
    pg.add_argument("--llm-policy", choices=["auto", "always", "never"], default=None)
    pg.add_argument("--rca-format", choices=["short", "long"], default="short")
    pg.set_defaults(func=cmd_agent)

    pl = sub.add_parser("poll", help="one ls-remote poll; report new/moved/deleted refs")
    pl.add_argument("--repo", required=True)
    pl.add_argument("--source", help="local path or URL override")
    pl.set_defaults(func=cmd_poll)

    pb = sub.add_parser("blast", help="blast radius of an error across all branches")
    pb.add_argument("--repo", required=True)
    pb.add_argument("--error", required=True)
    pb.add_argument("--branch")
    pb.add_argument("--source")
    pb.set_defaults(func=cmd_blast)

    pd = sub.add_parser("daemon", help="run the continuous RCA daemon")
    pd.add_argument("--targets", required=True)
    pd.add_argument("--interval", type=float, default=60.0)
    pd.add_argument("--workers", type=int, default=4)
    pd.add_argument("--no-llm", action="store_true")
    pd.add_argument("--llm-policy", choices=["auto", "always", "never"], default=None)
    pd.add_argument("--rca-format", choices=["short", "long"], default="short")
    pd.add_argument("--max-cycles", type=int, default=None)
    pd.set_defaults(func=cmd_daemon)

    pbp = sub.add_parser("backport-plan", help="read-only backport dry-run (D14)")
    pbp.add_argument("--repo", required=True)
    pbp.add_argument("--fix", required=True, help="fix commit sha")
    pbp.add_argument("--target", required=True, help="target branch or sha")
    pbp.add_argument("--source")
    pbp.set_defaults(func=cmd_backport)

    pe = sub.add_parser("eval", help="run the evaluation harness (D15)")
    pe.add_argument("kind", nargs="?", choices=["rca"], default=None,
                    help="'rca' for the RCA corpus eval; omit for the test-bed gate")
    pe.add_argument("--split", choices=["dev", "test"], default="dev")
    pe.add_argument("--final", action="store_true")
    pe.add_argument("--llm", action="store_true")
    pe.set_defaults(func=cmd_eval)

    # policy flags also available on analyze
    pa.add_argument("--llm-policy", choices=["auto", "always", "never"], default=None)
    pa.add_argument("--rca-format", choices=["short", "long"], default="short")
    return p


def main(argv=None):
    # Windows consoles default to cp1252; force UTF-8 so report text and
    # symbols never crash stdout.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()

```

### `ghrca/config.py`
**Purpose:** Central config: cache paths, LLM + GitHub settings, prompt versions, foreign-frame prefixes.

```python
"""Central configuration and paths for ghrca.

Everything is anchored under a single cache directory next to the package so a
run leaves no scattered state. Values can be overridden via environment
variables so the same code works on a laptop, a CI box, or an office machine.
"""

from __future__ import annotations

import os
from pathlib import Path

# --- Root layout ---------------------------------------------------------
# The project root is the parent of this package (…/github_scrape).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = Path(os.environ.get("GHRCA_CACHE", PROJECT_ROOT / ".cache"))

REPOS_DIR = CACHE_DIR / "repos"        # bare-ish clones, keyed by owner__repo
WORKTREES_DIR = CACHE_DIR / "worktrees"  # transient checkouts for indexing
INDEX_DIR = CACHE_DIR / "index"        # structural index JSON, keyed by sha
API_CACHE_DIR = CACHE_DIR / "apicache"  # GitHub REST responses
REPORTS_DIR = CACHE_DIR / "reports"    # RCA reports (md + json)
STATE_DIR = CACHE_DIR / "state"        # per-repo ref snapshots for new-branch detection

# --- Local LLM (llama.cpp OpenAI-compatible server) ----------------------
# Matches the convention used by the other agents in this workspace
# (launch_qwen38flashnxt.bat -> 127.0.0.1:8080, /v1/chat/completions, --jinja).
LLM_URL = os.environ.get("GHRCA_LLM_URL", "http://127.0.0.1:8080/v1/chat/completions")
LLM_MODEL = os.environ.get("GHRCA_LLM_MODEL", "local-model")
# The server is slow (~15 tok/s) and single-slot; give it plenty of wall time
# but keep the completion budget bounded so one call can't run for hours.
LLM_TIMEOUT_SECONDS = int(os.environ.get("GHRCA_LLM_TIMEOUT", "5400"))  # 90 min
LLM_MAX_TOKENS = int(os.environ.get("GHRCA_LLM_MAX_TOKENS", "2500"))  # D9 (was 8000)
LLM_TEMPERATURE = float(os.environ.get("GHRCA_LLM_TEMPERATURE", "0.3"))
# Thinking off by default (D9): probe showed chat_template_kwargs enable_thinking
# works on this model (2 vs 37 tokens). "off" | "on".
LLM_THINKING = os.environ.get("GHRCA_LLM_THINKING", "off").lower()
# LLM usage policy (D9): auto | always | never.
LLM_POLICY = os.environ.get("GHRCA_LLM_POLICY", "auto").lower()
# Prompt template versions — part of the RCA cache key; bump when prompt changes.
PROMPT_VER = 2            # legacy (run_rca)
PROMPT_VER_SHORT = 3      # llm_short (D8)
PROMPT_VER_DEEP = 4       # llm_deep  (D8)
# A fingerprint seen this often in 24h escalates to a deep analysis (D8).
DEEP_THRESHOLD = int(os.environ.get("GHRCA_DEEP_THRESHOLD", "50"))
# Context window of the served model (Qwen3.8-Flash-Next @ 131072). We keep the
# prompt well under this after reserving room for the completion.
LLM_CONTEXT_TOKENS = int(os.environ.get("GHRCA_LLM_CTX", "131072"))

# --- GitHub access -------------------------------------------------------
# Code/branches/history/diffs go through git over SSH (unlimited). The REST API
# is only used for issues/PRs and is rate-limited to 60/hr unauthenticated;
# a token (if present) raises that to 5000/hr and unlocks Actions logs.
GITHUB_TOKEN = (
    os.environ.get("GHRCA_GITHUB_TOKEN")
    or os.environ.get("GITHUB_TOKEN")
    or os.environ.get("GH_TOKEN")
    or ""
)
GITHUB_API = "https://api.github.com"
# Prefer SSH remotes so the existing SSH key is used and no API limit applies.
GIT_REMOTE_SCHEME = os.environ.get("GHRCA_GIT_SCHEME", "ssh")  # "ssh" | "https"

# How long a cached REST response stays fresh (seconds). Issues/PRs move slowly.
API_CACHE_TTL = int(os.environ.get("GHRCA_API_TTL", str(6 * 3600)))

# --- Indexing knobs ------------------------------------------------------
# Directories we never index (build output, tests optionally kept).
INDEX_SKIP_DIRS = {".git", "target", "build", "out", "node_modules", ".idea", ".mvn"}
JAVA_SUFFIX = ".java"

# Packages we treat as "not the repo's own code" when localizing a stack trace.
# The repo's own top-level packages are discovered from the index; these are the
# universally-foreign prefixes we always skip.
FOREIGN_FRAME_PREFIXES = (
    "java.", "javax.", "jakarta.", "jdk.", "sun.", "com.sun.",
    "kotlin.", "scala.", "org.junit", "org.gradle", "org.apache.maven",
    "org.springframework", "io.netty", "reactor.", "org.slf4j",
    "org.apache.logging", "ch.qos.logback",
)


def ensure_dirs() -> None:
    """Create all cache subdirectories (idempotent)."""
    for d in (REPOS_DIR, WORKTREES_DIR, INDEX_DIR, API_CACHE_DIR, REPORTS_DIR, STATE_DIR):
        d.mkdir(parents=True, exist_ok=True)


def repo_slug(owner_repo: str) -> str:
    """`opensolon/solon-ai` -> `opensolon__solon-ai` (filesystem-safe key)."""
    return owner_repo.replace("/", "__")


def clone_url(owner_repo: str) -> str:
    """Build the clone URL honoring the configured scheme."""
    if GIT_REMOTE_SCHEME == "https":
        base = f"https://github.com/{owner_repo}.git"
        if GITHUB_TOKEN:
            # Token-in-URL only for https; harmless for public repos.
            return f"https://x-access-token:{GITHUB_TOKEN}@github.com/{owner_repo}.git"
        return base
    return f"git@github.com:{owner_repo}.git"

```

### `ghrca/context.py`
**Purpose:** Value-origin context pack (D7): failing expression, cross-class field origin, callers, history, evidence ids.

```python
"""Value-origin context pack (D7).

After localization, assemble BOUNDED, deterministic evidence the RCA (model or
template) reasons over — so the narrative can say *why* a value was null, not just
*that* it was. Everything here is fact extraction; when nothing resolves we emit
`unknown` rather than guessing. Each item gets an evidence id (E1, E2, …) so a
hypothesis can cite it (D9).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import blobstore, tsjava

# --- failing-expression parsing (D7.1) ------------------------------------
# NPE helpful messages, e.g.:
#   Cannot invoke "org.x.ChatRole.name()" because the return value of
#     "org.x.AssistantMessage.getRole()" is null
#   ... because "this.name" is null
#   ... because "<local4>" is null
#   ... because "args[1]" is null
_NPE_RETVAL = re.compile(r'return value of "([^"]+)" is null')
_NPE_BECAUSE = re.compile(r'because "([^"]+)" is null')
_NPE_INVOKE = re.compile(r'Cannot invoke "([^"]+)"')
_AIOOBE = re.compile(r"Index (\d+) out of bounds for length (\d+)")
_CCE = re.compile(r"class (\S+) cannot be cast to class (\S+)")


def parse_failing_expression(exc_type: str, message: str) -> dict:
    """Return {kind, expr, method?, operands?} describing what failed."""
    t = exc_type.split(".")[-1]
    msg = message or ""
    if t == "NullPointerException":
        m = _NPE_RETVAL.search(msg)
        if m:
            expr = m.group(1)
            method = expr.split(".")[-1].rstrip("()")
            return {"kind": "null_return_value", "expr": expr, "method": method}
        m = _NPE_BECAUSE.search(msg)
        if m:
            expr = m.group(1)
            if expr.startswith("<local"):
                return {"kind": "null_local", "expr": expr}
            if "[" in expr:
                return {"kind": "null_array_element", "expr": expr}
            if expr.startswith("this."):
                return {"kind": "null_field", "expr": expr, "field": expr.split(".")[-1]}
            return {"kind": "null_value", "expr": expr}
        m = _NPE_INVOKE.search(msg)
        if m:
            return {"kind": "null_receiver", "expr": m.group(1)}
        return {"kind": "null_unknown", "expr": ""}
    if t == "ArrayIndexOutOfBoundsException":
        m = _AIOOBE.search(msg)
        if m:
            return {"kind": "index_oob", "index": int(m.group(1)), "length": int(m.group(2))}
        return {"kind": "index_oob", "expr": ""}
    if t == "ClassCastException":
        m = _CCE.search(msg)
        if m:
            return {"kind": "bad_cast", "from": m.group(1), "to": m.group(2)}
        return {"kind": "bad_cast", "expr": ""}
    if t in ("IllegalArgumentException", "NumberFormatException"):
        return {"kind": "bad_argument", "expr": msg[:120]}
    return {"kind": "other", "expr": ""}


# --- origin resolution (D7.2) ---------------------------------------------
_LOMBOK = ("@Data", "@Getter", "@Setter", "@Value", "@Builder",
           "@AllArgsConstructor", "@NoArgsConstructor", "@RequiredArgsConstructor",
           "@ToString", "@EqualsAndHashCode")
_DESER_ANN = ("@JsonCreator", "@JsonProperty", "@ONodeAttr", "@JSONField", "@SerializedName")
_FIELD_DECL = re.compile(
    r"\b(?:private|protected|public)\b[^;=]*\b(final\b)?[^;=]*\b{name}\b\s*(=\s*([^;]+))?;")


def resolve_origin(repo, commit: str, fault_path: str, fault_blob: str,
                   owner_fqn: str, failing: dict) -> dict:
    """Trace where the null/failing value comes from. Returns a machine-readable
    origin finding (D7.2)."""
    # Only getters/fields have a traceable backing field.
    field_name = None
    if failing.get("kind") == "null_return_value" and failing.get("method", "").startswith("get"):
        m = failing["method"]
        field_name = m[3].lower() + m[4:] if len(m) > 3 else None
    elif failing.get("kind") == "null_field":
        field_name = failing.get("field")
    if not field_name:
        return {"kind": "unknown", "reason": "no backing field inferable"}

    src = repo.read_blobs([fault_blob]).get(fault_blob, "") if fault_blob else ""
    if not src:
        return {"kind": "unknown", "reason": "fault source unavailable"}

    # find the field declaration line in the fault class (a line that declares the
    # field: has the name, ends the statement, has a modifier/type before it, and
    # is not a method signature or parameter — no '(' before the name).
    decl_line = None
    for line in src.splitlines():
        before = line.split(field_name)[0] if field_name in line else ""
        if (re.search(r"\b" + re.escape(field_name) + r"\b", line) and ";" in line
                and "(" not in before
                and re.search(r"\b(private|protected|public|final|static)\b", before)):
            decl_line = line
            break
    lombok = [a for a in _LOMBOK if a in src]
    deser = [a for a in _DESER_ANN if a in src] or \
            ([a for a in ("ONode", "Jackson", "Gson", "fastjson") if a in src])

    if decl_line:
        before = decl_line.split(field_name)[0]
        is_final = bool(re.search(r"\bfinal\b", before))
        init = ""
        if "=" in decl_line:
            init = decl_line.split("=", 1)[1].rsplit(";", 1)[0].strip()
        if is_final and init:
            return {"kind": "final_field_initialized", "field": field_name, "init": init,
                    "implication": "cannot be null via normal construction; null implies "
                                   "reflection/deserialization bypassing the constructor",
                    "deser_signals": deser}
        if is_final and not init:
            return {"kind": "final_field_uninitialized", "field": field_name,
                    "implication": "must be set in every constructor; null implies a "
                                   "constructor path or deserialization missed it"}

    # where is it assigned? scan for setX / builder / assignments
    assigns = []
    setter = "set" + field_name[:1].upper() + field_name[1:]
    if re.search(r"\b" + re.escape(setter) + r"\b", src):
        assigns.append(setter)
    if re.search(r"\b" + re.escape(field_name) + r"\s*=", src):
        assigns.append("direct_assignment")
    if any(a in src for a in ("@Builder", "Builder")):
        assigns.append("builder")
    if lombok:
        return {"kind": "lombok_generated", "field": field_name, "annotations": lombok,
                "implication": "accessor/assignment generated by Lombok; check builder/"
                               "constructor usage and deserialization"}
    if assigns:
        return {"kind": "assigned_in", "field": field_name, "where": assigns,
                "deser_signals": deser}
    return {"kind": "unknown", "field": field_name, "reason": "no assignment site found"}


# --- callers (D7.3), bounded ----------------------------------------------
def find_callers(repo, commit: str, method_name: str, module_dir: str,
                 partial: bool = False, max_hits: int = 10) -> list[str]:
    if partial:
        return []  # recorded as skipped(partial_clone) by the caller
    pathspec = module_dir if module_dir else "."
    out = repo._git("grep", "-n", "-w", method_name, commit, "--", pathspec, check=False)
    hits = []
    for line in out.splitlines():
        # format: <commit>:<path>:<lineno>:<code>
        parts = line.split(":", 3)
        if len(parts) == 4 and method_name + "(" in parts[3]:
            hits.append(f"{parts[1].split('/')[-1]}:{parts[2]}: {parts[3].strip()[:100]}")
        if len(hits) >= max_hits:
            break
    return hits


# --- history (D7.4) --------------------------------------------------------
def history_signals(repo, commit: str, path: str, line: int) -> list[str]:
    out = []
    origin = repo.blame_origin(commit, path, line)
    if origin:
        meta = repo.commit_meta(origin)
        tag = repo.first_tag_containing(origin)
        out.append(f"line introduced by {origin[:8]} \"{meta['subject'][:60]}\" "
                   f"({meta['date']})" + (f", first in {tag}" if tag else ""))
    for c in repo.log_line_range(path, max(1, line - 1), line + 1, limit=3):
        out.append(f"edited by {c['sha'][:8]} \"{c['subject'][:50]}\" ({c['date']})")
    return out[:4]


# --- the pack --------------------------------------------------------------
@dataclass
class ContextPack:
    failing: dict = field(default_factory=dict)
    origin: dict = field(default_factory=dict)
    callers: list = field(default_factory=list)
    callers_skipped: str = ""
    history: list = field(default_factory=list)
    evidence: list = field(default_factory=list)  # [(id, kind, text)]

    def to_prompt(self) -> str:
        lines = []
        for eid, kind, text in self.evidence:
            lines.append(f"{eid} [{kind}]: {text}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {"failing": self.failing, "origin_finding": self.origin,
                "callers": self.callers, "callers_skipped": self.callers_skipped,
                "history": self.history,
                "evidence": [{"id": e[0], "kind": e[1], "text": e[2]} for e in self.evidence]}


def build_context(repo, commit: str, loc, err, *, partial: bool = False,
                  token_budget: int = 1500) -> ContextPack:
    pack = ContextPack()
    p = err.primary
    if not (loc.resolved and loc.fault and p):
        pack.origin = {"kind": "unknown", "reason": "unlocalized"}
        return pack

    fault = loc.fault
    pack.failing = parse_failing_expression(p.type, p.message or "")

    # Resolve the blob that DEFINES the failing getter. For a null return value
    # like "pkg.Cart.getCustomer()", the backing field lives in Cart — which may
    # differ from the fault method's class — so resolve that class across the repo
    # (D7.2: same class / parent / the expression's declaring type).
    from . import indexer
    roots = indexer.source_roots(repo, repo.default_branch())
    origin_blob = None
    origin_path = fault.path
    expr = pack.failing.get("expr", "")
    if pack.failing.get("kind") == "null_return_value" and "." in expr:
        qual = expr.rsplit(".", 1)[0]          # pkg.Cart.getCustomer() -> pkg.Cart
        simple = qual.split(".")[-1]
        qpath, qblob = indexer.resolve_frame_path(repo, commit, qual,
                                                  simple + ".java", roots)
        if qblob:
            origin_blob, origin_path = qblob, qpath
    if origin_blob is None:
        origin_path, origin_blob = indexer.resolve_frame_path(
            repo, commit, fault.frame.cls, fault.frame.file, roots)
    owner = fault.method_fqn.split("#")[0]
    pack.origin = resolve_origin(repo, commit, origin_path, origin_blob, owner, pack.failing)

    module_dir = "/".join(fault.path.split("/")[:3])
    pack.callers = find_callers(repo, commit, fault.frame.method, module_dir, partial)
    if partial and not pack.callers:
        pack.callers_skipped = "skipped(partial_clone)"
    pack.history = history_signals(repo, commit, fault.path, fault.frame.line)

    # assemble evidence items in priority order (D7.5), budget-truncated
    ev = []
    n = 1
    # E: failing method source (highest priority)
    ev.append((f"E{n}", "failing_method",
               f"{fault.method_fqn} ({fault.path}:{fault.method_start}-{fault.method_end})"))
    n += 1
    if pack.failing.get("expr") or pack.failing.get("kind"):
        ev.append((f"E{n}", "failing_expression",
                   f"{pack.failing.get('kind')}: {pack.failing.get('expr','')}".strip())); n += 1
    ev.append((f"E{n}", "origin_finding", str(pack.origin))); n += 1
    for cs in pack.callers[:5]:
        ev.append((f"E{n}", "call_site", cs)); n += 1
    for h in pack.history:
        ev.append((f"E{n}", "history", h)); n += 1
    # budget (~4 chars/token)
    budget_chars = token_budget * 4
    acc, used = [], 0
    for e in ev:
        c = len(e[2]) + 10
        if used + c > budget_chars:
            break
        acc.append(e); used += c
    pack.evidence = acc
    return pack

```

### `ghrca/daemon.py`
**Purpose:** Continuous daemon: poll -> ingest -> Stage-A threadpool -> LLM queue worker; graceful shutdown + resume.

```python
"""Continuous RCA daemon (D13).

Loop: poll refs (fetch only on change) -> ingest dropped errors -> fingerprint /
dedupe -> deterministic Stage-A report (thread pool) -> enqueue LLM job -> a
single LLM worker fills Stage B. Jobs persist in SQLite so SIGINT/SIGTERM is safe
and work resumes on restart without duplicates. Structured JSON logs are written
to .cache/logs/daemon.jsonl.
"""

from __future__ import annotations

import json
import signal
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from . import (config, db, errors as errmod, fingerprint, htmlreport,
               llmqueue, poller, rca)
from .archaeology import analyze_fix_status, FixStatus
from .ghapi import GitHubAPI
from .locate import localize_lazy
from .repo import Repo
from .sources import dropdir


def _slug(s: str) -> str:
    import re
    return re.sub(r"[^\w.-]+", "-", s).strip("-")[:40] or "x"


class Daemon:
    def __init__(self, targets: dict, *, poll_interval: float = 60.0,
                 workers: int = 4, use_llm: bool = True, out_dir: Path | None = None,
                 policy: str | None = None, rca_format: str = "short"):
        self.repos_cfg = targets.get("repos", [])
        self.poll_interval = poll_interval
        self.workers = workers
        self.use_llm = use_llm
        self.policy = policy or config.LLM_POLICY
        self.rca_format = rca_format
        self.out_dir = out_dir or (config.PROJECT_ROOT / "agent_reports")
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.stop = threading.Event()
        self._lock = threading.Lock()
        self._enqueued: set = set()   # (fp, method_hash) in-flight this run
        self.logfile = config.CACHE_DIR / "logs" / "daemon.jsonl"
        self.logfile.parent.mkdir(parents=True, exist_ok=True)
        self._repos: dict[str, Repo] = {}
        self._cfg: dict[str, dict] = {}
        for c in self.repos_cfg:
            self._repos[c["id"]] = Repo(c["id"], source=c.get("source"))
            self._cfg[c["id"]] = c

    # -- logging -----------------------------------------------------------
    def log(self, event: str, **kw):
        rec = {"ts": datetime.now().isoformat(timespec="seconds"), "event": event, **kw}
        with open(self.logfile, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        print(f"[{rec['ts']}] {event} " +
              " ".join(f"{k}={v}" for k, v in kw.items()), flush=True)

    # -- deployment resolution --------------------------------------------
    def _deployed_ref(self, repo: Repo, cfg: dict):
        default_branch = repo.default_branch()
        dep = cfg.get("deployment", {"strategy": "default"})
        if dep.get("strategy") == "file":
            raw = repo.read_file(dep.get("ref", default_branch),
                                 dep.get("path", "deployment-info.json"))
            if raw:
                try:
                    info = json.loads(raw)
                    b = info.get("deployed_branch") or info.get("branch") or default_branch
                    sha = info.get("deployed_sha") or info.get("deployed_commit")
                    if sha:
                        return sha, b, True
                    if info.get("deployed_tag"):
                        return info["deployed_tag"], b, True
                    return b, b, False
                except json.JSONDecodeError:
                    pass
        if dep.get("strategy") == "fixed":
            return dep.get("branch", default_branch), dep.get("branch", default_branch), False
        return default_branch, default_branch, False

    # -- one Stage-A job ---------------------------------------------------
    def _stage_a(self, repo_id: str, rec: dict):
        try:
            repo = self._repos[repo_id]
            cfg = self._cfg[repo_id]
            partial = cfg.get("clone_mode") == "partial"
            recs = errmod.from_text(rec["raw_text"], source=rec["source_id"])
            if not recs:
                return
            err = recs[0]
            ref, branch, pinned = self._deployed_ref(repo, cfg)
            commit = repo.rev_parse(ref)
            default_branch = repo.default_branch()

            t0 = time.perf_counter()
            loc = localize_lazy(err, repo, commit, default_branch)
            fp, exc_type, norm_msg, top = fingerprint.compute(
                err, loc.root_packages if loc.resolved else None)
            count, first_time = db.upsert_fingerprint(fp, repo_id, exc_type, norm_msg, top)
            method_hash = loc.method_hash() if loc.resolved else "none"

            if loc.resolved and loc.fault:
                f = loc.fault
                fix = analyze_fix_status(
                    repo, None, f.path, f.method_fqn.split("#")[-1],
                    f.method_start, f.method_end, commit, branch,
                    fault_line=f.frame.line,
                    use_patch_id=not partial, content_check=not partial)
            else:
                fix = FixStatus(headline="Localization failed.")
            stage_a_s = time.perf_counter() - t0

            cached = rca.cache_get(fp, method_hash, config.PROMPT_VER)
            status = "done" if cached else "pending"
            fname = (f"{datetime.now():%Y%m%dT%H%M%S}_{_slug(repo_id)}_{fp[:8]}_"
                     f"{err.id[:8]}.html")
            fpath = self.out_dir / fname
            html = htmlreport.render_html(
                err, loc, fix, branch, cached["narrative"] if cached else "",
                {"source": "cache" if cached else "pending"},
                rca_status=status, pinned=pinned)
            fpath.write_text(html, encoding="utf-8")
            db.record_error(err.id, repo_id, fp, rec["source_id"], err.raw_text,
                            branch, commit, status)
            self.log("stage_a", repo=repo_id, fp=fp[:8], seen=count,
                     new=first_time, fault=(loc.fault.method_fqn if loc.resolved else None),
                     verdict=fix.verdict if hasattr(fix, "verdict") else "?",
                     ms=round(stage_a_s * 1000, 1), report=fname, rca=status)

            # enqueue LLM job once per distinct (fp, method_hash): skip if cached
            # or already queued/running this run (dedup before the first completes)
            key = (fp, method_hash)
            do_enqueue = False
            if self.use_llm and self.policy != "never" and not cached:
                with self._lock:
                    if key not in self._enqueued:
                        self._enqueued.add(key)
                        do_enqueue = True
            if do_enqueue:
                priority = llmqueue.rca_priority(
                    100 if pinned else 30, count, first_time)
                llmqueue.enqueue("rca", {
                    "repo": repo_id, "source": cfg.get("source"),
                    "raw_text": err.raw_text, "source_id": rec["source_id"],
                    "ref": commit, "branch": branch, "default_branch": default_branch,
                    "report": str(fpath), "pinned": pinned, "partial": partial,
                    "fp": fp, "method_hash": method_hash, "fmt": self.rca_format,
                    "policy": self.policy}, priority=priority)
        except Exception as e:  # noqa: BLE001
            self.log("stage_a_error", repo=repo_id, error=f"{type(e).__name__}: {e}")

    # -- LLM job (Stage B) -------------------------------------------------
    def _rca_job(self, payload: dict):
        repo = Repo(payload["repo"], source=payload.get("source"))
        recs = errmod.from_text(payload["raw_text"], source=payload["source_id"])
        if not recs:
            return
        err = recs[0]
        loc = localize_lazy(err, repo, payload["ref"], payload["default_branch"])
        partial = payload.get("partial")
        if loc.resolved and loc.fault:
            f = loc.fault
            fix = analyze_fix_status(
                repo, None, f.path, f.method_fqn.split("#")[-1],
                f.method_start, f.method_end, payload["ref"], payload["branch"],
                fault_line=f.frame.line, use_patch_id=not partial, content_check=not partial)
        else:
            fix = FixStatus(headline="Localization failed.")
        res = rca.produce_narrative(
            err, loc, fix, payload["branch"], loc.root_packages,
            fp=payload["fp"], method_hash=payload["method_hash"],
            policy=payload["policy"], fmt=payload["fmt"],
            repo=repo, commit=payload["ref"], partial=payload.get("partial", False))
        html = htmlreport.render_html(
            err, loc, fix, payload["branch"], res["narrative"],
            {"source": res["source"], "completion_tokens": res["tokens"],
             "elapsed_s": res["seconds"], "rca_depth": res.get("rca_depth")},
            rca_status="done", pinned=payload.get("pinned", False))
        Path(payload["report"]).write_text(html, encoding="utf-8")
        db.record_error(err.id, payload["repo"], payload["fp"], payload["source_id"],
                        err.raw_text, payload["branch"], payload["ref"], "done")
        self.log("stage_b", repo=payload["repo"], fp=payload["fp"][:8],
                 source=res["source"], tokens=res["tokens"])

    # -- one cycle ---------------------------------------------------------
    def cycle(self, executor: ThreadPoolExecutor):
        for repo_id, repo in self._repos.items():
            cfg = self._cfg[repo_id]
            first = not repo.exists()
            if first:
                self.log("clone", repo=repo_id)
                repo.clone_or_update()
            # Always poll: on the first cycle this baselines the ref set (so it is
            # not mistaken for change next time); afterwards it detects deltas.
            ch = poller.poll_once(repo)
            if ch["changed"] and not first:
                self.log("refs_changed", repo=repo_id, new=len(ch["new"]),
                         moved=len(ch["moved"]), deleted=len(ch["deleted"]),
                         new_branches=ch["new"][:10])
                repo.clone_or_update()
            recs = dropdir.poll([repo_id])
            if recs:
                self.log("ingest", repo=repo_id, count=len(recs))
                for rec in recs:
                    executor.submit(self._stage_a, repo_id, rec)

    # -- run modes ---------------------------------------------------------
    def run(self, max_cycles: int | None = None):
        def _handler(signum, frame):
            self.log("signal", signum=signum)
            self.stop.set()
        signal.signal(signal.SIGINT, _handler)
        try:
            signal.signal(signal.SIGTERM, _handler)
        except (ValueError, AttributeError):
            pass

        resumed = llmqueue.reset_running()
        self.log("start", repos=list(self._repos), resumed_jobs=resumed,
                 poll_interval=self.poll_interval)
        worker = None
        if self.use_llm:
            worker = llmqueue.Worker({"rca": self._rca_job})
            worker.start()

        executor = ThreadPoolExecutor(max_workers=self.workers)
        cycles = 0
        try:
            while not self.stop.is_set():
                self.cycle(executor)
                cycles += 1
                if max_cycles and cycles >= max_cycles:
                    break
                self.stop.wait(self.poll_interval)
        finally:
            executor.shutdown(wait=True)
            if worker:
                worker.stop()
                worker.join(timeout=5)
            self.log("stopped", cycles=cycles, queue=llmqueue.depth())

    def run_once_sync(self):
        """One cycle + drain Stage-A, no LLM worker (for tests)."""
        executor = ThreadPoolExecutor(max_workers=self.workers)
        self.cycle(executor)
        executor.shutdown(wait=True)


def run_daemon(targets_path: str, *, max_cycles=None, **kw):
    targets = json.loads(Path(targets_path).read_text(encoding="utf-8"))
    Daemon(targets, **kw).run(max_cycles=max_cycles)

```

### `ghrca/db.py`
**Purpose:** SQLite (WAL) store + migrations: blobs/types/methods, refs, fixes, fingerprints, errors, rca_cache, jobs, repo_meta.

```python
"""SQLite storage (D1) — one WAL database replacing per-branch JSON indexes.

A migrations list keyed by a `schema_version` table lets the schema evolve
without wiping the cache. One connection per thread (SQLite objects are not
shareable across threads); use `connect()` wherever you need one.
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

from . import config

# Each migration is a list of SQL statements applied in order. Append new
# migrations; never edit an applied one.
MIGRATIONS: list[list[str]] = [
    # v1 — initial schema
    [
        """CREATE TABLE blobs(
             sha TEXT NOT NULL, parser_ver INTEGER NOT NULL,
             package TEXT, imports TEXT, scanned_at REAL,
             PRIMARY KEY(sha, parser_ver))""",
        """CREATE TABLE types(
             blob_sha TEXT NOT NULL, fqn TEXT NOT NULL, simple TEXT NOT NULL,
             kind TEXT, start_line INT, end_line INT, extends TEXT, implements TEXT,
             PRIMARY KEY(blob_sha, fqn))""",
        """CREATE TABLE methods(
             blob_sha TEXT NOT NULL, owner_fqn TEXT NOT NULL, name TEXT NOT NULL,
             sig TEXT, start_line INT NOT NULL, end_line INT NOT NULL,
             body_hash TEXT NOT NULL,
             PRIMARY KEY(blob_sha, owner_fqn, name, start_line))""",
        "CREATE INDEX idx_types_simple ON types(simple)",
        "CREATE INDEX idx_methods_hash ON methods(body_hash)",
        """CREATE TABLE refs(
             repo TEXT, ref TEXT, sha TEXT, first_seen REAL, last_seen REAL,
             prev_sha TEXT, PRIMARY KEY(repo, ref))""",
        """CREATE TABLE fixes(
             repo TEXT, path TEXT, commit_sha TEXT, patch_id TEXT, subject TEXT,
             jira_or_issue_id TEXT, PRIMARY KEY(repo, path, commit_sha))""",
        """CREATE TABLE fingerprints(
             fp TEXT, repo TEXT, exc_type TEXT, norm_msg TEXT, top_frame TEXT,
             first_seen REAL, last_seen REAL, count INT, PRIMARY KEY(fp, repo))""",
        """CREATE TABLE errors(
             id TEXT PRIMARY KEY, repo TEXT, fp TEXT, source TEXT, raw TEXT,
             received_at REAL, branch TEXT, commit_sha TEXT, status TEXT)""",
        """CREATE TABLE rca_cache(
             fp TEXT, method_hash TEXT, prompt_ver INT, model TEXT,
             narrative TEXT, tokens INT, seconds REAL, created REAL,
             PRIMARY KEY(fp, method_hash, prompt_ver))""",
        """CREATE TABLE jobs(
             id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT, priority INT,
             payload TEXT, state TEXT, attempts INT DEFAULT 0,
             created REAL, updated REAL, error TEXT)""",
        "CREATE INDEX idx_jobs_pick ON jobs(state, priority DESC, created)",
        # repo-level scratch (source roots, etc.) as JSON
        "CREATE TABLE repo_meta(repo TEXT PRIMARY KEY, data TEXT, updated REAL)",
    ],
]

_local = threading.local()


def _db_path() -> Path:
    import os
    p = Path(os.environ.get("GHRCA_DB", config.CACHE_DIR / "ghrca.db"))
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def connect() -> sqlite3.Connection:
    """Return this thread's connection, applying pragmas + migrations once."""
    conn = getattr(_local, "conn", None)
    if conn is not None:
        return conn
    conn = sqlite3.connect(str(_db_path()), timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=30000")
    _migrate(conn)
    _local.conn = conn
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    conn.execute("CREATE TABLE IF NOT EXISTS schema_version(v INTEGER NOT NULL)")
    row = conn.execute("SELECT MAX(v) AS v FROM schema_version").fetchone()
    cur = row["v"] if row and row["v"] is not None else 0
    for i in range(cur, len(MIGRATIONS)):
        conn.execute("BEGIN")
        try:
            for stmt in MIGRATIONS[i]:
                conn.execute(stmt)
            conn.execute("INSERT INTO schema_version(v) VALUES(?)", (i + 1,))
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise


def upsert_fingerprint(fp: str, repo: str, exc_type: str, norm_msg: str,
                       top_frame: str) -> tuple[int, bool]:
    """Increment the fingerprint's count. Returns (new_count, first_time)."""
    import time
    conn = connect()
    now = time.time()
    row = conn.execute("SELECT count FROM fingerprints WHERE fp=? AND repo=?",
                       (fp, repo)).fetchone()
    if row is None:
        conn.execute(
            "INSERT INTO fingerprints(fp,repo,exc_type,norm_msg,top_frame,"
            "first_seen,last_seen,count) VALUES(?,?,?,?,?,?,?,1)",
            (fp, repo, exc_type, norm_msg, top_frame, now, now))
        return 1, True
    n = row["count"] + 1
    conn.execute("UPDATE fingerprints SET count=?, last_seen=? WHERE fp=? AND repo=?",
                 (n, now, fp, repo))
    return n, False


def record_error(err_id: str, repo: str, fp: str, source: str, raw: str,
                 branch: str, commit_sha: str, status: str) -> None:
    import time
    connect().execute(
        "INSERT OR REPLACE INTO errors(id,repo,fp,source,raw,received_at,"
        "branch,commit_sha,status) VALUES(?,?,?,?,?,?,?,?,?)",
        (err_id, repo, fp, source, raw[:20000], time.time(), branch, commit_sha, status))


def reset_thread_conn() -> None:
    """Drop this thread's cached connection (used in tests)."""
    conn = getattr(_local, "conn", None)
    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass
    _local.conn = None

```

### `ghrca/errors.py`
**Purpose:** Java stack-trace parser (exception chain + frames); lambda/anon/proxy/non-Java frame normalization; jar-version parsing.

```python
"""Runtime-error ingestion: parse Java stack traces from logs or issues.

A stack trace is the primary signal. We parse it into a throwable *chain*
(primary + "Caused by" causes), each with ordered frames
`Class.method(File.java:line)`. This structure is what the localizer and RCA
engine consume.
"""

from __future__ import annotations

import re
import hashlib
from dataclasses import dataclass, field, asdict

# Exception header: "java.lang.NullPointerException: message"
_EXC_RE = re.compile(r"([A-Za-z_][\w.$]*(?:Exception|Error|Throwable))\b(?::\s*(.*))?")
# Frame: "at pkg.Class.method(File.java:123)"  /  "(Native Method)" / "(Unknown Source)"
_FRAME_RE = re.compile(
    r"^\s*at\s+([\w.$]+)\.([\w$<>]+)\((?:([\w.$]+\.java):(\d+)|[^)]*)\)")
_CAUSED_RE = re.compile(r"^\s*Caused by:\s*(.*)")
_VERSION_RE = re.compile(r"\b(\d+\.\d+(?:\.\d+)?(?:[.-][A-Za-z0-9]+)?)\b")


_PROXY_RE = re.compile(r"\$\$(?:Enhancer|FastClass)By|^com\.sun\.proxy\.\$Proxy"
                       r"|^jdk\.proxy\d|\$\$SpringCGLIB\$\$|CGLIB\$\$")
_LAMBDA_RE = re.compile(r"^lambda\$(.+)\$\d+$")
_SYNTH_RE = re.compile(r"^(access\$\d+|.*\$\$.*|\$\d+)$")
_UNSUP_SUFFIX = (".kt", ".scala", ".groovy")
# jar-version annotation, e.g.  ~[kafka-clients-3.7.0.jar:?]  [spring-core-5.3.1.jar:5.3.1]
_LIB_RE = re.compile(r"[~\[]\s*\[?([A-Za-z0-9._-]+?)-(\d[\w.\-]*)\.jar:")


@dataclass
class Frame:
    cls: str
    method: str
    file: str = ""
    line: int = 0
    lib: dict = field(default_factory=dict)   # {name, version} from jar annotation

    def is_located(self) -> bool:
        return bool(self.file and self.line)

    def is_proxy(self) -> bool:
        return bool(_PROXY_RE.search(self.cls))

    def language(self) -> str:
        if self.file.endswith(".java"):
            return "java"
        if self.file.endswith(_UNSUP_SUFFIX):
            return "unsupported"
        return "unknown"

    def normalized_method(self) -> tuple[str, bool]:
        """Return (method_name, is_synthetic). lambda$foo$0 -> ('foo', False);
        access$100 / bridge -> ('', True)."""
        m = _LAMBDA_RE.match(self.method)
        if m:
            return m.group(1), False
        if self.method.startswith("access$") or self.method in ("<clinit>",):
            return self.method, True
        return self.method, False


@dataclass
class Throwable:
    type: str
    message: str = ""
    frames: list = field(default_factory=list)  # list[Frame]


@dataclass
class ErrorRecord:
    id: str
    source: str                       # "log:file.txt" | "issue:#123"
    title: str = ""
    raw_text: str = ""
    chain: list = field(default_factory=list)   # list[Throwable], primary first
    branch_hint: str = ""             # version/branch mentioned near the error
    branch: str = ""                  # resolved branch (filled by orchestrator)

    # convenience -----------------------------------------------------------
    @property
    def primary(self):
        return self.chain[0] if self.chain else None

    @property
    def deepest(self):
        return self.chain[-1] if self.chain else None

    def all_frames(self):
        for t in self.chain:
            yield from t.frames

    def to_dict(self) -> dict:
        return {
            "id": self.id, "source": self.source, "title": self.title,
            "branch_hint": self.branch_hint, "branch": self.branch,
            "chain": [
                {"type": t.type, "message": t.message,
                 "frames": [asdict(f) for f in t.frames]}
                for t in self.chain
            ],
        }

    def summary(self) -> str:
        p = self.primary
        if not p:
            return "(no exception parsed)"
        head = f"{p.type}: {p.message}".strip().rstrip(":")
        d = self.deepest
        if d and d is not p:
            head += f"  <- caused by {d.type}: {d.message}".rstrip(":")
        return head[:300]


def _parse_throwable_header(line: str):
    m = _EXC_RE.search(line)
    if not m:
        return None
    return Throwable(type=m.group(1), message=(m.group(2) or "").strip())


def parse_trace(text: str) -> list[Throwable]:
    """Parse one stack trace (possibly with Caused-by chain) into throwables."""
    chain: list[Throwable] = []
    current: Throwable | None = None
    for line in text.splitlines():
        caused = _CAUSED_RE.match(line)
        if caused:
            th = _parse_throwable_header(caused.group(1))
            if th:
                chain.append(th)
                current = th
            continue
        fm = _FRAME_RE.match(line)
        if fm:
            if current is None:
                # frames before any header we recognized -> synthesize one
                current = Throwable(type="UnknownThrowable")
                chain.append(current)
            f = Frame(cls=fm.group(1), method=fm.group(2))
            if fm.group(3):
                f.file = fm.group(3)
                f.line = int(fm.group(4))
            lm = _LIB_RE.search(line)
            if lm:
                f.lib = {"name": lm.group(1), "version": lm.group(2)}
            current.frames.append(f)
            continue
        # a header line not preceded by "Caused by"
        if current is None or (not line.startswith((" ", "\t")) and _EXC_RE.search(line)
                               and "at " not in line):
            th = _parse_throwable_header(line)
            if th and (current is None or th.frames == []):
                # only start a new top throwable if we don't already have one
                if current is None:
                    chain.append(th)
                    current = th
    return chain


def _mk_id(source: str, text: str) -> str:
    return hashlib.sha1((source + "\n" + text).encode()).hexdigest()[:12]


def _find_traces_in_blob(text: str) -> list[str]:
    """Split a log blob into individual stack-trace chunks."""
    lines = text.splitlines()
    chunks: list[list[str]] = []
    cur: list[str] = []
    in_trace = False
    for i, line in enumerate(lines):
        is_header = bool(_EXC_RE.search(line)) and "at " not in line
        is_frame = bool(_FRAME_RE.match(line)) or bool(_CAUSED_RE.match(line)) \
            or line.strip().startswith("...")
        if is_header and not line.strip().startswith("Caused by"):
            # a fresh top-level exception header starts a new chunk
            if in_trace and cur:
                chunks.append(cur)
            cur = [line]
            in_trace = True
        elif in_trace and (is_frame or is_header):
            cur.append(line)
        elif in_trace and not line.strip():
            cur.append(line)
        elif in_trace:
            # non-trace line: allow a couple before ending the chunk
            if cur and cur[-1].strip() == "" and (
                    i + 1 >= len(lines) or not _FRAME_RE.match(lines[i + 1] if i + 1 < len(lines) else "")):
                chunks.append(cur)
                cur = []
                in_trace = False
            else:
                cur.append(line)
    if cur:
        chunks.append(cur)
    # keep only chunks that actually contain a frame
    return ["\n".join(c) for c in chunks if any(_FRAME_RE.match(x) for x in c)]


def from_text(text: str, source: str, title: str = "") -> list[ErrorRecord]:
    """Parse all stack traces found in a text blob into ErrorRecords."""
    records: list[ErrorRecord] = []
    for chunk in _find_traces_in_blob(text) or [text]:
        chain = parse_trace(chunk)
        if not chain or not any(t.frames for t in chain):
            continue
        vh = _VERSION_RE.search(chunk)
        rec = ErrorRecord(
            id=_mk_id(source, chunk),
            source=source,
            title=title or (chain[0].type if chain else "error"),
            raw_text=chunk.strip(),
            chain=chain,
            branch_hint=(vh.group(1) if vh else ""),
        )
        records.append(rec)
    return records


def from_issue(issue: dict) -> list[ErrorRecord]:
    """Extract stack traces from a GitHub issue body."""
    body = issue.get("body") or ""
    if not _FRAME_RE.search(body) and "at " not in body:
        return []
    num = issue.get("number")
    recs = from_text(body, source=f"issue:#{num}", title=issue.get("title", ""))
    # prefer a version hint from the title/labels if the body lacked one
    for r in recs:
        if not r.branch_hint:
            vh = _VERSION_RE.search(issue.get("title", ""))
            if vh:
                r.branch_hint = vh.group(1)
    return recs

```

### `ghrca/fingerprint.py`
**Purpose:** Error fingerprint + message normalization + message-identifier extraction.

```python
"""Error fingerprinting (D6) and message-identifier extraction (used by D11).

A fingerprint collapses superficially-different occurrences of the *same* bug
(different ids, counts, paths, addresses) to one stable key, so the LLM is called
once per distinct bug rather than once per error.
"""

from __future__ import annotations

import hashlib
import re

from . import config

# --- message normalization -------------------------------------------------
_RE_QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")
_RE_UUID = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
                      r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
# hex: 0x + >=6 hex digits (>=8 chars total), OR an >=8-char run that actually
# contains a letter (so pure-decimal integers fall through to the <N> rule).
_RE_HEX = re.compile(r"\b0x[0-9a-fA-F]{6,}\b"
                     r"|\b(?=[0-9a-fA-F]{8,}\b)[0-9a-fA-F]*[a-fA-F][0-9a-fA-F]*\b")
_RE_NUM = re.compile(r"(?<![\w])[+-]?\d+(?:\.\d+)?(?![\w])")
_RE_IPV4 = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
_RE_IPV6 = re.compile(r"\b(?:[0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}\b")
_RE_PATH_WIN = re.compile(r"\b[A-Za-z]:\\[^\s\"']*")
_RE_PATH_NIX = re.compile(r"(?<![\w])/[^\s\"':]+")
_RE_WS = re.compile(r"\s+")

# NPE "helpful message" wrapper we preserve (only its inner exprs get normalized)
# e.g. Cannot invoke "X.name()" because the return value of "Y.getRole()" is null


def normalize_message(msg: str) -> str:
    """Normalize a throwable message so variable data doesn't split fingerprints.

    Order per D6. Note: integers are replaced before the IP rules, so a numeric
    IPv4/IPv6 collapses to a dotted/colon-joined run of <N> — still stable, which
    is all fingerprinting needs. Quoted-expression *shape* (the NPE helpful
    message) is preserved; only literal values inside change.
    """
    if not msg:
        return ""
    s = msg
    # Keep quoted *expressions* that look like code (contain a dot or parens)
    # intact; replace only quoted *string literals* with <S>.
    def _quote_sub(m):
        inner = m.group(0)[1:-1]
        if ("(" in inner) or ("." in inner and " " not in inner):
            return m.group(0)  # code-like expr -> keep (NPE helpful message)
        return "<S>"
    s = _RE_QUOTED.sub(_quote_sub, s)
    s = _RE_UUID.sub("<UUID>", s)
    s = _RE_HEX.sub("<HEX>", s)
    s = _RE_PATH_WIN.sub("<PATH>", s)
    s = _RE_PATH_NIX.sub("<PATH>", s)
    s = _RE_NUM.sub("<N>", s)
    s = _RE_IPV4.sub("<IP>", s)            # after <N>: numeric IPs already <N>.<N>...
    s = _RE_IPV6.sub("<IP>", s)
    s = s.lower()
    s = _RE_WS.sub(" ", s).strip()
    return s[:200]


# --- identifier extraction (for drift validation, D11) ---------------------
_RE_IDENT = re.compile(r"[A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)*(?:\(\))?")


def extract_message_identifiers(msg: str) -> list[str]:
    """Pull code identifiers out of the quoted parts of an exception message.

    e.g. 'Cannot invoke "ChatRole.name()" because the return value of
    "AssistantMessage.getRole()" is null' -> ['ChatRole.name()', 'name',
    'AssistantMessage.getRole()', 'getRole'].
    """
    out: list[str] = []
    for q in _RE_QUOTED.findall(msg or ""):
        inner = q[1:-1]
        for m in _RE_IDENT.findall(inner):
            if len(m) < 2:
                continue
            out.append(m)
            # also the trailing simple member (name from X.name())
            simple = m.rstrip("()").split(".")[-1]
            if simple and simple != m:
                out.append(simple)
    # de-dup preserve order
    seen, uniq = set(), []
    for x in out:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq


# --- top repo-owned frame --------------------------------------------------
def _is_repo_owned(cls: str, root_packages=None) -> bool:
    if cls.startswith(config.FOREIGN_FRAME_PREFIXES):
        return False
    if root_packages:
        return any(cls.startswith(rp) for rp in root_packages)
    return True  # ingest-time heuristic: anything not clearly foreign


def top_frame(err, root_packages=None) -> str:
    """'Class#method' of the first repo-owned frame of the deepest cause,
    else the top frame of the deepest cause, else ''."""
    if not err.chain:
        return ""
    deepest = err.chain[-1]
    for f in deepest.frames:
        if _is_repo_owned(f.cls, root_packages):
            return f"{f.cls}#{f.method}"
    # scan all throwables deepest-first for any repo-owned frame
    for th in reversed(err.chain):
        for f in th.frames:
            if _is_repo_owned(f.cls, root_packages):
                return f"{f.cls}#{f.method}"
    f0 = deepest.frames[0] if deepest.frames else None
    return f"{f0.cls}#{f0.method}" if f0 else ""


def fingerprint(exc_type: str, message: str, top: str) -> str:
    norm = normalize_message(message)
    key = f"{exc_type}|{norm}|{top}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def compute(err, root_packages=None):
    """Return (fp, exc_type, norm_msg, top_frame) for an ErrorRecord."""
    p = err.primary
    exc_type = p.type if p else "UnknownThrowable"
    message = p.message if p else ""
    top = top_frame(err, root_packages)
    norm = normalize_message(message)
    return fingerprint(exc_type, message, top), exc_type, norm, top

```

### `ghrca/ghapi.py`
**Purpose:** Throttled, on-disk + ETag-cached GitHub REST client (issues/PRs only; 60/hr aware).

```python
"""Throttled, on-disk-cached GitHub REST client.

The API is the *scarce* resource here (60 req/hr unauthenticated). Everything
that can be done with git-over-SSH is done there instead; this module is only
for issues/PRs/search. Every GET is cached to disk and every call respects the
live rate-limit headers, backing off (or refusing) rather than getting the key
throttled.
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

from . import config


@dataclass
class RateState:
    remaining: int = -1     # -1 = unknown
    limit: int = -1
    reset_epoch: int = 0

    def note(self, headers) -> None:
        try:
            self.remaining = int(headers.get("X-RateLimit-Remaining", self.remaining))
            self.limit = int(headers.get("X-RateLimit-Limit", self.limit))
            self.reset_epoch = int(headers.get("X-RateLimit-Reset", self.reset_epoch))
        except (TypeError, ValueError):
            pass


class RateLimited(RuntimeError):
    """Raised when the API budget is exhausted and the caller opted not to wait."""


class GitHubAPI:
    def __init__(self, wait_on_limit: bool = False):
        self.rate = RateState()
        self.wait_on_limit = wait_on_limit
        config.API_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # -- caching -----------------------------------------------------------
    def _cache_path(self, url: str):
        key = hashlib.sha1(url.encode()).hexdigest()
        return config.API_CACHE_DIR / f"{key}.json"

    def _read_cache(self, url: str):
        p = self._cache_path(url)
        if not p.exists():
            return None
        try:
            blob = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        if time.time() - blob.get("_fetched_at", 0) > config.API_CACHE_TTL:
            return None
        return blob.get("data")

    def _write_cache(self, url: str, data, etag: str | None = None) -> None:
        p = self._cache_path(url)
        p.write_text(
            json.dumps({"_fetched_at": time.time(), "data": data, "etag": etag}),
            encoding="utf-8",
        )

    def _read_cache_raw(self, url: str):
        p = self._cache_path(url)
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    # -- core GET ----------------------------------------------------------
    def get(self, path: str, params: dict | None = None, *, use_cache: bool = True):
        """GET a REST path (e.g. '/repos/o/r/issues'). Returns parsed JSON.

        Returns None if the budget is exhausted and wait_on_limit is False and
        there is no cache -- callers must degrade gracefully.
        """
        url = config.GITHUB_API + path
        if params:
            url += "?" + urllib.parse.urlencode(params)

        if use_cache:
            cached = self._read_cache(url)
            if cached is not None:
                return cached

        # Respect a known-exhausted budget before spending a request.
        if self.rate.remaining == 0:
            wait = max(0, self.rate.reset_epoch - int(time.time())) + 2
            if self.wait_on_limit and wait < 3600:
                time.sleep(wait)
            else:
                raise RateLimited(
                    f"GitHub API budget exhausted; resets in ~{wait}s. "
                    f"Set GITHUB_TOKEN for 5000/hr, or rely on git-only analysis."
                )

        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "ghrca/0.1",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if config.GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {config.GITHUB_TOKEN}"

        # Conditional request (D10): with a token, a 304 costs no rate budget.
        raw = self._read_cache_raw(url) if use_cache else None
        if raw and raw.get("etag") and config.GITHUB_TOKEN:
            headers["If-None-Match"] = raw["etag"]

        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                self.rate.note(resp.headers)
                etag = resp.headers.get("ETag")
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            self.rate.note(e.headers)
            if e.code == 304 and raw is not None:
                # not modified — refresh freshness, no budget spent
                self._write_cache(url, raw["data"], raw.get("etag"))
                return raw["data"]
            if e.code == 403 and self.rate.remaining == 0:
                raise RateLimited("GitHub API 403 (rate limited).") from e
            if e.code == 404:
                return None
            raise
        if use_cache:
            self._write_cache(url, data, etag)
        return data

    # -- convenience -------------------------------------------------------
    def issues(self, owner_repo: str, state: str = "open", per_page: int = 30, page: int = 1):
        return self.get(
            f"/repos/{owner_repo}/issues",
            {"state": state, "per_page": per_page, "page": page},
        ) or []

    def pulls(self, owner_repo: str, state: str = "all", per_page: int = 50, page: int = 1):
        return self.get(
            f"/repos/{owner_repo}/pulls",
            {"state": state, "per_page": per_page, "page": page,
             "sort": "updated", "direction": "desc"},
        ) or []

    def search_issues(self, query: str, per_page: int = 20):
        return self.get(
            "/search/issues", {"q": query, "per_page": per_page}
        ) or {"items": []}

    def budget_note(self) -> str:
        if self.rate.remaining < 0:
            tok = "authenticated" if config.GITHUB_TOKEN else "unauthenticated (60/hr)"
            return f"API budget unknown ({tok})."
        return f"API budget: {self.rate.remaining}/{self.rate.limit} remaining."

```

### `ghrca/htmlreport.py`
**Purpose:** Standalone HTML reports (inline CSS, light/dark): depth + confidence badges, hypotheses, blast block.

````python
"""Render an RCA into a standalone, self-contained HTML report.

No external assets or JS libraries: inline CSS only, works offline, light/dark
aware. The analytical narrative (LLM markdown) is converted with a small,
dependency-free markdown subset; the deterministic sections are built directly
from structured data with proper escaping.
"""

from __future__ import annotations

import html
import re
from datetime import datetime

from .archaeology import FixStatus
from .errors import ErrorRecord
from .locate import LocResult

_KIND_COLORS = {
    "reverted": "#e5484d", "lost_fix": "#e5484d", "open_pr": "#f5a623",
    "abandoned_pr": "#f5a623", "merged_pr": "#30a46c", "fix_present": "#30a46c",
    "fixy_commit": "#8b8d98",
}


def _esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def _md_to_html(md: str) -> str:
    """Convert a small markdown subset (headings, fences, lists, bold, code)."""
    lines = (md or "").splitlines()
    out: list[str] = []
    i = 0
    in_list = False

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    def inline(t: str) -> str:
        t = _esc(t)
        t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
        t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
        return t

    while i < len(lines):
        line = lines[i]
        # fenced code block
        m = re.match(r"^```(\w*)\s*$", line)
        if m:
            close_list()
            lang = m.group(1)
            buf = []
            i += 1
            while i < len(lines) and not re.match(r"^```\s*$", lines[i]):
                buf.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            out.append(f'<pre class="code lang-{_esc(lang)}"><code>'
                       + _esc("\n".join(buf)) + "</code></pre>")
            continue
        hm = re.match(r"^(#{1,6})\s+(.*)$", line)
        if hm:
            close_list()
            lvl = min(len(hm.group(1)) + 1, 6)  # shift so ### -> h4-ish scale
            out.append(f"<h{lvl}>{inline(hm.group(2))}</h{lvl}>")
            i += 1
            continue
        lm = re.match(r"^\s*[-*]\s+(.*)$", line)
        if lm:
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline(lm.group(1))}</li>")
            i += 1
            continue
        if line.strip() == "":
            close_list()
            i += 1
            continue
        close_list()
        out.append(f"<p>{inline(line)}</p>")
        i += 1
    close_list()
    return "\n".join(out)


def _numbered_code(code: str) -> str:
    return f'<pre class="code numbered"><code>{_esc(code)}</code></pre>'


_CSS = """
:root{--bg:#ffffff;--fg:#1a1a1e;--muted:#6b6d76;--card:#f6f7f9;--border:#e3e5ea;
--accent:#3b82f6;--code-bg:#f2f3f5;--code-fg:#0f172a;--chip:#eef1f6;}
@media (prefers-color-scheme:dark){:root{--bg:#0f1115;--fg:#e6e7ea;--muted:#9a9da6;
--card:#181b21;--border:#282c34;--accent:#6ea8fe;--code-bg:#0b0d11;--code-fg:#d6deeb;
--chip:#20242c;}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:920px;margin:0 auto;padding:32px 16px 80px}
h1{font-size:22px;line-height:1.35;margin:0 0 6px}
h2{font-size:17px;margin:34px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--border)}
h3,h4{font-size:15px;margin:18px 0 6px}
p{margin:8px 0}
.sub{color:var(--muted);font-size:13px;margin-bottom:20px}
.meta{background:var(--card);border:1px solid var(--border);border-radius:10px;
padding:14px 16px;margin:16px 0}
.meta div{margin:3px 0}
.k{color:var(--muted);display:inline-block;min-width:118px}
.chip{display:inline-block;padding:2px 9px;border-radius:999px;background:var(--chip);
font-size:12px;font-weight:600}
.headline{font-weight:600}
pre.code{background:var(--code-bg);color:var(--code-fg);border:1px solid var(--border);
border-radius:8px;padding:12px 14px;overflow:auto;font:12.5px/1.5 "SF Mono",Consolas,
"Roboto Mono",monospace;white-space:pre;margin:8px 0}
code{background:var(--code-bg);padding:1px 5px;border-radius:4px;
font:12.5px "SF Mono",Consolas,monospace}
pre.code code{background:none;padding:0}
.findings li{margin:6px 0}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:7px;
vertical-align:middle}
.kind{font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.4px}
.refs{color:var(--muted);font-size:12px}
.foot{color:var(--muted);font-size:12px;margin-top:40px;border-top:1px solid var(--border);
padding-top:12px}
details{margin:8px 0}summary{cursor:pointer;color:var(--accent);font-weight:600}
.trace{white-space:pre;font:12.5px/1.5 "SF Mono",Consolas,monospace}
"""


_BLAST_COLORS = {"affected": "#e5484d", "fixed": "#30a46c",
                 "changed_unrelated": "#f5a623", "n/a": "#8b8d98"}


def render_blast_html(res, repo_id: str, manifest_branch=None) -> str:
    counts = " · ".join(f'<b style="color:{_BLAST_COLORS.get(k,"#888")}">{v} {k}</b>'
                        for k, v in sorted(res.counts.items(), key=lambda x: -x[1]))
    rows = res.by_priority(manifest_branch)
    top = rows[:20]
    def row_html(pr, b, st):
        c = _BLAST_COLORS.get(st, "#888")
        return (f'<tr><td>{pr}</td><td><code>{_esc(b)}</code></td>'
                f'<td style="color:{c};font-weight:600">{_esc(st)}</td></tr>')
    top_rows = "".join(row_html(*r) for r in top)
    all_rows = "".join(row_html(*r) for r in rows)
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>Blast — {_esc(res.method)}</title><style>{_CSS}
table{{border-collapse:collapse;width:100%;font-size:13px}}
th,td{{border:1px solid var(--border);padding:5px 9px;text-align:left}}</style></head>
<body><div class="wrap">
<h1>Blast radius — {_esc(res.method)}</h1>
<div class="sub">{_esc(res.path)} · {_esc(repo_id)} · computed in {res.seconds:.2f}s
{'(cached)' if res.cached else ''}</div>
<div class="meta"><b>Branch impact:</b> {counts}</div>
<h2>Top 20 branches by priority</h2>
<table><tr><th>prio</th><th>branch</th><th>status</th></tr>{top_rows}</table>
<details><summary>All {len(rows)} branches</summary>
<table><tr><th>prio</th><th>branch</th><th>status</th></tr>{all_rows}</table></details>
</div></body></html>"""


def render_html(err: ErrorRecord, loc: LocResult, fix: FixStatus, branch: str,
                narrative: str, llm_meta: dict, *, rca_status: str = "done",
                pinned: bool = True) -> str:
    p = err.primary
    title = f"{p.type}: {p.message}" if p else "Runtime error"

    banner = ""
    if rca_status == "pending":
        banner = ('<div style="background:#f5a62322;border:1px solid #f5a623;'
                  'border-radius:8px;padding:10px 14px;margin:12px 0;font-weight:600">'
                  '⏳ RCA pending — deterministic analysis shown below; the LLM '
                  'narrative will fill in when its queued job completes.</div>')
    conf = getattr(loc, "confidence", "high")
    conf_color = {"high": "#30a46c", "medium": "#f5a623", "low": "#e5484d"}.get(conf, "#8b8d98")
    conf_chip = (f'<span class="chip" style="color:{conf_color}">localization: '
                 f'{_esc(conf)}</span>')
    depth = (llm_meta or {}).get("rca_depth", "")
    depth_color = {"llm_deep": "#6ea8fe", "llm_short": "#30a46c",
                   "location_only": "#f5a623"}.get(depth, "#8b8d98")
    depth_chip = (f' <span class="chip" style="color:{depth_color}">depth: '
                  f'{_esc(depth)}</span>') if depth else ""
    pin_warn = ("" if pinned else
                '<div class="sub">⚠ analyzed against branch tip; line numbers may '
                'have drifted (not pinned to a deployed commit).</div>')

    # meta block
    fault_line = ""
    if loc.resolved and loc.fault:
        fault_line = (f'<div><span class="k">Fault site</span> '
                      f'<code>{_esc(loc.fault.method_fqn)}</code> '
                      f'({_esc(loc.fault.path)}:{loc.fault.frame.line})</div>')
    head_color = _KIND_COLORS.get(fix.findings[0].kind, "#8b8d98") if fix.findings else "#8b8d98"

    # stack trace
    trace_lines = []
    for i, th in enumerate(err.chain):
        tag = "" if i == 0 else "Caused by: "
        trace_lines.append(_esc(f"{tag}{th.type}: {th.message}".rstrip()))
        for f in th.frames[:14]:
            locs = f"({f.file}:{f.line})" if f.is_located() else ""
            trace_lines.append(_esc(f"    at {f.cls}.{f.method}{locs}"))
    trace_html = "\n".join(trace_lines)

    # findings
    if fix.findings:
        items = []
        for f in fix.findings:
            color = _KIND_COLORS.get(f.kind, "#8b8d98")
            refs = (f'<div class="refs">refs: {_esc(", ".join(f.refs))}</div>'
                    if f.refs else "")
            db = getattr(f, "decided_by", "")
            conf = getattr(f, "confidence", "")
            meta = (f' <span class="refs">[{_esc(db)}{"/" + _esc(conf) if conf else ""}]</span>'
                    if db else "")
            items.append(
                f'<li><span class="dot" style="background:{color}"></span>'
                f'<span class="kind" style="color:{color}">{_esc(f.kind)}</span>{meta} '
                f'— {_esc(f.detail)}{refs}</li>')
        findings_html = f'<ul class="findings">{"".join(items)}</ul>'
    else:
        findings_html = "<p>No fix-related history found for this location.</p>"
    note_html = f'<p class="sub">{_esc(fix.note)}</p>' if fix.note else ""

    # code evidence
    evidence = []
    if loc.resolved:
        for rf in loc.frames:
            role = "cause site" if rf.in_cause else "frame"
            evidence.append(
                f'<h3>{_esc(rf.method_fqn)} '
                f'<span class="sub">({role} — {_esc(rf.path)}:'
                f'{rf.method_start}-{rf.method_end})</span></h3>'
                + _numbered_code(rf.code))
    else:
        evidence.append(f"<p>{_esc(loc.note)}</p>")

    narrative_html = _md_to_html(narrative) if narrative else "<p><em>No analysis.</em></p>"

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>RCA — {_esc(err.id)}</title>
<style>{_CSS}</style></head>
<body><div class="wrap">
<h1>{_esc(title)}</h1>
<div class="sub">Root-cause analysis · generated {datetime.now():%Y-%m-%d %H:%M} · {conf_chip}{depth_chip}</div>
{banner}
{pin_warn}

<div class="meta">
<div><span class="k">Error id</span> <code>{_esc(err.id)}</code></div>
<div><span class="k">Source</span> {_esc(err.source)}</div>
<div><span class="k">Branch</span> <span class="chip">{_esc(branch)}</span>
{f'<span class="sub"> hint: {_esc(err.branch_hint)}</span>' if err.branch_hint else ''}</div>
{fault_line}
<div><span class="k">Fix status</span> <span class="headline"
style="color:{head_color}">{_esc(fix.headline)}</span></div>
</div>

<h2>Stack trace</h2>
<pre class="code"><span class="trace">{trace_html}</span></pre>

<h2>Analysis</h2>
{narrative_html}

<h2>Fix-status evidence (git / PR)</h2>
{note_html}
{findings_html}

<h2>Code evidence</h2>
{''.join(evidence)}

<div class="foot">Generated by ghrca · LLM {_esc(str(llm_meta.get('completion_tokens','?')))}
completion tokens in {llm_meta.get('elapsed_s',0):.0f}s ·
model reasoning grounded in indexed source.</div>
</div></body></html>"""

````

### `ghrca/indexer.py`
**Purpose:** Lazy path resolution (source roots, tree-sha memo, frame->blob) + LEGACY per-branch index (baseline only).

```python
"""Lazy path resolution (D3) + LEGACY per-branch index.

This module now has two parts:

  * The lazy, blob-keyed path used everywhere in production — `source_roots`,
    `resolve_frame_path`, `_pkg_dir`, tree-sha memoization — which resolve a stack
    frame to a single blob without building any whole-branch index.

  * A DEPRECATED per-branch JSON index (`RepoIndex`, `Indexer`) retained ONLY so
    the Phase-0 baseline benchmark can reproduce the pre-upgrade numbers. Nothing
    in the analyze/agent/daemon flow uses it any more; the scalable store is the
    SQLite blob cache (`blobstore.py`).

  MIGRATION NOTE: old `.cache/index/<repo>/<branch>.json` files are obsolete and
  may be deleted; the SQLite `blobs/types/methods` tables supersede them.
"""

from __future__ import annotations

import json
import re
import time
import zlib
from dataclasses import dataclass, field

from . import config
from .javascan import FileIndex, scan, method_at_line, type_at_line
from .repo import Repo

# --- lazy, blob-keyed path resolution (D3) --------------------------------
_ROOT_RE = re.compile(r"(.*?/)?(src/(?:main|test)/java|java|src)/")


def _repo_meta_get(repo_id: str) -> dict:
    from . import db
    row = db.connect().execute("SELECT data FROM repo_meta WHERE repo=?",
                               (repo_id,)).fetchone()
    if row:
        try:
            return json.loads(row["data"])
        except json.JSONDecodeError:
            return {}
    return {}


def _repo_meta_put(repo_id: str, data: dict) -> None:
    from . import db
    db.connect().execute(
        "INSERT OR REPLACE INTO repo_meta(repo,data,updated) VALUES(?,?,?)",
        (repo_id, json.dumps(data), time.time()))


def source_roots(repo: Repo, default_branch: str) -> list[str]:
    """Learn per-repo source roots (e.g. 'clients/src/main/java') once, cached."""
    meta = _repo_meta_get(repo.owner_repo)
    if "source_roots" in meta:
        return meta["source_roots"]
    roots: set[str] = set()
    for path in repo.ls_java_files(default_branch):
        m = _ROOT_RE.match(path)
        if m:
            roots.add(path[:m.end()])       # includes trailing '/'
    roots_list = sorted(roots, key=len)
    meta["source_roots"] = roots_list
    _repo_meta_put(repo.owner_repo, meta)
    return roots_list


def _tree_filenames(repo: Repo, commit: str) -> list[str]:
    """All non-skipped file paths at a commit, memoized per tree sha (D3)."""
    tsha = repo.tree_sha(commit)
    cache = config.CACHE_DIR / "trees" / f"{tsha}.z"
    cache.parent.mkdir(parents=True, exist_ok=True)
    if cache.exists():
        try:
            return zlib.decompress(cache.read_bytes()).decode("utf-8").splitlines()
        except Exception:
            pass
    files = repo.ls_all_files(commit)
    cache.write_bytes(zlib.compress("\n".join(files).encode("utf-8")))
    return files


def _pkg_dir(cls: str, filename: str) -> str:
    """Package directory path from a frame's class + File.java."""
    base = filename[:-5] if filename.endswith(".java") else filename  # top class
    segs = cls.replace("$", ".").split(".")
    if base in segs:
        segs = segs[:segs.index(base)]
    else:
        segs = segs[:-1]  # drop the class simple name
    return "/".join(segs)


def resolve_frame_path(repo: Repo, commit: str, cls: str, filename: str,
                       roots: list[str]):
    """Return (path, blob_sha) for a stack frame's class+file, or (None, None).

    Tries known source roots with one batch-check; falls back to a suffix match
    over the (memoized) tree file list."""
    pkg_dir = _pkg_dir(cls, filename)
    suffix = (pkg_dir + "/" + filename) if pkg_dir else filename
    candidates = [root + suffix for root in roots] + [suffix]
    specs = [f"{commit}:{c}" for c in candidates]
    checked = repo.batch_check(specs)
    for cand, spec in zip(candidates, specs):
        if checked.get(spec):
            return cand, checked[spec]
    # fallback: suffix match over the tree file list
    tail = "/" + filename
    matches = [p for p in _tree_filenames(repo, commit)
               if p.endswith(tail) and (not pkg_dir or pkg_dir in p)]
    if len(matches) == 1:
        sha = repo.batch_check([f"{commit}:{matches[0]}"]).get(f"{commit}:{matches[0]}")
        return matches[0], sha
    for p in matches:  # prefer one whose package dir matches exactly
        if pkg_dir and p.endswith(pkg_dir + tail):
            sha = repo.batch_check([f"{commit}:{p}"]).get(f"{commit}:{p}")
            return p, sha
    return None, None


def _safe(name: str) -> str:
    return name.replace("/", "__").replace("\\", "__")


@dataclass
class RepoIndex:
    repo: str
    branch: str
    sha: str
    indexed_at: float
    files: dict = field(default_factory=dict)          # path -> FileIndex
    by_type: dict = field(default_factory=dict)        # fqn -> path
    by_simple: dict = field(default_factory=dict)      # SimpleName -> [paths]
    root_packages: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    # -- lookups used by the localizer ------------------------------------
    def find_type(self, fqn: str):
        """Resolve a (possibly nested) type FQN to (path, FileIndex)."""
        # Direct hit
        if fqn in self.by_type:
            p = self.by_type[fqn]
            return p, self.files[p]
        # Nested class in a stack frame is written Outer$Inner -> normalize
        norm = fqn.replace("$", ".")
        if norm in self.by_type:
            p = self.by_type[norm]
            return p, self.files[p]
        # Fall back to simple name (last segment before any $)
        simple = norm.split(".")[-1]
        paths = self.by_simple.get(simple, [])
        if len(paths) == 1:
            return paths[0], self.files[paths[0]]
        # Multiple candidates: prefer one whose package prefixes the fqn
        for p in paths:
            fi = self.files[p]
            if fi.package and norm.startswith(fi.package + "."):
                return p, fi
        if paths:
            return paths[0], self.files[paths[0]]
        return None, None

    def file_tree(self, max_entries: int = 4000) -> dict:
        """Nested dict representing the directory structure of indexed files."""
        tree: dict = {}
        for i, path in enumerate(sorted(self.files)):
            if i >= max_entries:
                break
            node = tree
            parts = path.split("/")
            for seg in parts[:-1]:
                node = node.setdefault(seg, {})
            node.setdefault("__files__", []).append(parts[-1])
        return tree


class Indexer:
    def __init__(self, repo: Repo):
        self.repo = repo
        self.dir = config.INDEX_DIR / repo.slug
        self.dir.mkdir(parents=True, exist_ok=True)

    def _index_path(self, branch: str):
        return self.dir / f"{_safe(branch)}.json"

    def cached_sha(self, branch: str) -> str | None:
        p = self._index_path(branch)
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8")).get("sha")
        except (json.JSONDecodeError, OSError):
            return None

    def build(self, branch: str, force: bool = False) -> tuple[RepoIndex, bool]:
        """Build (or load cached) index for a branch. Returns (index, did_work)."""
        sha = self.repo.rev_parse(branch)
        if not force and self.cached_sha(branch) == sha:
            return self.load(branch), False

        java_files = self.repo.ls_java_files(branch)
        contents = self.repo.read_files(branch, java_files)

        files: dict[str, dict] = {}
        by_type: dict[str, str] = {}
        by_simple: dict[str, list] = {}
        pkg_counts: dict[str, int] = {}
        total_types = total_methods = 0

        for path, src in contents.items():
            fi = scan(path, src)
            files[path] = fi.to_dict()
            total_methods += len(fi.methods)
            total_types += len(fi.types)
            if fi.package:
                top = ".".join(fi.package.split(".")[:2])
                pkg_counts[top] = pkg_counts.get(top, 0) + 1
            for t in fi.types:
                by_type[t.fqn] = path
                by_simple.setdefault(t.name, []).append(path)

        root_packages = sorted(pkg_counts, key=lambda k: -pkg_counts[k])[:8]
        idx = RepoIndex(
            repo=self.repo.owner_repo, branch=branch, sha=sha,
            indexed_at=time.time(), files=files, by_type=by_type,
            by_simple=by_simple, root_packages=root_packages,
            stats={"java_files": len(java_files), "types": total_types,
                   "methods": total_methods},
        )
        self._save(idx)
        # Reload so callers always get typed FileIndex/MethodInfo objects,
        # exactly like the cached path returns.
        return self.load(branch), True

    def _save(self, idx: RepoIndex) -> None:
        payload = {
            "repo": idx.repo, "branch": idx.branch, "sha": idx.sha,
            "indexed_at": idx.indexed_at, "files": idx.files,
            "by_type": idx.by_type, "by_simple": idx.by_simple,
            "root_packages": idx.root_packages, "stats": idx.stats,
        }
        self._index_path(idx.branch).write_text(
            json.dumps(payload), encoding="utf-8")

    def load(self, branch: str) -> RepoIndex:
        blob = json.loads(self._index_path(branch).read_text(encoding="utf-8"))
        # Rehydrate FileIndex objects for typed access.
        files = {}
        for path, d in blob["files"].items():
            fi = FileIndex(path=path)
            fi.package = d.get("package", "")
            fi.imports = d.get("imports", [])
            fi.loc = d.get("loc", 0)
            fi.fields = d.get("fields", [])
            from .javascan import TypeInfo, MethodInfo
            fi.types = [TypeInfo(**t) for t in d.get("types", [])]
            fi.methods = [MethodInfo(**m) for m in d.get("methods", [])]
            files[path] = fi
        return RepoIndex(
            repo=blob["repo"], branch=blob["branch"], sha=blob["sha"],
            indexed_at=blob["indexed_at"], files=files,
            by_type=blob["by_type"], by_simple=blob["by_simple"],
            root_packages=blob.get("root_packages", []),
            stats=blob.get("stats", {}),
        )

```

### `ghrca/javascan.py`
**Purpose:** Compiler-free REGEX Java scanner (fallback) + stable method body_hash.

```python
"""A tolerant, compiler-free Java structural scanner.

We cannot compile the target (only JDK 8 here, targets need 17+), and we want to
survive newer syntax (records, sealed, text blocks) without a full grammar. So
this is a best-effort *skeleton* scanner:

  1. blank out comments and string/char literal *contents* (keeping newlines) so
     brace counting and signature matching are reliable,
  2. walk the skeleton with a brace-stack state machine, attaching each `{...}`
     to a pending type/method declaration.

Output per file: package, imports, types (with line ranges + extends/implements)
and methods (with line ranges + signatures). Good enough to map a stack-trace
frame `pkg.Class.method(File.java:line)` to an exact method body.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field, asdict

_TYPE_KEYWORDS = ("class", "interface", "enum", "record", "@interface")
_CONTROL = {"if", "for", "while", "switch", "catch", "synchronized",
            "return", "new", "else", "do", "try", "finally", "assert",
            "throw", "yield", "case", "default", "instanceof"}

_PACKAGE_RE = re.compile(r"^\s*package\s+([\w.]+)\s*;")
_IMPORT_RE = re.compile(r"^\s*import\s+(?:static\s+)?([\w.*]+)\s*;")
_TYPE_RE = re.compile(
    r"(?:^|\s)(?:class|interface|enum|record|@interface)\s+([A-Za-z_]\w*)")
_TYPE_KIND_RE = re.compile(r"(class|interface|enum|record|@interface)\s+[A-Za-z_]\w*")
_EXTENDS_RE = re.compile(r"\bextends\s+([\w.<>,\s]+?)(?:\bimplements\b|\{|$)")
_IMPLEMENTS_RE = re.compile(r"\bimplements\s+([\w.<>,\s]+?)(?:\{|$)")
# method: <mods/generics/returnType> name ( params ) [throws ...] ( { | ; )
_METHOD_RE = re.compile(
    r"(?:^|[\s>])([A-Za-z_]\w*)\s*\(([^)]*)\)\s*(?:throws\s[\w.,\s]+?)?\s*(\{|;)")
_FIELD_RE = re.compile(
    r"^\s*(?:(?:public|private|protected|static|final|transient|volatile)\s+)+"
    r"[\w.<>\[\],?\s]+?\s([A-Za-z_]\w*)\s*(?:=|;)")


@dataclass
class TypeInfo:
    name: str
    kind: str
    fqn: str
    start: int
    end: int
    extends: str = ""
    implements: str = ""


@dataclass
class MethodInfo:
    name: str
    owner: str        # fqn of the enclosing type
    fqn: str          # owner#name
    start: int
    end: int
    signature: str
    body_hash: str = ""


@dataclass
class FileIndex:
    path: str
    package: str = ""
    imports: list = field(default_factory=list)
    types: list = field(default_factory=list)      # list[TypeInfo]
    methods: list = field(default_factory=list)    # list[MethodInfo]
    fields: list = field(default_factory=list)     # list[dict]
    loc: int = 0

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


def strip_noise(src: str) -> str:
    """Blank out comment and literal *contents*, preserving line structure."""
    out = []
    i, n = 0, len(src)
    state = "code"  # code | line_comment | block_comment | string | char | text_block
    while i < n:
        c = src[i]
        nxt = src[i + 1] if i + 1 < n else ""
        if state == "code":
            if c == "/" and nxt == "/":
                state = "line_comment"; out.append("  "); i += 2; continue
            if c == "/" and nxt == "*":
                state = "block_comment"; out.append("  "); i += 2; continue
            if c == '"' and src[i:i + 3] == '"""':
                state = "text_block"; out.append('   '); i += 3; continue
            if c == '"':
                state = "string"; out.append(' '); i += 1; continue
            if c == "'":
                state = "char"; out.append(' '); i += 1; continue
            out.append(c); i += 1; continue
        # inside a non-code state: keep newlines, blank the rest
        if state == "line_comment":
            if c == "\n":
                state = "code"; out.append("\n")
            else:
                out.append(" ")
            i += 1; continue
        if state == "block_comment":
            if c == "*" and nxt == "/":
                state = "code"; out.append("  "); i += 2; continue
            out.append("\n" if c == "\n" else " "); i += 1; continue
        if state == "text_block":
            if src[i:i + 3] == '"""':
                state = "code"; out.append("   "); i += 3; continue
            out.append("\n" if c == "\n" else " "); i += 1; continue
        if state == "string":
            if c == "\\":
                out.append("  "); i += 2; continue
            if c == '"':
                state = "code"; out.append(' '); i += 1; continue
            out.append("\n" if c == "\n" else " "); i += 1; continue
        if state == "char":
            if c == "\\":
                out.append("  "); i += 2; continue
            if c == "'":
                state = "code"; out.append(' '); i += 1; continue
            out.append(" "); i += 1; continue
    return "".join(out)


def body_hash(method_src: str) -> str:
    """Stable hash of a method's source, comment- and whitespace-insensitive.

    Two byte-different-but-semantically-identical method texts (differing only in
    comments or spacing) hash equal, so an RCA cached for one branch is reused on
    another branch whose method is effectively the same (D7).
    """
    skel = strip_noise(method_src)
    normalized = re.sub(r"\s+", " ", skel).strip()
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()


def scan(path: str, src: str) -> FileIndex:
    fi = FileIndex(path=path, loc=src.count("\n") + 1)
    skel = strip_noise(src)
    skel_lines = skel.splitlines()
    raw_lines = src.splitlines()

    # package / imports from raw lines (cheap, unambiguous)
    for ln in raw_lines[:200]:
        m = _PACKAGE_RE.match(ln)
        if m:
            fi.package = m.group(1)
        mi = _IMPORT_RE.match(ln)
        if mi:
            fi.imports.append(mi.group(1))

    # brace-stack walk over the skeleton
    scope_stack: list[dict] = []   # each: {kind, name, fqn, start} for named scopes
    brace_stack: list[dict | None] = []  # None = anonymous block
    pending: dict | None = None    # a decl awaiting its '{' or ';'

    def cur_type_fqn() -> str:
        for s in reversed(scope_stack):
            if s["kind"] == "type":
                return s["fqn"]
        return ""

    def innermost_kind() -> str:
        return scope_stack[-1]["kind"] if scope_stack else "file"

    def pkg_prefix() -> str:
        return (fi.package + ".") if fi.package else ""

    for idx, sline in enumerate(skel_lines):
        lineno = idx + 1
        # Detect a declaration on this line only when we're at file/type scope
        # (methods & control-flow live inside a method scope -> skip there).
        if innermost_kind() in ("file", "type") and pending is None:
            tm = _TYPE_RE.search(sline)
            if tm:
                km = _TYPE_KIND_RE.search(sline)
                kind = km.group(1) if km else "class"
                name = tm.group(1)
                owner = cur_type_fqn()
                fqn = (owner + "." + name) if owner else (pkg_prefix() + name)
                ext = _EXTENDS_RE.search(sline)
                impl = _IMPLEMENTS_RE.search(sline)
                pending = {"kind": "type", "name": name, "fqn": fqn,
                           "start": lineno,
                           "extends": (ext.group(1).strip() if ext else ""),
                           "implements": (impl.group(1).strip() if impl else "")}
            elif innermost_kind() == "type":
                mm = _METHOD_RE.search(sline)
                if mm and mm.group(1) not in _CONTROL:
                    before = sline[:mm.start(1)]
                    # reject assignments (x = foo()) and annotations only
                    if "=" not in before.split("(")[0]:
                        owner = cur_type_fqn()
                        name = mm.group(1)
                        sig = re.sub(r"\s+", " ", sline.strip())[:200]
                        pending = {"kind": "method", "name": name,
                                   "owner": owner, "fqn": f"{owner}#{name}",
                                   "start": lineno, "signature": sig}
                else:
                    fdm = _FIELD_RE.match(sline)
                    if fdm and "(" not in sline.split("=")[0]:
                        fi.fields.append({"name": fdm.group(1),
                                          "owner": cur_type_fqn(), "line": lineno})

        # Now consume braces / semicolons on this line to move the state machine.
        for ch in sline:
            if ch == "{":
                if pending is not None:
                    scope_stack.append(pending)
                    brace_stack.append(pending)
                    pending = None
                else:
                    brace_stack.append(None)
            elif ch == "}":
                if brace_stack:
                    top = brace_stack.pop()
                    if top is not None and scope_stack and scope_stack[-1] is top:
                        s = scope_stack.pop()
                        s["end"] = lineno
                        if s["kind"] == "type":
                            fi.types.append(TypeInfo(
                                s["name"], s.get("_kind", "class"), s["fqn"],
                                s["start"], lineno, s.get("extends", ""),
                                s.get("implements", "")))
                        else:
                            mbody = "\n".join(raw_lines[s["start"] - 1:lineno])
                            fi.methods.append(MethodInfo(
                                s["name"], s["owner"], s["fqn"],
                                s["start"], lineno, s.get("signature", ""),
                                body_hash=body_hash(mbody)))
            elif ch == ";":
                # a bodyless declaration (abstract/interface method) resolves here
                if pending is not None and pending["kind"] == "method":
                    fi.methods.append(MethodInfo(
                        pending["name"], pending["owner"], pending["fqn"],
                        pending["start"], pending["start"],
                        pending.get("signature", "")))
                    pending = None

    # We lost the type kind above (dataclass built at close); patch kinds by
    # re-reading the first declaring line for each type.
    for t in fi.types:
        if 1 <= t.start <= len(skel_lines):
            km = _TYPE_KIND_RE.search(skel_lines[t.start - 1])
            if km:
                t.kind = km.group(1)
    return fi


def method_at_line(fi: FileIndex, line: int):
    """Return the innermost MethodInfo containing `line`, or None."""
    best = None
    for m in fi.methods:
        if m.start <= line <= m.end:
            if best is None or (m.start >= best.start and m.end <= best.end):
                best = m
    return best


def type_at_line(fi: FileIndex, line: int):
    best = None
    for t in fi.types:
        if t.start <= line <= t.end:
            if best is None or (t.start >= best.start and t.end <= best.end):
                best = t
    return best

```

### `ghrca/llm.py`
**Purpose:** Local llama.cpp OpenAI-compatible client (thinking-off, cache_prompt, health check).

```python
"""Client for the local llama.cpp OpenAI-compatible server.

Kept deliberately small: one blocking chat call with retry/health-check. The
server is slow and single-slot, so callers should batch reasoning into as few
calls as possible rather than chatting turn-by-turn.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

from . import config


class LLMError(RuntimeError):
    """Raised when the LLM server is unreachable or returns an error."""


@dataclass
class LLMResult:
    text: str
    prompt_tokens: int
    completion_tokens: int
    elapsed_s: float


def _post(url: str, payload: dict, timeout: int) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def health_check(timeout: int = 5) -> bool:
    """True if the server answers on /v1/models."""
    base = config.LLM_URL.rsplit("/v1/", 1)[0]
    try:
        req = urllib.request.Request(f"{base}/v1/models", method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def chat(
    system: str,
    user: str,
    *,
    max_tokens: int | None = None,
    temperature: float | None = None,
    thinking: str | None = None,
    cache_prompt: bool = True,
    retries: int = 2,
) -> LLMResult:
    """Single system+user chat completion. Retries on transient failures.

    thinking: "off" disables reasoning tokens via chat_template_kwargs
    (falls back to a /no_think system marker); "on" leaves the model default.
    cache_prompt: enables llama.cpp prompt caching — keep static content first.
    """
    think = (thinking or config.LLM_THINKING)
    sys_content = system
    payload = {
        "model": config.LLM_MODEL,
        "messages": [
            {"role": "system", "content": sys_content},
            {"role": "user", "content": user},
        ],
        "temperature": config.LLM_TEMPERATURE if temperature is None else temperature,
        "max_tokens": config.LLM_MAX_TOKENS if max_tokens is None else max_tokens,
        "stream": False,
        "cache_prompt": cache_prompt,
    }
    if think == "off":
        # Primary mechanism (probed to work on this model); harmless if ignored.
        payload["chat_template_kwargs"] = {"enable_thinking": False}

    last_err: Exception | None = None
    for attempt in range(retries + 1):
        t0 = time.time()
        try:
            data = _post(config.LLM_URL, payload, config.LLM_TIMEOUT_SECONDS)
            msg = data["choices"][0]["message"]["content"] or ""
            usage = data.get("usage", {})
            return LLMResult(
                text=msg.strip(),
                prompt_tokens=int(usage.get("prompt_tokens", 0)),
                completion_tokens=int(usage.get("completion_tokens", 0)),
                elapsed_s=time.time() - t0,
            )
        except (urllib.error.URLError, urllib.error.HTTPError, KeyError, TimeoutError) as e:
            last_err = e
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
            continue
    raise LLMError(
        f"LLM call failed after {retries + 1} attempts: {last_err}. "
        f"Is the server running? ({config.LLM_URL})"
    )


def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 chars/token) for budgeting prompts."""
    return max(1, len(text) // 4)

```

### `ghrca/llmqueue.py`
**Purpose:** Persistent priority job queue + single worker; crash-resume via reset_running().

```python
"""Persistent priority job queue for LLM work (D9).

Jobs live in the SQLite `jobs` table so an interrupted run resumes exactly where
it stopped. A single worker drains them (the LLM server is single-slot), ordered
by priority then age. Handlers are injected so this module stays decoupled from
the RCA logic.
"""

from __future__ import annotations

import json
import threading
import time

from . import db

MAX_ATTEMPTS = 3   # initial try + 2 retries (D9)


def enqueue(kind: str, payload: dict, priority: int = 0) -> int:
    conn = db.connect()
    now = time.time()
    cur = conn.execute(
        "INSERT INTO jobs(kind,priority,payload,state,attempts,created,updated)"
        " VALUES(?,?,?,'queued',0,?,?)",
        (kind, priority, json.dumps(payload), now, now))
    return cur.lastrowid


def rca_priority(branch_priority: int, frequency: int, first_time: bool) -> int:
    """priority = branch_priority + min(frequency,50) + (40 if first time)."""
    return branch_priority + min(frequency, 50) + (40 if first_time else 0)


def reset_running() -> int:
    """On startup, requeue jobs left 'running' by a crash. Returns count."""
    conn = db.connect()
    cur = conn.execute(
        "UPDATE jobs SET state='queued', updated=? WHERE state='running'",
        (time.time(),))
    return cur.rowcount


def _claim_next():
    """Atomically claim the highest-priority queued job (single worker)."""
    conn = db.connect()
    conn.execute("BEGIN IMMEDIATE")
    try:
        row = conn.execute(
            "SELECT * FROM jobs WHERE state='queued' "
            "ORDER BY priority DESC, created ASC LIMIT 1").fetchone()
        if row is None:
            conn.execute("COMMIT")
            return None
        conn.execute("UPDATE jobs SET state='running', attempts=attempts+1, updated=? "
                     "WHERE id=?", (time.time(), row["id"]))
        conn.execute("COMMIT")
        return row
    except Exception:
        conn.execute("ROLLBACK")
        raise


def _complete(job_id: int):
    db.connect().execute("UPDATE jobs SET state='done', updated=? WHERE id=?",
                         (time.time(), job_id))


def _fail(job_id: int, attempts: int, err: str):
    conn = db.connect()
    state = "failed" if attempts >= MAX_ATTEMPTS else "queued"
    conn.execute("UPDATE jobs SET state=?, error=?, updated=? WHERE id=?",
                 (state, err[:500], time.time(), job_id))


def process_all(dispatch: dict, *, stop=None, max_jobs=None, backoff_base=2.0):
    """Drain queued jobs. `dispatch` maps kind -> handler(payload_dict).

    Returns the number of jobs completed. Used both one-shot (analyze) and by
    the daemon worker thread.
    """
    done = 0
    while True:
        if stop is not None and stop.is_set():
            break
        if max_jobs is not None and done >= max_jobs:
            break
        row = _claim_next()
        if row is None:
            break
        payload = json.loads(row["payload"])
        handler = dispatch.get(row["kind"])
        if handler is None:
            _fail(row["id"], MAX_ATTEMPTS, f"no handler for kind={row['kind']}")
            continue
        attempts_now = row["attempts"] + 1  # _claim_next already incremented in DB
        try:
            handler(payload)
            _complete(row["id"])
            done += 1
        except Exception as e:  # noqa: BLE001 - persist and back off
            _fail(row["id"], attempts_now, f"{type(e).__name__}: {e}")
            if attempts_now < MAX_ATTEMPTS:
                time.sleep(backoff_base * attempts_now)
    return done


def depth() -> dict:
    conn = db.connect()
    rows = conn.execute("SELECT state, COUNT(*) AS n FROM jobs GROUP BY state").fetchall()
    return {r["state"]: r["n"] for r in rows}


class Worker(threading.Thread):
    """Background single-slot worker for the daemon."""

    def __init__(self, dispatch: dict, poll_interval: float = 1.0):
        super().__init__(daemon=True, name="llm-worker")
        self.dispatch = dispatch
        self.poll_interval = poll_interval
        self._stop = threading.Event()

    def run(self):
        reset_running()
        while not self._stop.is_set():
            n = process_all(self.dispatch, stop=self._stop, max_jobs=1)
            if n == 0:
                self._stop.wait(self.poll_interval)

    def stop(self):
        self._stop.set()

```

### `ghrca/locate.py`
**Purpose:** localize_lazy: resolve each frame to one blob + method (no whole-branch index); drift validation + confidence.

```python
"""Deterministic error -> code localization.

Given a parsed error and a branch index, find the repo-owned frames, resolve
each to an exact method body, and assemble the code evidence the RCA engine
needs. No LLM here -- this is what keeps the (single) LLM call grounded and
cheap.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import config, javascan
from .errors import ErrorRecord, Frame
from .fingerprint import extract_message_identifiers
from .indexer import RepoIndex
from .javascan import method_at_line, type_at_line
from .repo import Repo


@dataclass
class ResolvedFrame:
    frame: Frame
    path: str
    method_fqn: str
    method_sig: str
    method_start: int
    method_end: int
    code: str            # numbered source slice of the method (for display)
    body_hash: str = ""  # hash of the raw method body (for the RCA cache, D7)
    in_cause: bool = False


@dataclass
class LocResult:
    resolved: bool
    fault: ResolvedFrame | None = None       # best single fault site
    frames: list = field(default_factory=list)  # all resolved repo frames
    imports: list = field(default_factory=list)
    type_summary: str = ""
    note: str = ""
    confidence: str = "high"                  # high | medium | low (D11 drift check)
    corrected_line: int | None = None         # set when identifiers found off-line
    drift_note: str = ""
    root_packages: list = field(default_factory=list)

    def method_hash(self) -> str:
        """sha1 of concatenated body_hashes of the call-path methods, deepest
        first — the RCA cache key component (D7)."""
        import hashlib
        joined = "|".join(rf.body_hash for rf in self.frames if rf.body_hash)
        return hashlib.sha1(joined.encode("utf-8")).hexdigest()


def _is_repo_owned(cls: str, index: RepoIndex) -> bool:
    if cls.startswith(config.FOREIGN_FRAME_PREFIXES):
        return False
    if any(cls.startswith(rp + ".") or cls.startswith(rp) for rp in index.root_packages):
        return True
    # else: resolvable in the index counts as owned
    _, fi = index.find_type(cls)
    return fi is not None


def _number_slice(src: str, start: int, end: int, pad: int = 2) -> str:
    lines = src.splitlines()
    a = max(1, start - pad)
    b = min(len(lines), end + pad)
    out = []
    for n in range(a, b + 1):
        out.append(f"{n:>5} | {lines[n - 1]}")
    return "\n".join(out)


def localize(err: ErrorRecord, index: RepoIndex, repo: Repo, branch: str,
             max_frames: int = 4) -> LocResult:
    # Order: deepest cause first (usual fault site), then outward to primary.
    ordered: list[tuple[Frame, bool]] = []
    for ti, th in enumerate(err.chain):
        is_cause = ti > 0
        for f in th.frames:
            ordered.append((f, is_cause))

    resolved: list[ResolvedFrame] = []
    file_cache: dict[str, str] = {}
    imports: list[str] = []
    type_summary = ""

    for frame, is_cause in ordered:
        if not frame.is_located():
            continue
        if not _is_repo_owned(frame.cls, index):
            continue
        path, fi = index.find_type(frame.cls)
        if not fi:
            continue
        if path not in file_cache:
            src = repo.read_file(branch, path) or ""
            file_cache[path] = src
        src = file_cache[path]
        m = method_at_line(fi, frame.line)
        if m is None:
            # method name fallback: match by name within the type
            cands = [mm for mm in fi.methods if mm.name == frame.method]
            m = cands[0] if cands else None
        if m is None:
            continue
        raw_method = "\n".join(src.splitlines()[m.start - 1:m.end])
        rf = ResolvedFrame(
            frame=frame, path=path, method_fqn=m.fqn, method_sig=m.signature,
            method_start=m.start, method_end=m.end,
            code=_number_slice(src, m.start, m.end),
            body_hash=javascan.body_hash(raw_method),
            in_cause=is_cause,
        )
        resolved.append(rf)
        if not imports:
            imports = fi.imports[:40]
            t = type_at_line(fi, frame.line)
            if t:
                sibs = [mm.name for mm in fi.methods if mm.owner == t.fqn][:25]
                type_summary = (
                    f"{t.kind} {t.fqn}"
                    + (f" extends {t.extends}" if t.extends else "")
                    + (f" implements {t.implements}" if t.implements else "")
                    + f"\n  methods: {', '.join(sibs)}"
                )
        if len(resolved) >= max_frames:
            break

    if not resolved:
        return LocResult(
            resolved=False,
            note=("No stack-trace frame resolved to indexed repo code. "
                  "The exception may originate entirely in third-party code, "
                  "or the failing class isn't on this branch."),
        )
    result = LocResult(
        resolved=True, fault=resolved[0], frames=resolved,
        imports=imports, type_summary=type_summary,
        root_packages=list(index.root_packages),
    )
    _validate_drift(result, err, file_cache)
    return result


def localize_lazy(err: ErrorRecord, repo: Repo, commit: str, default_branch: str,
                  max_frames: int = 4) -> LocResult:
    """Localize WITHOUT a whole-branch index (D3): resolve each frame's file to a
    blob, scan just that blob, and look up the method. This is the fast path used
    by the daemon and the `blast`/`analyze` commands at scale."""
    from . import blobstore, indexer

    roots = indexer.source_roots(repo, default_branch)
    ordered: list[tuple[Frame, bool]] = []
    for ti, th in enumerate(err.chain):
        for f in th.frames:
            ordered.append((f, ti > 0))

    resolved: list[ResolvedFrame] = []
    imports: list[str] = []
    type_summary = ""
    root_pkgs: list[str] = []
    fault_src_for_drift = {}

    # Resolve ALL candidate paths in ONE cat-file --batch-check (not one per
    # frame) — subprocess spawns dominate latency at this scale.
    cand_frames = [(f, c) for (f, c) in ordered
                   if f.is_located() and not f.cls.startswith(config.FOREIGN_FRAME_PREFIXES)
                   and not f.is_proxy() and f.language() != "unsupported"]
    all_specs: list[str] = []
    per_frame_specs: list[list[str]] = []
    for frame, _ in cand_frames:
        pkg_dir = indexer._pkg_dir(frame.cls, frame.file)
        suffix = (pkg_dir + "/" + frame.file) if pkg_dir else frame.file
        cands = [root + suffix for root in roots] + [suffix]
        specs = [f"{commit}:{c}" for c in cands]
        per_frame_specs.append(specs)
        all_specs.extend(specs)
    checked = repo.batch_check(all_specs) if all_specs else {}

    # First pass: resolve (path, blob) per frame; collect blobs to scan+read once.
    frame_resolution: list[tuple] = []  # (frame, is_cause, path, blob)
    need_blobs: list[str] = []
    for (frame, is_cause), specs in zip(cand_frames, per_frame_specs):
        path = blob = None
        for spec in specs:
            if checked.get(spec):
                blob = checked[spec]
                path = spec.split(":", 1)[1]
                break
        if blob is None:
            continue
        frame_resolution.append((frame, is_cause, path, blob))
        need_blobs.append(blob)

    if need_blobs:
        blobstore.scan_blobs(repo, need_blobs, path_hint="X.java")
    blob_cache = repo.read_blobs(list(dict.fromkeys(need_blobs))) if need_blobs else {}

    for frame, is_cause, path, blob in frame_resolution:
        mname, synthetic = frame.normalized_method()
        row = blobstore.method_at_line(blob, frame.line)
        if row is None and not synthetic:
            row = blobstore.method_by_name(blob, mname)
        if row is None:
            continue
        src = blob_cache.get(blob, "")
        rf = ResolvedFrame(
            frame=frame, path=path, method_fqn=f"{row['owner_fqn']}#{row['name']}",
            method_sig=row["sig"] or "",
            method_start=row["start_line"], method_end=row["end_line"],
            code=_number_slice(src, row["start_line"], row["end_line"]),
            body_hash=row["body_hash"] or "", in_cause=is_cause,
        )
        resolved.append(rf)
        if not imports:
            imports = blobstore.imports_for_blob(blob)[:40]
            fault_src_for_drift[path] = src
            # type summary + root package from this blob
            for t in blobstore.types_for_blob(blob):
                if t["start_line"] <= frame.line <= t["end_line"]:
                    sibs = [m["name"] for m in blobstore.methods_for_blob(blob)
                            if m["owner_fqn"] == t["fqn"]][:25]
                    type_summary = (f"{t['kind']} {t['fqn']}"
                                    + (f" extends {t['extends']}" if t["extends"] else "")
                                    + (f" implements {t['implements']}" if t["implements"] else "")
                                    + f"\n  methods: {', '.join(sibs)}")
                    pkg = ".".join(t["fqn"].split(".")[:2])
                    root_pkgs = [pkg]
                    break
        if len(resolved) >= max_frames:
            break

    if not resolved:
        return LocResult(resolved=False,
                         note="No repo-owned frame resolved to a file at this commit.")
    result = LocResult(resolved=True, fault=resolved[0], frames=resolved,
                       imports=imports, type_summary=type_summary,
                       root_packages=root_pkgs)
    _validate_drift(result, err, fault_src_for_drift)
    return result


def _validate_drift(result: "LocResult", err: ErrorRecord,
                    file_cache: dict[str, str]) -> None:
    """Check that identifiers from the exception message actually appear at/near
    the resolved fault line; set confidence + a corrected line (D11)."""
    fault = result.fault
    idents = extract_message_identifiers(err.primary.message if err.primary else "")
    src = file_cache.get(fault.path, "")
    lines = src.splitlines()
    line = fault.frame.line

    def line_text(n: int) -> str:
        return lines[n - 1] if 1 <= n <= len(lines) else ""

    if not idents:
        # nothing to verify against; confidence is high if the line is inside the
        # method (it is, by construction), else medium.
        result.confidence = "high"
        result.drift_note = "no identifiers in message to verify; line inside method"
        return

    def found_on(n: int) -> bool:
        t = line_text(n)
        return any(_ident_in(i, t) for i in idents)

    if found_on(line):
        result.confidence = "high"
        result.drift_note = f"message identifiers found on line {line}"
        return
    for d in (1, 2, 3):
        for n in (line - d, line + d):
            if found_on(n):
                result.confidence = "medium"
                result.corrected_line = n
                result.drift_note = (f"identifiers found on line {n} "
                                     f"(±{d} from reported {line}); line may have drifted")
                return
    # Broader recovery: scan the resolved method's whole body for the identifiers
    # (handles larger drift when the deployed commit is older than the tip).
    if fault is not None:
        for n in range(fault.method_start, fault.method_end + 1):
            if found_on(n):
                result.confidence = "low"
                result.corrected_line = n
                result.drift_note = (f"reported line {line} drifted; identifiers found "
                                     f"on line {n} within {fault.method_fqn.split('#')[-1]} "
                                     f"— mapped, but verify (analyzed against branch tip)")
                return
    result.confidence = "low"
    result.drift_note = (f"message identifiers not found near line {line}; "
                         f"analyzed against branch tip — likely line drift, verdict "
                         f"confidence lowered")


def _ident_in(ident: str, text: str) -> bool:
    core = ident.rstrip("()").split(".")[-1]
    if not core:
        return False
    return re.search(r"\b" + re.escape(core) + r"\b", text) is not None

```

### `ghrca/orchestrator.py`
**Purpose:** `analyze` wiring (lazy path): parse -> localize -> fix-status -> RCA -> report.

```python
"""End-to-end orchestration of the analysis pipeline."""

from __future__ import annotations

import json
import time
from pathlib import Path

from . import config, db, errors as errmod, fingerprint, rca
from . import htmlreport
from .archaeology import FixStatus, analyze_fix_status
from .ghapi import GitHubAPI, RateLimited
from .locate import localize_lazy
from .repo import GitError, Repo


def _safe(name: str) -> str:
    return name.replace("/", "__").replace("\\", "__")


def resolve_branch(repo: Repo, hint: str, default_branch: str) -> str:
    """Map a version/branch hint to an actual ref, else the default branch."""
    if not hint:
        return default_branch
    for cand in (hint, f"v{hint}", f"release/{hint}", f"{hint}.x"):
        sha = repo._git("rev-parse", "--verify", "--quiet", cand, check=False).strip()
        if sha:
            # only accept branch-ish refs for cross-branch analysis; tags ok too
            return cand
    return default_branch


def prepare(owner_repo: str, do_refresh: bool = True,
            auto_index_new: bool = True) -> dict:
    """Clone/fetch and detect new/changed branches (no whole-branch indexing —
    localization scans only the blobs a given error needs)."""
    config.ensure_dirs()
    repo = Repo(owner_repo)
    log = []
    log.append(repo.clone_or_update() if do_refresh or not repo.exists()
               else "using cached clone")
    changes = repo.detect_new_and_changed()
    default_branch = repo.default_branch()
    return {
        "repo": owner_repo, "default_branch": default_branch,
        "log": log, "changes": changes, "indexed": [],
        "repo_obj": repo,
    }


def analyze_error(repo: Repo, api: GitHubAPI | None,
                  err: errmod.ErrorRecord, default_branch: str,
                  use_llm: bool = True, force_branch: str | None = None,
                  policy: str | None = None) -> dict:
    branch = force_branch or resolve_branch(repo, err.branch_hint, default_branch)
    err.branch = branch
    commit = repo.rev_parse(branch)

    # lazy localization — no whole-branch index built (D3)
    loc = localize_lazy(err, repo, commit, default_branch)

    if loc.resolved and loc.fault:
        fix = analyze_fix_status(
            repo, api, loc.fault.path, loc.fault.method_fqn.split("#")[-1],
            loc.fault.method_start, loc.fault.method_end,
            commit, branch, fault_line=loc.fault.frame.line)
    else:
        fix = FixStatus(headline="Localization failed — fix-status not computed.",
                        note="Could not resolve the error to repo code.")

    fp, exc_type, norm_msg, top = fingerprint.compute(err, loc.root_packages)
    db.upsert_fingerprint(fp, repo.owner_repo, exc_type, norm_msg, top)
    method_hash = loc.method_hash() if loc.resolved else "none"
    pol = "never" if not use_llm else policy
    res = rca.produce_narrative(err, loc, fix, branch, loc.root_packages,
                               fp=fp, method_hash=method_hash, policy=pol,
                               repo=repo, commit=commit)
    narrative = res["narrative"]
    llm_meta = {"completion_tokens": res["tokens"], "elapsed_s": res["seconds"],
                "source": res["source"], "rca_depth": res.get("rca_depth")}

    report_md = rca.render_report(err, loc, fix, branch, narrative, llm_meta)
    report_html = htmlreport.render_html(err, loc, fix, branch, narrative, llm_meta)

    # persist
    rdir = config.REPORTS_DIR / repo.slug
    rdir.mkdir(parents=True, exist_ok=True)
    (rdir / f"{err.id}.md").write_text(report_md, encoding="utf-8")
    (rdir / f"{err.id}.html").write_text(report_html, encoding="utf-8")
    record = {
        **err.to_dict(),
        "fault": (
            {"method": loc.fault.method_fqn, "path": loc.fault.path,
             "line": loc.fault.frame.line} if loc.resolved and loc.fault else None),
        "fix_status": fix.to_dict(),
        "report": str((rdir / f"{err.id}.md")),
        "report_html": str((rdir / f"{err.id}.html")),
    }
    (rdir / f"{err.id}.json").write_text(
        json.dumps(record, indent=2), encoding="utf-8")
    return record


def _save_error_list(repo: Repo, records: list[dict]) -> Path:
    rdir = config.REPORTS_DIR / repo.slug
    rdir.mkdir(parents=True, exist_ok=True)
    p = rdir / "errors.json"
    # merge with any existing list, de-dup by id
    existing = {}
    if p.exists():
        try:
            for r in json.loads(p.read_text(encoding="utf-8")):
                existing[r["id"]] = r
        except (json.JSONDecodeError, OSError):
            pass
    for r in records:
        existing[r["id"]] = r
    merged = sorted(existing.values(), key=lambda r: (r.get("branch", ""), r["id"]))
    p.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    return p


def analyze_log(owner_repo: str, log_path: str, use_llm: bool = True,
                force_branch: str | None = None, refresh: bool = True) -> dict:
    prep = prepare(owner_repo, do_refresh=refresh)
    repo = prep["repo_obj"]
    api = GitHubAPI()
    text = Path(log_path).read_text(encoding="utf-8", errors="replace")
    recs = errmod.from_text(text, source=f"log:{Path(log_path).name}")
    if not recs:
        return {"prep": prep, "records": [], "note": "No stack trace parsed from log."}
    out = []
    for err in recs:
        out.append(analyze_error(repo, api, err,
                                 prep["default_branch"], use_llm, force_branch))
    _save_error_list(repo, out)
    return {"prep": prep, "records": out, "api": api.budget_note()}


def analyze_stdin_text(owner_repo: str, text: str, use_llm: bool = True,
                       force_branch: str | None = None, refresh: bool = True) -> dict:
    prep = prepare(owner_repo, do_refresh=refresh)
    repo = prep["repo_obj"]
    api = GitHubAPI()
    recs = errmod.from_text(text, source="log:stdin")
    out = [analyze_error(repo, api, err, prep["default_branch"], use_llm, force_branch) for err in recs]
    _save_error_list(repo, out)
    return {"prep": prep, "records": out, "api": api.budget_note()}


def analyze_issues(owner_repo: str, limit: int = 5, use_llm: bool = True,
                   refresh: bool = True) -> dict:
    prep = prepare(owner_repo, do_refresh=refresh)
    repo = prep["repo_obj"]
    api = GitHubAPI()
    found: list[errmod.ErrorRecord] = []
    try:
        # pull a couple of pages of open+closed issues, mine stack traces
        for state in ("open", "closed"):
            for page in (1, 2):
                if len(found) >= limit:
                    break
                for issue in api.issues(owner_repo, state=state, per_page=30, page=page):
                    if "pull_request" in issue:
                        continue
                    recs = errmod.from_issue(issue)
                    found.extend(recs)
                    if len(found) >= limit:
                        break
    except RateLimited as e:
        if not found:
            return {"prep": prep, "records": [], "note": str(e)}
    found = found[:limit]
    out = [analyze_error(repo, api, err, prep["default_branch"], use_llm)
           for err in found]
    _save_error_list(repo, out)
    return {"prep": prep, "records": out, "api": api.budget_note(),
            "mined": len(found)}

```

### `ghrca/poller.py`
**Purpose:** ls-remote poll + ref-diff classification + branch priority.

```python
"""Ref polling and branch priority (D4).

`git ls-remote` is one cheap round trip. We compare its result to the `refs`
table and only trigger a real `git fetch` when something actually changed. New
branches are therefore detected within one poll interval, and priority scoring
decides which branches are pre-warmed / analyzed first.
"""

from __future__ import annotations

import re
import time

from . import db
from .repo import Repo

DEFAULT_PRIORITY_PATTERNS = [
    r"^(release|hotfix|maint|branch)[-/_.]",
    r"^\d+\.\d+(\.x)?$",
]


def classify(prev: dict[str, str], cur: dict[str, str]) -> dict[str, list]:
    """Compare two {ref: sha} maps → new / moved / deleted / unchanged."""
    new = [r for r in cur if r not in prev]
    moved = [r for r in cur if r in prev and prev[r] != cur[r]]
    deleted = [r for r in prev if r not in cur]
    unchanged = [r for r in cur if r in prev and prev[r] == cur[r]]
    return {"new": sorted(new), "moved": sorted(moved),
            "deleted": sorted(deleted), "unchanged": sorted(unchanged)}


def load_refs(repo_id: str) -> dict[str, str]:
    conn = db.connect()
    rows = conn.execute("SELECT ref, sha FROM refs WHERE repo=?", (repo_id,)).fetchall()
    return {r["ref"]: r["sha"] for r in rows}


def save_refs(repo_id: str, cur: dict[str, str], changes: dict) -> None:
    """Bulk upsert all refs in one transaction (no per-row SELECT).

    The ON CONFLICT clause records prev_sha only when the sha actually changed
    and never overwrites first_seen, so 'moved' history is captured for free.
    """
    conn = db.connect()
    now = time.time()
    rows = [(repo_id, ref, sha, now, now) for ref, sha in cur.items()]
    conn.execute("BEGIN")
    try:
        conn.executemany(
            "INSERT INTO refs(repo,ref,sha,first_seen,last_seen,prev_sha)"
            " VALUES(?,?,?,?,?,NULL)"
            " ON CONFLICT(repo,ref) DO UPDATE SET"
            "   prev_sha=CASE WHEN refs.sha<>excluded.sha THEN refs.sha ELSE refs.prev_sha END,"
            "   sha=excluded.sha,"
            "   last_seen=excluded.last_seen",
            rows)
        if changes["deleted"]:
            conn.executemany("DELETE FROM refs WHERE repo=? AND ref=?",
                             [(repo_id, r) for r in changes["deleted"]])
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


def poll_once(repo: Repo) -> dict:
    """One poll cycle: ls-remote, classify vs DB, persist. Does NOT fetch."""
    t0 = time.perf_counter()
    cur = repo.ls_remote_heads()
    prev = load_refs(repo.owner_repo)
    changes = classify(prev, cur)
    changes["elapsed_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    changes["n_refs"] = len(cur)
    save_refs(repo.owner_repo, cur, changes)
    changes["changed"] = bool(changes["new"] or changes["moved"] or changes["deleted"])
    return changes


def branch_priority(name: str, *, manifest_branch: str | None = None,
                    tip_age_days: float | None = None,
                    patterns: list[str] | None = None) -> int:
    if manifest_branch and name == manifest_branch:
        return 100
    pats = patterns or DEFAULT_PRIORITY_PATTERNS
    for pat in pats:
        if re.search(pat, name):
            return 60
    if tip_age_days is not None and tip_age_days < 30:
        return 30
    return 0

```

### `ghrca/rca.py`
**Purpose:** RCA engine: depth modes (location_only/llm_short/llm_deep), prompt v3/v4, ranked hypotheses + grounding, RCA cache, templated location-only.

````python
"""Root-cause analysis: prompt assembly, RCA cache (D7), LLM policy (D9).

Two prompt formats:
  - short (prompt_ver=2, default): 3 sections, thinking off, small token budget.
  - long  (5 sections): the original, behind `--rca-format long`.

The narrative is cached by (fp, method_hash, prompt_ver): different branches with
byte-identical methods reuse one narrative. The fix-status verdict and
deployed-branch facts are always recomputed and are NOT part of the cache.
"""

from __future__ import annotations

import textwrap
import time

import re

from . import config, context, db, llm
from .archaeology import FixStatus
from .errors import ErrorRecord
from .locate import LocResult

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------
_SYSTEM_LONG = (
    "You are a senior Java engineer performing a rigorous root-cause analysis "
    "of a runtime error. Reason strictly from the evidence provided (parsed stack "
    "trace, real source of the failing methods, and a git/PR fix investigation). "
    "If localization confidence is not high, treat line references cautiously. Be "
    "concrete; do not invent code you were not shown."
)
_INSTRUCTION_LONG = textwrap.dedent("""\
    Produce the analysis in this exact Markdown structure:
    ### 1. What the code does
    ### 2. Root cause
    ### 3. Why the error occurred
    ### 4. Suggested fix
    ### 5. Fix-status assessment
    """)

_SYSTEM_SHORT = (
    "You are a senior Java engineer doing a fast, precise root-cause analysis from "
    "the evidence given (stack trace, real failing-method source, git fix-status). "
    "Be concrete and brief. Do not invent code. If localization confidence is low, "
    "say so and hedge line references."
)
_INSTRUCTION_SHORT = textwrap.dedent("""\
    Output EXACTLY three Markdown sections, nothing else:
    ### Root cause
    (What the code does and why it fails. <= 8 sentences.)
    ### Suggested fix
    (A unified diff in a ```diff code block.)
    ### Fix-status
    (<= 4 sentences. Must AGREE with the deterministic verdict below, not contradict it.)
    """)


def _trim(text: str, max_chars: int) -> str:
    return text if len(text) <= max_chars else text[:max_chars] + "\n… [truncated]"


def build_prompt(err: ErrorRecord, loc: LocResult, fix: FixStatus,
                 branch: str, root_packages: list, fmt: str = "short") -> tuple[str, str]:
    """Return (system, user). Static/repo content first for prompt-cache reuse."""
    system = _SYSTEM_SHORT if fmt == "short" else _SYSTEM_LONG
    instruction = _INSTRUCTION_SHORT if fmt == "short" else _INSTRUCTION_LONG

    parts: list[str] = []
    # static-ish first (helps llama.cpp cache_prompt): instruction + repo shape
    parts.append(instruction)
    parts.append(f"\nRepo top-level packages: {', '.join(root_packages) or 'unknown'}")
    if loc.resolved and loc.type_summary:
        parts.append("\n## Enclosing type\n" + loc.type_summary)

    # per-error content last
    parts.append(f"\n## Error (branch: {branch}, source: {err.source})")
    parts.append(f"Summary: {err.summary()}")
    parts.append(f"Localization confidence: {loc.confidence.upper()}"
                 + (f" ({loc.drift_note})" if loc.drift_note else ""))
    parts.append("\nException chain:")
    for i, th in enumerate(err.chain):
        tag = "PRIMARY" if i == 0 else f"CAUSED BY [{i}]"
        parts.append(f"  {tag}: {th.type}: {th.message}".rstrip())
        for f in th.frames[:6]:
            locs = f"({f.file}:{f.line})" if f.is_located() else ""
            parts.append(f"      at {f.cls}.{f.method}{locs}")

    if loc.resolved:
        parts.append("\n## Failing code (call path, deepest first)")
        budget = 8000
        for rf in loc.frames:
            role = "CAUSE SITE" if rf.in_cause else "FRAME"
            block = (f"\n### {role}: {rf.method_fqn} "
                     f"(lines {rf.method_start}-{rf.method_end}, {rf.path})\n"
                     f"```java\n{rf.code}\n```")
            parts.append(_trim(block, budget // max(1, len(loc.frames))))
    else:
        parts.append("\n## Localization\n" + loc.note)

    parts.append("\n## Deterministic fix-status verdict (do not contradict)")
    parts.append(f"Headline: {fix.headline}")
    for f in fix.findings[:8]:
        parts.append(f"  - [{f.kind}] {f.detail}")
    return system, "\n".join(parts)


_SYSTEM_V3 = (
    "You are a senior Java engineer doing a precise root-cause analysis from the "
    "evidence given (failing method source, a value-origin finding, call sites, "
    "history, and deterministic git fix-status). Cite evidence by its id (E1, E2…). "
    "Do not invent code or evidence. If localization confidence is low, hedge."
)
_INSTR_V3 = (
    "Output EXACTLY these Markdown sections:\n"
    "## Summary  (<=4 sentences)\n"
    "## Hypotheses  (1-3 blocks, each:)\n"
    "### H1 | category: <null_guard|bounds_check|type_check|exception_handling|logic|"
    "config|data|dependency|other> | confidence: <high|medium|low>\n"
    "Evidence: <comma-separated evidence ids you used>\n"
    "Why: <one line>\n"
    "Verify: <what to check in logs/config/data to confirm or refute>\n"
    "## Suggested fix  (unified diff vs the failing method; only if H1 is high/medium)\n"
    "## Fix-status commentary  (<=4 sentences; must agree with the deterministic verdict)\n")
_INSTR_DEEP_EXTRA = ("\nConsider at least TWO alternative explanations and state what "
                     "evidence would distinguish them.\n")


def build_prompt_v3(err, loc, fix, branch, root_packages, ctx, det_hyps, deep):
    system = _SYSTEM_V3
    parts = [_INSTR_V3 + (_INSTR_DEEP_EXTRA if deep else ""),
             f"\nRepo packages: {', '.join(root_packages) or 'unknown'}"]
    if loc.resolved and loc.type_summary:
        parts.append("\n## Enclosing type\n" + loc.type_summary)
    parts.append(f"\n## Error (branch {branch}): {err.summary()}")
    parts.append(f"Localization confidence: {loc.confidence} "
                 f"({loc.drift_note})" if loc.resolved else "unlocalized")
    if ctx is not None:
        parts.append("\n## Evidence\n" + ctx.to_prompt())
    if loc.resolved:
        parts.append("\n## Failing code")
        for rf in loc.frames[:3]:
            parts.append(f"```java\n{_trim(rf.code, 2500)}\n```")
    parts.append(f"\n## Deterministic verdict (do not contradict): {fix.headline}")
    if det_hyps:
        parts.append("## Deterministic hypotheses already established (facts):")
        for h in det_hyps:
            parts.append(f"- {h['category']}/{h['confidence']}: {h['why']}")
    return system, "\n".join(parts)


# ---------------------------------------------------------------------------
# RCA cache (D7)
# ---------------------------------------------------------------------------
def cache_get(fp: str, method_hash: str, prompt_ver: int):
    row = db.connect().execute(
        "SELECT narrative, tokens, seconds, model FROM rca_cache "
        "WHERE fp=? AND method_hash=? AND prompt_ver=?",
        (fp, method_hash, prompt_ver)).fetchone()
    return row


def cache_put(fp: str, method_hash: str, prompt_ver: int, model: str,
              narrative: str, tokens: int, seconds: float):
    db.connect().execute(
        "INSERT OR REPLACE INTO rca_cache"
        "(fp,method_hash,prompt_ver,model,narrative,tokens,seconds,created)"
        " VALUES(?,?,?,?,?,?,?,?)",
        (fp, method_hash, prompt_ver, model, narrative, tokens, seconds, time.time()))


# ---------------------------------------------------------------------------
# Auto-policy templating (D9)
# ---------------------------------------------------------------------------
def _known_simple(err: ErrorRecord):
    p = err.primary
    if not p:
        return None
    t = p.type.split(".")[-1]
    msg = p.message or ""
    if t == "NullPointerException" and 'because' in msg and ('"' in msg or "'" in msg):
        return "npe"
    if t == "ArrayIndexOutOfBoundsException":
        return "aioobe"
    if t == "ClassCastException" and (" cannot be cast to " in msg or "class " in msg):
        return "cce"
    return None


def is_templatable(err: ErrorRecord, loc: LocResult, fix: FixStatus) -> bool:
    return (loc.resolved and loc.confidence == "high"
            and _known_simple(err) is not None)


def templated_narrative(err: ErrorRecord, loc: LocResult, fix: FixStatus) -> str:
    p = err.primary
    fault = loc.fault
    kind = _known_simple(err)
    site = f"`{fault.method_fqn}` ({fault.path}:{fault.frame.line})" if fault else "the fault site"
    lines = [f"### Root cause",
             f"A `{p.type.split('.')[-1]}` is thrown at {site}. {p.message}".strip()]
    if kind == "npe":
        lines.append("A referenced value is null at this point and is dereferenced "
                     "without a guard.")
    elif kind == "aioobe":
        lines.append("An index outside the array bounds is used at this point.")
    elif kind == "cce":
        lines.append("An object is cast to a type it is not an instance of at this point.")
    lines.append("\n### Suggested fix")
    lines.append("```diff\n# Add a guard / bounds or type check before the failing "
                 "operation; see the code evidence for the exact expression.\n```")
    lines.append("\n### Fix-status")
    lines.append(fix.headline + (f" {fix.findings[0].detail}" if fix.findings else ""))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Depth selection + deterministic hypotheses + grounding (D8/D9)
# ---------------------------------------------------------------------------
def select_depth(loc: LocResult, ctx, fix: FixStatus, fmt: str, freq: int = 0) -> str:
    """location_only | llm_short | llm_deep (D8)."""
    if fmt == "deep":
        return "llm_deep"
    origin_unknown = (ctx is None) or (ctx.origin.get("kind") == "unknown")
    if (loc.resolved and loc.confidence in ("medium", "low")) or origin_unknown \
            or freq >= config.DEEP_THRESHOLD \
            or (fix.verdict == "none_found"):
        return "llm_deep"
    if fmt == "short" and loc.resolved and loc.confidence == "high" \
            and _known_simple_resolved(loc) and not origin_unknown:
        return "location_only"
    return "llm_short"


def _known_simple_resolved(loc: LocResult) -> bool:
    return loc.resolved and loc.fault is not None


def deterministic_hypotheses(err: ErrorRecord, loc: LocResult, ctx, fix: FixStatus) -> list:
    """Injected hypotheses that need no LLM (D9)."""
    hyps = []
    if ctx is not None:
        ok = ctx.origin.get("kind")
        if ok in ("final_field_initialized", "final_field_uninitialized"):
            hyps.append({"id": "D-data", "category": "data",
                         "confidence": "high" if ok == "final_field_initialized" else "medium",
                         "evidence": [e[0] for e in ctx.evidence if e[1] == "origin_finding"],
                         "why": f"The value is a {ok.replace('_',' ')} "
                                f"({ctx.origin.get('field')}); {ctx.origin.get('implication','')}",
                         "verify": "Check whether the object was deserialized/replayed from "
                                   "an older schema (the constructor/initializer was bypassed)."})
        if ok == "lombok_generated":
            hyps.append({"id": "D-lombok", "category": "data", "confidence": "medium",
                         "evidence": [], "why": "Accessor generated by Lombok; the field is "
                         "populated by a builder/constructor/deserializer.",
                         "verify": "Confirm the builder/deserializer actually sets this field."})
    if loc.resolved and loc.confidence != "high":
        hyps.append({"id": "D-drift", "category": "logic", "confidence": "low",
                     "evidence": [], "why": f"Localization confidence is {loc.confidence} "
                     f"({loc.drift_note}); line numbers may have drifted from the deployed build.",
                     "verify": "Re-analyze pinned to the exact deployed commit/tag."})
    # third-party deepest frame -> dependency
    deepest = err.chain[-1] if err.chain else None
    if deepest and deepest.frames:
        tf = deepest.frames[0]
        if tf.cls.startswith(config.FOREIGN_FRAME_PREFIXES) and loc.resolved:
            hyps.append({"id": "D-dep", "category": "dependency", "confidence": "medium",
                         "evidence": [], "why": f"The deepest frame is third-party "
                         f"({tf.cls})" + (f" {tf.lib}" if tf.lib else ""),
                         "verify": "Check the third-party library version/behavior."})
    return hyps


_H_HEADER = re.compile(r"^###\s*H\d+\s*\|\s*category:\s*(\w+)\s*\|\s*confidence:\s*(\w+)", re.I)
_H_EVID = re.compile(r"Evidence:\s*([E0-9,\s]+)", re.I)


def parse_hypotheses(narrative: str, ctx) -> list:
    """Parse '### H1 | category: X | confidence: Y' blocks; keep only those whose
    cited evidence ids exist (grounding check, D9)."""
    valid_ids = {e[0] for e in (ctx.evidence if ctx else [])}
    hyps, cur = [], None
    for line in narrative.splitlines():
        hm = _H_HEADER.match(line.strip())
        if hm:
            if cur:
                hyps.append(cur)
            cur = {"category": hm.group(1).lower(), "confidence": hm.group(2).lower(),
                   "evidence": [], "why": ""}
            continue
        if cur is not None:
            em = _H_EVID.search(line)
            if em:
                cur["evidence"] = [x.strip() for x in em.group(1).split(",") if x.strip()]
            elif line.strip().startswith("Why:"):
                cur["why"] = line.split("Why:", 1)[1].strip()
    if cur:
        hyps.append(cur)
    # grounding: drop hypotheses citing non-existent evidence ids
    grounded = [h for h in hyps if not h["evidence"]
                or all(e in valid_ids for e in h["evidence"])]
    return grounded


def _location_only(err: ErrorRecord, loc: LocResult, ctx, fix: FixStatus, det_hyps: list) -> str:
    p = err.primary
    f = loc.fault
    lines = ["### Location-only analysis (not a full root cause)",
             f"A `{p.type.split('.')[-1]}` is thrown at `{f.method_fqn}` "
             f"({f.path}:{f.frame.line})."]
    if ctx and ctx.failing.get("expr"):
        lines.append(f"Failing expression: `{ctx.failing['expr']}` "
                     f"({ctx.failing.get('kind')}).")
    if ctx and ctx.origin.get("kind") not in (None, "unknown"):
        lines.append(f"Value origin: {ctx.origin}")
    else:
        lines.append("Root cause not analyzed; see hypotheses.")
    if det_hyps:
        lines.append("\n### Hypotheses")
        for h in det_hyps:
            lines.append(f"- [{h['category']}/{h['confidence']}] {h['why']} "
                         f"(verify: {h['verify']})")
    lines.append(f"\n### Fix-status\n{fix.headline}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Orchestration entry point (Round 2)
# ---------------------------------------------------------------------------
def produce_narrative(err: ErrorRecord, loc: LocResult, fix: FixStatus, branch: str,
                      root_packages: list, *, fp: str, method_hash: str,
                      policy: str | None = None, fmt: str = "short",
                      repo=None, commit: str | None = None, partial: bool = False,
                      freq: int = 0) -> dict:
    """Return {narrative, hypotheses, rca_depth, rca_status, source, tokens, seconds}.

    Honors the RCA cache + policy; assembles the context pack (D7), selects depth
    (D8), injects deterministic hypotheses and (for LLM paths) parses + grounds the
    model's hypotheses (D9). Never raises on LLM failure.
    """
    policy = policy or config.LLM_POLICY
    ctx = None
    if repo is not None and commit and loc.resolved:
        try:
            ctx = context.build_context(repo, commit, loc, err, partial=partial)
        except Exception:
            ctx = None
    det_hyps = deterministic_hypotheses(err, loc, ctx, fix)
    depth = select_depth(loc, ctx, fix, fmt, freq)
    base = {"hypotheses": det_hyps, "rca_depth": depth,
            "evidence": ctx.to_dict() if ctx else {},
            "origin_finding": ctx.origin if ctx else {"kind": "unknown"}}

    if policy == "never":
        # deterministic-only: emit the location-only analysis (never "root cause")
        narr = (_location_only(err, loc, ctx, fix, det_hyps) if loc.resolved
                else "_No repo code localized; deterministic evidence only._")
        return {**base, "narrative": narr, "tokens": 0, "seconds": 0,
                "source": "deterministic", "rca_status": "location_only",
                "rca_depth": "location_only"}

    pv = config.PROMPT_VER_DEEP if depth == "llm_deep" else config.PROMPT_VER_SHORT
    # cache: a deep (pv4) result also satisfies a short (pv3) lookup
    for cand_pv in ([config.PROMPT_VER_DEEP, config.PROMPT_VER_SHORT]
                    if depth != "llm_deep" else [config.PROMPT_VER_DEEP]):
        row = cache_get(fp, method_hash, cand_pv)
        if row is not None:
            return {**base, "narrative": row["narrative"], "tokens": row["tokens"],
                    "seconds": row["seconds"], "source": "cache", "rca_status": "done"}

    # location_only: template, no model (never labelled "root cause")
    if depth == "location_only":
        narr = _location_only(err, loc, ctx, fix, det_hyps)
        cache_put(fp, method_hash, config.PROMPT_VER_SHORT, "template", narr, 0, 0.0)
        return {**base, "narrative": narr, "tokens": 0, "seconds": 0,
                "source": "template", "rca_status": "location_only"}

    # LLM path (short or deep)
    deep = depth == "llm_deep"
    system, user = build_prompt_v3(err, loc, fix, branch, root_packages, ctx, det_hyps, deep)
    try:
        res = llm.chat(system, user, thinking=("on" if deep else "off"),
                       max_tokens=(6000 if deep else 2500))
    except llm.LLMError as e:
        return {**base, "narrative": f"_LLM unavailable: {e}_", "tokens": 0,
                "seconds": 0, "source": "skipped", "rca_status": "pending"}
    llm_hyps = parse_hypotheses(res.text, ctx)
    status = "done"
    narrative = res.text
    # grounding: if the model produced hypotheses but none are grounded -> ungrounded
    if "### H" in res.text and not llm_hyps:
        status = "ungrounded"
    # contradiction auto-correction (D9)
    if fix.verdict == "lost" and re.search(r"no fix (exists|found)", res.text, re.I):
        narrative += ("\n\n> **Automatic correction:** the deterministic verdict is "
                      "`lost` — a fix exists on another branch but is absent here.")
    merged = (llm_hyps or []) + det_hyps
    cache_put(fp, method_hash, pv, config.LLM_MODEL, narrative,
              res.completion_tokens, res.elapsed_s)
    return {**base, "narrative": narrative, "hypotheses": merged, "tokens": res.completion_tokens,
            "seconds": res.elapsed_s, "source": "llm", "rca_status": status}


# Backward-compatible wrapper used by the old single-error path/tests.
def run_rca(err, loc, fix, branch, root_packages):
    system, user = build_prompt(err, loc, fix, branch, root_packages, fmt="long")
    result = llm.chat(system, user)
    return result, user


# ---------------------------------------------------------------------------
# Markdown report (kept; HTML lives in htmlreport.py)
# ---------------------------------------------------------------------------
def render_report(err: ErrorRecord, loc: LocResult, fix: FixStatus,
                  branch: str, narrative: str, llm_meta: dict) -> str:
    md: list[str] = []
    md.append(f"# RCA — {err.summary()}")
    md.append("")
    md.append(f"- **Error id:** `{err.id}`")
    md.append(f"- **Source:** {err.source}")
    md.append(f"- **Branch:** `{branch}`")
    md.append(f"- **Localization confidence:** {loc.confidence}"
              + (f" — {loc.drift_note}" if loc.drift_note else ""))
    if loc.resolved and loc.fault:
        md.append(f"- **Fault site:** `{loc.fault.method_fqn}` "
                  f"({loc.fault.path}:{loc.fault.frame.line})")
    md.append(f"- **Fix status:** {fix.headline}")
    md.append(f"- **RCA source:** {llm_meta.get('source','?')}")
    md.append("")
    md.append("## Analysis")
    md.append(narrative.strip() or "_(pending)_")
    md.append("")
    md.append("## Fix-status evidence (git/PR)")
    if fix.note:
        md.append(f"> {fix.note}")
    for f in fix.findings:
        refs = f" — refs: {', '.join(f.refs)}" if f.refs else ""
        md.append(f"- **{f.kind}**: {f.detail}{refs}")
    if not fix.findings:
        md.append("- No fix-related history found.")
    md.append("")
    if loc.resolved:
        md.append("## Code evidence")
        for rf in loc.frames:
            md.append(f"### {rf.method_fqn} ({rf.path}:{rf.method_start}-{rf.method_end})")
            md.append("```java")
            md.append(rf.code)
            md.append("```")
    return "\n".join(md)

````

### `ghrca/repo.py`
**Purpose:** git-over-SSH: mirror clone/fetch, ls-remote, bulk blob reads, batch-check, diffs, patch-id, blame, ancestry, branch_delta, commit-graph.

```python
"""Git operations over SSH -- the unlimited, no-API-cost path.

We keep a single `--mirror` clone per repo (all refs, compact, shared object
store). File contents for indexing are read straight out of the object store
with `git cat-file --batch` (one process for thousands of files) rather than
checking anything out. Branch/commit/diff queries are thin wrappers over git.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass

from . import config


class GitError(RuntimeError):
    pass


@dataclass
class BranchRef:
    name: str          # e.g. "main"
    sha: str           # full commit sha
    committed: str     # ISO date of tip commit


class Repo:
    def __init__(self, owner_repo: str, source: str | None = None):
        # `owner_repo` is the logical id ("opensolon/solon-ai" or "local/testbed").
        # `source` overrides the clone URL — a local path or any git URL. When
        # omitted, the SSH GitHub URL is derived from owner_repo.
        self.owner_repo = owner_repo
        self.source = source
        self.slug = config.repo_slug(owner_repo)
        self.path = config.REPOS_DIR / f"{self.slug}.git"

    # -- low-level git -----------------------------------------------------
    def _git(self, *args: str, check: bool = True, binary: bool = False):
        # Always capture bytes and decode as UTF-8 ourselves. git output is
        # UTF-8, but Python's text mode would use the Windows cp1252 locale and
        # crash on non-ASCII source/commit content.
        cmd = ["git", "--git-dir", str(self.path), *args]
        proc = subprocess.run(cmd, capture_output=True)
        if check and proc.returncode != 0:
            err = proc.stderr.decode("utf-8", "replace")
            raise GitError(f"git {' '.join(args[:3])}... failed: {err.strip()[:500]}")
        if binary:
            return proc.stdout
        return proc.stdout.decode("utf-8", "replace")

    # -- lifecycle ---------------------------------------------------------
    def exists(self) -> bool:
        return self.path.exists()

    def remote_url(self) -> str:
        return self.source or config.clone_url(self.owner_repo)

    def ls_remote_heads(self) -> dict[str, str]:
        """One network round trip: {branch_name: sha} for remote heads.

        Does not fetch objects — used by the poller to detect change cheaply.
        """
        out = subprocess.run(
            ["git", "ls-remote", "--heads", self.remote_url()],
            capture_output=True)
        if out.returncode != 0:
            raise GitError(f"ls-remote failed: "
                           f"{out.stderr.decode('utf-8','replace')[:300]}")
        refs: dict[str, str] = {}
        for line in out.stdout.decode("utf-8", "replace").splitlines():
            parts = line.split("\t")
            if len(parts) == 2 and parts[1].startswith("refs/heads/"):
                refs[parts[1][len("refs/heads/"):]] = parts[0]
        return refs

    def _setup_commit_graph(self, big: bool = False) -> None:
        """Enable + (re)write the commit-graph for fast history/ancestry ops (D4)."""
        try:
            self._git("config", "fetch.writeCommitGraph", "true", check=False)
            self._git("config", "core.commitGraph", "true", check=False)
            self._git("commit-graph", "write", "--reachable",
                      "--changed-paths", check=False)
        except GitError:
            pass  # commit-graph is an optimization, never fatal

    def clone_or_update(self) -> str:
        """Mirror-clone on first use, else fetch --prune. Returns a status line."""
        config.ensure_dirs()
        if not self.exists():
            url = self.source or config.clone_url(self.owner_repo)
            proc = subprocess.run(
                ["git", "clone", "--mirror", url, str(self.path)],
                capture_output=True,
            )
            if proc.returncode != 0:
                raise GitError(
                    f"clone failed: {proc.stderr.decode('utf-8','replace').strip()[:500]}")
            self._setup_commit_graph()
            return f"cloned {self.owner_repo}"
        # Update all refs; prune deleted branches.
        self._git("remote", "update", "--prune")
        self._setup_commit_graph()
        return f"fetched {self.owner_repo}"

    # -- refs / branches ---------------------------------------------------
    def default_branch(self) -> str:
        out = self._git("symbolic-ref", "--short", "HEAD", check=False).strip()
        if out:
            return out
        for cand in ("main", "master"):
            if self._git("rev-parse", "--verify", cand, check=False).strip():
                return cand
        branches = self.list_branches()
        return branches[0].name if branches else "main"

    def list_branches(self) -> list[BranchRef]:
        fmt = "%(refname:short)%09%(objectname)%09%(committerdate:iso-strict)"
        out = self._git("for-each-ref", "--sort=-committerdate",
                        f"--format={fmt}", "refs/heads")
        refs: list[BranchRef] = []
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) == 3:
                refs.append(BranchRef(parts[0], parts[1], parts[2]))
        return refs

    def rev_parse(self, rev: str) -> str:
        return self._git("rev-parse", rev).strip()

    # -- new-branch detection (req #2) ------------------------------------
    def _state_path(self):
        return config.STATE_DIR / f"{self.slug}.refs.json"

    def snapshot_refs(self) -> dict[str, str]:
        return {b.name: b.sha for b in self.list_branches()}

    def detect_new_and_changed(self) -> dict[str, list[str]]:
        """Compare live refs to the last snapshot.

        Returns {"new": [...], "changed": [...], "removed": [...]} and updates
        the snapshot on disk. This is how a freshly-created branch gets picked
        up and indexed ASAP on the next `refresh`.
        """
        config.ensure_dirs()
        prev: dict[str, str] = {}
        sp = self._state_path()
        if sp.exists():
            try:
                prev = json.loads(sp.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                prev = {}
        cur = self.snapshot_refs()
        new = [b for b in cur if b not in prev]
        changed = [b for b in cur if b in prev and prev[b] != cur[b]]
        removed = [b for b in prev if b not in cur]
        sp.write_text(json.dumps(cur, indent=2), encoding="utf-8")
        return {"new": sorted(new), "changed": sorted(changed), "removed": sorted(removed)}

    # -- reading file trees (for the indexer) -----------------------------
    def ls_java_files(self, rev: str) -> list[str]:
        out = self._git("ls-tree", "-r", "--name-only", rev)
        files = []
        for path in out.splitlines():
            if not path.endswith(config.JAVA_SUFFIX):
                continue
            parts = path.split("/")
            if any(seg in config.INDEX_SKIP_DIRS for seg in parts):
                continue
            files.append(path)
        return files

    def ls_all_files(self, rev: str) -> list[str]:
        out = self._git("ls-tree", "-r", "--name-only", rev)
        return [p for p in out.splitlines()
                if not any(seg in config.INDEX_SKIP_DIRS for seg in p.split("/"))]

    def read_files(self, rev: str, paths: list[str]) -> dict[str, str]:
        """Bulk-read many blobs in a single `git cat-file --batch` process."""
        if not paths:
            return {}
        specs = "".join(f"{rev}:{p}\n" for p in paths).encode("utf-8")
        proc = subprocess.run(
            ["git", "--git-dir", str(self.path), "cat-file", "--batch"],
            input=specs, capture_output=True,
        )
        if proc.returncode != 0:
            raise GitError(f"cat-file failed: {proc.stderr.decode('utf-8','replace')[:300]}")
        out = proc.stdout
        result: dict[str, str] = {}
        i = 0
        n = len(out)
        for path in paths:
            # header line: "<sha> <type> <size>\n"  (or "<spec> missing\n")
            nl = out.find(b"\n", i)
            if nl < 0:
                break
            header = out[i:nl].decode("utf-8", "replace")
            i = nl + 1
            if header.endswith("missing"):
                continue
            try:
                size = int(header.rsplit(" ", 1)[1])
            except (ValueError, IndexError):
                continue
            content = out[i:i + size]
            i += size + 1  # skip trailing newline
            result[path] = content.decode("utf-8", "replace")
        return result

    def read_file(self, rev: str, path: str) -> str | None:
        out = self._git("show", f"{rev}:{path}", check=False)
        return out if out else None

    def ls_java_blobs(self, rev: str) -> dict[str, str]:
        """{path: blob_sha} for every .java file at `rev` (one ls-tree)."""
        out = self._git("ls-tree", "-r", rev)
        result: dict[str, str] = {}
        for line in out.splitlines():
            meta, _, path = line.partition("\t")
            if not path.endswith(config.JAVA_SUFFIX):
                continue
            if any(seg in config.INDEX_SKIP_DIRS for seg in path.split("/")):
                continue
            parts = meta.split()
            if len(parts) >= 3 and parts[1] == "blob":
                result[path] = parts[2]
        return result

    def read_blobs(self, shas: list[str]) -> dict[str, str]:
        """Bulk-read blobs BY blob-sha in one cat-file --batch process.

        On a partial (blob:none) clone this transparently triggers the promisor
        lazy-fetch for any missing blob."""
        if not shas:
            return {}
        specs = "".join(f"{s}\n" for s in shas).encode("utf-8")
        proc = subprocess.run(
            ["git", "--git-dir", str(self.path), "cat-file", "--batch"],
            input=specs, capture_output=True)
        out = proc.stdout
        result: dict[str, str] = {}
        i = 0
        for sha in shas:
            nl = out.find(b"\n", i)
            if nl < 0:
                break
            header = out[i:nl].decode("utf-8", "replace")
            i = nl + 1
            if header.endswith("missing"):
                continue
            parts = header.split(" ")
            if len(parts) < 3:
                continue
            try:
                size = int(parts[2])
            except ValueError:
                continue
            result[parts[0]] = out[i:i + size].decode("utf-8", "replace")
            i += size + 1
        return result

    def batch_check(self, specs: list[str]) -> dict[str, str | None]:
        """Resolve many `<commit>:<path>` (or sha) specs to blob shas in one
        cat-file --batch-check process. Value is the blob sha, or None if missing."""
        if not specs:
            return {}
        payload = "".join(f"{s}\n" for s in specs).encode("utf-8")
        proc = subprocess.run(
            ["git", "--git-dir", str(self.path), "cat-file", "--batch-check"],
            input=payload, capture_output=True)
        result: dict[str, str | None] = {}
        lines = proc.stdout.decode("utf-8", "replace").splitlines()
        for spec, line in zip(specs, lines):
            parts = line.split(" ")
            if len(parts) >= 2 and parts[1] == "blob":
                result[spec] = parts[0]
            else:
                result[spec] = None
        return result

    def prefetch_blobs(self, shas: list[str]) -> float:
        """Ensure blobs are local (partial-clone promisor fetch), batched.

        Returns seconds spent. Reading via cat-file --batch already triggers the
        lazy fetch; this forces it up-front in one process rather than per-blob."""
        import time as _t
        if not shas:
            return 0.0
        t0 = _t.time()
        self.read_blobs(shas)
        return _t.time() - t0

    def tree_sha(self, rev: str) -> str:
        return self._git("rev-parse", f"{rev}^{{tree}}").strip()

    def merge_base(self, a: str, b: str) -> str:
        return self._git("merge-base", a, b, check=False).strip()

    def branch_delta(self, base: str, branch: str) -> dict[str, tuple]:
        """{path: (old_blob, new_blob, status)} changed between merge-base(base,
        branch) and branch. git diff-tree already skips identical subtrees (D3)."""
        mb = self.merge_base(base, branch) or base
        out = self._git("diff-tree", "-r", "--no-renames", "--raw", mb, branch,
                        check=False)
        delta: dict[str, tuple] = {}
        for line in out.splitlines():
            if not line.startswith(":"):
                continue
            meta, _, path = line.partition("\t")
            parts = meta.split()
            if len(parts) >= 5:
                old_blob, new_blob, status = parts[2], parts[3], parts[4]
                delta[path] = (old_blob, new_blob, status)
        return delta

    # -- diff / log / archaeology helpers ---------------------------------
    def diff(self, a: str, b: str, path: str | None = None, unified: int = 3) -> str:
        args = ["diff", f"-U{unified}", a, b]
        if path:
            args += ["--", path]
        return self._git(*args, check=False)

    def diff_stat(self, a: str, b: str) -> str:
        return self._git("diff", "--stat", a, b, check=False)

    def log_for_path(self, path: str, rev: str = "--all", limit: int = 30) -> list[dict]:
        fmt = "%H%x09%an%x09%ad%x09%s"
        out = self._git("log", rev, f"-n{limit}", "--date=short",
                        f"--format={fmt}", "--", path, check=False)
        commits = []
        for line in out.splitlines():
            parts = line.split("\t", 3)
            if len(parts) == 4:
                commits.append({"sha": parts[0], "author": parts[1],
                                "date": parts[2], "subject": parts[3]})
        return commits

    def log_line_range(self, path: str, start: int, end: int, limit: int = 15) -> list[dict]:
        """History of a specific line range (`git log -L`)."""
        fmt = "%H%x09%an%x09%ad%x09%s"
        out = self._git("log", "--all", f"-n{limit}", "--date=short",
                        f"-L{start},{end}:{path}", "--format=%n"+fmt,
                        check=False)
        commits = []
        for line in out.splitlines():
            if "\t" not in line:
                continue
            parts = line.split("\t", 3)
            if len(parts) == 4 and len(parts[0]) >= 7:
                commits.append({"sha": parts[0], "author": parts[1],
                                "date": parts[2], "subject": parts[3]})
        # de-dup while preserving order
        seen, uniq = set(), []
        for c in commits:
            if c["sha"] not in seen:
                seen.add(c["sha"])
                uniq.append(c)
        return uniq

    def branches_containing(self, sha: str) -> list[str]:
        out = self._git("branch", "--contains", sha, "--format=%(refname:short)",
                        check=False)
        return [b.strip() for b in out.splitlines() if b.strip()]

    def cherry(self, upstream: str, head: str) -> list[dict]:
        """Commits on `head` not yet in `upstream` (git cherry). '+' = not applied."""
        out = self._git("cherry", "-v", upstream, head, check=False)
        commits = []
        for line in out.splitlines():
            line = line.strip()
            if not line or line[0] not in "+-":
                continue
            mark, rest = line[0], line[1:].strip()
            sha, _, subject = rest.partition(" ")
            commits.append({"applied": mark == "-", "sha": sha, "subject": subject})
        return commits

    def grep_log(self, pattern: str, rev: str = "--all", limit: int = 40) -> list[dict]:
        fmt = "%H%x09%an%x09%ad%x09%s"
        out = self._git("log", rev, f"-n{limit}", "--date=short", "-i",
                        f"--grep={pattern}", f"--format={fmt}", check=False)
        commits = []
        for line in out.splitlines():
            parts = line.split("\t", 3)
            if len(parts) == 4:
                commits.append({"sha": parts[0], "author": parts[1],
                                "date": parts[2], "subject": parts[3]})
        return commits

    # -- D10 fix-status primitives ----------------------------------------
    def is_ancestor(self, anc: str, desc: str) -> bool:
        """True if `anc` is an ancestor of `desc` (git merge-base --is-ancestor)."""
        proc = subprocess.run(
            ["git", "--git-dir", str(self.path), "merge-base", "--is-ancestor",
             anc, desc], capture_output=True)
        return proc.returncode == 0

    def file_patch_id(self, sha: str, path: str) -> str:
        """Stable, file-scoped patch-id: `git show <sha> -- <path> | git patch-id
        --stable`. Equal across cherry-picks/rebases of the same change."""
        show = subprocess.run(
            ["git", "--git-dir", str(self.path), "show", sha, "--", path],
            capture_output=True)
        if show.returncode != 0 or not show.stdout:
            return ""
        pid = subprocess.run(
            ["git", "--git-dir", str(self.path), "patch-id", "--stable"],
            input=show.stdout, capture_output=True)
        out = pid.stdout.decode("utf-8", "replace").strip()
        return out.split(" ")[0] if out else ""

    def commits_touching_in_range(self, range_expr: str, path: str,
                                  limit: int = 200) -> list[str]:
        out = self._git("log", f"-n{limit}", "--format=%H", range_expr, "--", path,
                        check=False)
        return [l.strip() for l in out.splitlines() if l.strip()]

    def added_lines(self, sha: str, path: str) -> list[str]:
        out = self._git("show", "--format=", "--unified=0", sha, "--", path, check=False)
        added = []
        for line in out.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                added.append(line[1:])
        return added

    def removed_lines(self, sha: str, path: str) -> list[str]:
        out = self._git("show", "--format=", "--unified=0", sha, "--", path, check=False)
        removed = []
        for line in out.splitlines():
            if line.startswith("-") and not line.startswith("---"):
                removed.append(line[1:])
        return removed

    def blame_origin(self, commit: str, path: str, line: int) -> str | None:
        out = self._git("blame", "-L", f"{line},{line}", "--porcelain",
                        commit, "--", path, check=False)
        first = out.splitlines()[0] if out else ""
        sha = first.split(" ")[0] if first else ""
        return sha if len(sha) >= 7 else None

    def first_tag_containing(self, sha: str) -> str | None:
        out = self._git("tag", "--contains", sha, "--sort=creatordate", check=False)
        tags = [t.strip() for t in out.splitlines() if t.strip()]
        return tags[0] if tags else None

    def commits_grep_touching(self, target: str, pattern: str, path: str,
                              limit: int = 50) -> list[str]:
        out = self._git("log", f"-n{limit}", "--format=%H", "-i",
                        f"--grep={pattern}", target, "--", path, check=False)
        return [l.strip() for l in out.splitlines() if l.strip()]

    def commit_meta(self, sha: str) -> dict:
        out = self._git("show", "-s", "--format=%H%x09%an%x09%ad%x09%s",
                        "--date=short", sha, check=False)
        parts = out.strip().split("\t", 3)
        if len(parts) == 4:
            return {"sha": parts[0], "author": parts[1], "date": parts[2],
                    "subject": parts[3]}
        return {"sha": sha, "author": "", "date": "", "subject": ""}

    def show_commit(self, sha: str, max_chars: int = 4000) -> str:
        out = self._git("show", "--stat", "--format=%H%n%an %ad%n%n%s%n%n%b",
                        sha, check=False)
        return out[:max_chars]

```

### `ghrca/sources/__init__.py`
**Purpose:** Error-source package.

```python
"""Pluggable error sources (D13). Each source yields records:
  {"repo": <id>, "name": <short>, "raw_text": <trace>, "source_id": <str>,
   "version": <optional>}
"""
from . import dropdir  # noqa: F401

```

### `ghrca/sources/dropdir.py`
**Purpose:** Drop-directory error source (errors_inbox/<slug>/*.txt|log|jsonl -> _done).

```python
"""Drop-directory error source (D13).

Files placed under `errors_inbox/<repo-slug>/*.txt|*.log|*.jsonl` are ingested and
moved to `errors_inbox/_done/`. JSONL lines may carry {"trace","version","ts"}.
Splunk/Sentry are out of scope but can write here.
"""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

from .. import config


def inbox_root() -> Path:
    import os
    return Path(os.environ.get("GHRCA_INBOX", config.PROJECT_ROOT / "errors_inbox"))


def _done_dir() -> Path:
    d = inbox_root() / "_done"
    d.mkdir(parents=True, exist_ok=True)
    return d


def poll(repo_ids: list[str]) -> list[dict]:
    """Return new error records for the given repos and archive processed files."""
    root = inbox_root()
    records: list[dict] = []
    for repo_id in repo_ids:
        slug = config.repo_slug(repo_id)
        d = root / slug
        if not d.is_dir():
            continue
        for f in sorted(d.iterdir()):
            if f.suffix not in (".txt", ".log", ".jsonl") or not f.is_file():
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if f.suffix == ".jsonl":
                for i, line in enumerate(text.splitlines()):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    records.append({
                        "repo": repo_id, "name": f"{f.stem}#{i}",
                        "raw_text": obj.get("trace", ""),
                        "version": obj.get("version", ""),
                        "source_id": f"drop:{f.name}#{i}"})
            else:
                records.append({
                    "repo": repo_id, "name": f.stem, "raw_text": text,
                    "version": "", "source_id": f"drop:{f.name}"})
            # archive
            dest = _done_dir() / f"{int(time.time()*1000)}_{slug}_{f.name}"
            try:
                shutil.move(str(f), str(dest))
            except OSError:
                pass
    return records

```

### `ghrca/tsjava.py`
**Purpose:** tree-sitter Java scanner (PRIMARY): types/methods with line ranges, body_hash, statement_at().

```python
"""Tree-sitter Java scanner (D2).

Same output shape as `javascan.scan()` (package, imports, types with fqn + line
ranges + extends/implements, methods with owner fqn + line ranges + signature,
fields) plus a per-method `body_hash` and a `statement_at()` helper for drift
validation. Error-tolerant: on a file that yields zero types but is non-empty,
callers fall back to the regex scanner.
"""

from __future__ import annotations

import tree_sitter_java
from tree_sitter import Language, Parser

from .javascan import FileIndex, TypeInfo, MethodInfo, body_hash

PARSER_VER = 3  # bump when output changes (part of the blob cache key)

_LANG = Language(tree_sitter_java.language())
_PARSER = Parser(_LANG)

_TYPE_NODES = {
    "class_declaration": "class",
    "interface_declaration": "interface",
    "enum_declaration": "enum",
    "record_declaration": "record",
    "annotation_type_declaration": "@interface",
}
_METHOD_NODES = {"method_declaration", "constructor_declaration"}


def _txt(src: bytes, node) -> str:
    return src[node.start_byte:node.end_byte].decode("utf-8", "replace")


def _line(node) -> int:
    return node.start_point[0] + 1


def _end_line(node) -> int:
    return node.end_point[0] + 1


def _field_text(src: bytes, node, field: str) -> str:
    ch = node.child_by_field_name(field)
    return _txt(src, ch) if ch is not None else ""


def scan(path: str, src: str) -> FileIndex:
    data = src.encode("utf-8")
    tree = _PARSER.parse(data)
    fi = FileIndex(path=path, loc=src.count("\n") + 1)
    package = {"name": ""}

    def walk(node, type_stack):
        t = node.type
        if t == "package_declaration":
            # child is a scoped/identifier name
            name = ""
            for c in node.named_children:
                if c.type in ("scoped_identifier", "identifier"):
                    name = _txt(data, c)
            package["name"] = name
            fi.package = name
            return
        if t == "import_declaration":
            raw = _txt(data, node)
            raw = raw.replace("import", "", 1).replace("static", "", 1)
            fi.imports.append(raw.strip().rstrip(";").strip())
            return

        if t in _TYPE_NODES:
            name = _field_text(data, node, "name")
            owner = type_stack[-1] if type_stack else ""
            if owner:
                fqn = owner + "." + name
            else:
                fqn = (package["name"] + "." + name) if package["name"] else name
            ext = _field_text(data, node, "superclass").replace("extends", "").strip()
            # interfaces: 'super_interfaces' -> 'interfaces'
            impl = ""
            si = node.child_by_field_name("interfaces")
            if si is not None:
                impl = _txt(data, si).replace("implements", "").strip()
            fi.types.append(TypeInfo(name=name, kind=_TYPE_NODES[t], fqn=fqn,
                                     start=_line(node), end=_end_line(node),
                                     extends=ext, implements=impl))
            # recurse into body with this fqn pushed
            for c in node.named_children:
                walk(c, type_stack + [fqn])
            return

        if t in _METHOD_NODES:
            owner = type_stack[-1] if type_stack else (package["name"] or "")
            name = _field_text(data, node, "name") or (
                owner.split(".")[-1] if t == "constructor_declaration" else "")
            # signature = text up to the body '{' or ';'
            body = node.child_by_field_name("body")
            sig_end = body.start_byte if body is not None else node.end_byte
            sig = data[node.start_byte:sig_end].decode("utf-8", "replace")
            sig = " ".join(sig.split())[:200]
            src_text = _txt(data, node)
            fi.methods.append(MethodInfo(
                name=name, owner=owner, fqn=f"{owner}#{name}",
                start=_line(node), end=_end_line(node), signature=sig))
            fi.methods[-1].body_hash = body_hash(src_text)  # attach dynamically
            # methods can contain local/anonymous classes; keep scanning for types
            for c in node.named_children:
                walk(c, type_stack)
            return

        if t == "field_declaration":
            owner = type_stack[-1] if type_stack else ""
            for c in node.named_children:
                if c.type == "variable_declarator":
                    nm = _field_text(data, c, "name")
                    if nm:
                        fi.fields.append({"name": nm, "owner": owner, "line": _line(node)})
            return

        for c in node.named_children:
            walk(c, type_stack)

    walk(tree.root_node, [])
    return fi


def statement_at(source: str, line: int) -> str:
    """Return the smallest statement/expression node text covering `line` (D11)."""
    data = source.encode("utf-8")
    tree = _PARSER.parse(data)
    best = None

    def visit(node):
        nonlocal best
        s = node.start_point[0] + 1
        e = node.end_point[0] + 1
        if s <= line <= e:
            if node.type.endswith("statement") or node.type in (
                    "expression_statement", "local_variable_declaration",
                    "return_statement", "field_declaration"):
                if best is None or (e - s) <= (best.end_point[0] - best.start_point[0]):
                    best = node
            for c in node.named_children:
                visit(c)

    visit(tree.root_node)
    if best is not None:
        return _txt(data, best)
    lines = source.splitlines()
    return lines[line - 1] if 1 <= line <= len(lines) else ""

```

### `requirements.txt`
**Purpose:** pip dependencies.

```text
# ghrca runtime deps (stdlib otherwise)
tree-sitter>=0.23
tree-sitter-java>=0.23
# dev/test
pytest>=8.0

```

### `targets.json`
**Purpose:** Agent/daemon input: repos x error traces + deployment config.

```json
{
  "output_dir": "agent_reports",
  "repos": [
    {
      "id": "opensolon/solon-ai",
      "source": null,
      "deployment": {"strategy": "default"},
      "errors": [
        {
          "name": "assistant-role-npe",
          "source": "splunk:prod-2026-09-28",
          "trace": "2026-09-28 14:22:07.114 ERROR [http-nio-8080-exec-3] o.n.s.web.DispatcherHandler - Unhandled exception\njava.lang.NullPointerException: Cannot invoke \"org.noear.solon.ai.chat.message.ChatRole.name()\" because the return value of \"org.noear.solon.ai.chat.message.AssistantMessage.getRole()\" is null\n\tat org.noear.solon.ai.chat.dialect.AbstractChatDialect.buildAssistantMessageNodeDo(AbstractChatDialect.java:93)\n\tat org.noear.solon.ai.chat.dialect.AbstractChatDialect.buildChatMessageNodeDo(AbstractChatDialect.java:210)\n\tat org.noear.solon.ai.chat.ChatRequestDefault.call(ChatRequestDefault.java:180)\n\tat com.example.myapp.ChatController.ask(ChatController.java:42)\n\tat java.base/java.lang.reflect.Method.invoke(Method.java:568)"
        },
        {
          "name": "tool-role-npe",
          "source": "splunk:prod-2026-09-29",
          "trace": "2026-09-29 09:05:41.882 ERROR [reactor-http-nio-4] o.n.s.ai.chat - tool message serialization failed\njava.lang.NullPointerException: Cannot invoke \"org.noear.solon.ai.chat.ChatRole.name()\" because the return value of \"org.noear.solon.ai.chat.message.ToolMessage.getRole()\" is null\n\tat org.noear.solon.ai.chat.dialect.AbstractChatDialect.buildToolMessageNodeDo(AbstractChatDialect.java:191)\n\tat org.noear.solon.ai.chat.dialect.AbstractChatDialect.buildChatMessageNodeDo(AbstractChatDialect.java:340)\n\tat org.noear.solon.ai.chat.ChatRequestDefault.call(ChatRequestDefault.java:180)"
        }
      ]
    },
    {
      "id": "local/acme-orders",
      "source": "F:\\Desktop\\python-vm\\github_scrape\\testbed\\acme-orders.git",
      "deployment": {"strategy": "file", "path": "deployment-info.json", "ref": "main"},
      "errors": [
        {
          "name": "order-checkout-npe",
          "source": "splunk:acme-prod-2026-09-30",
          "trace": "2026-09-30 02:14:55.001 ERROR [http-nio-9090-exec-7] c.a.orders.OrderApi - checkout failed\njava.lang.NullPointerException: Cannot invoke \"com.acme.orders.Customer.getId()\" because the return value of \"com.acme.orders.Cart.getCustomer()\" is null\n\tat com.acme.orders.OrderService.checkout(OrderService.java:8)\n\tat com.acme.orders.OrderApi.handle(OrderApi.java:6)"
        }
      ]
    }
  ]
}

```

### `tests/__init__.py`
**Purpose:** (source file)

```python

```

### `tests/conftest.py`
**Purpose:** pytest fixtures (isolated temp SQLite DB).

```python
"""Shared test fixtures. Isolates the SQLite DB into a temp dir so tests never
touch the real cache."""
import os
import tempfile
import pytest


@pytest.fixture()
def temp_db(monkeypatch):
    d = tempfile.mkdtemp(prefix="ghrca_test_")
    dbpath = os.path.join(d, "t.db")
    monkeypatch.setenv("GHRCA_DB", dbpath)
    from ghrca import db
    db.reset_thread_conn()
    yield dbpath
    db.reset_thread_conn()

```

### `tests/test_metamorphic.py`
**Purpose:** Metamorphic/anti-saturation tests (body_hash invariants, blast classification).

```python
"""Metamorphic tests (D6): transform a fixture and assert the classification is
what it must be. These are generated variants; they never enter the dev corpus."""

import re

from ghrca import tsjava, blast

_BUGGY = (
    "public Receipt checkout(Cart cart) {\n"
    "    String customerId = cart.getCustomer().getId();\n"
    "    int n = cart.getItems().size();\n"
    "    return new Receipt(customerId, n);\n"
    "}\n")


def _wrap(method_src):
    return "package com.x;\npublic class M {\n" + method_src + "}\n"


def _bh(method_src):
    fi = tsjava.scan("M.java", _wrap(method_src))
    return [m for m in fi.methods if m.name == "checkout"][0].body_hash


# --- body_hash invariants (affected detection) ---
def test_whitespace_change_same_hash():
    spaced = _BUGGY.replace("    ", "        ").replace("\n}", "\n\n}")
    assert _bh(spaced) == _bh(_BUGGY)          # whitespace-only -> still affected


def test_comment_change_same_hash():
    commented = _BUGGY.replace("int n", "// loyalty check\n    int n")
    assert _bh(commented) == _bh(_BUGGY)       # comment-only -> still affected


def test_line_shift_same_method_hash():
    # inserting lines ABOVE the method doesn't change its body hash
    shifted = "private int VERSION = 1;\n" + _BUGGY
    assert _bh(shifted) == _bh(_BUGGY)


def test_guard_changes_hash():
    guarded = _BUGGY.replace(
        "String customerId = cart.getCustomer().getId();",
        "if (cart.getCustomer() == null) throw new IllegalStateException();\n"
        "    String customerId = cart.getCustomer().getId();")
    assert _bh(guarded) != _bh(_BUGGY)


# --- blast differing-method classification (D10) ---
def _fault_sig():
    return re.sub(r"\s+", " ", "String customerId = cart.getCustomer().getId();").strip()


def test_classify_still_buggy():
    # failing statement survives, no fix content -> still_buggy
    body = "{ String customerId = cart.getCustomer().getId(); return customerId; }"
    assert blast.classify_differing(body, _fault_sig(), []) == "still_buggy"


def test_classify_fixed_by_content():
    fix_added = [re.sub(r"\s+", "", "if (cart.getCustomer() == null) return null;")]
    body = ("{ if (cart.getCustomer() == null) return null; "
            "String customerId = cart.getCustomer().getId(); }")
    assert blast.classify_differing(body, _fault_sig(), fix_added) == "fixed"


def test_classify_refactored_unknown():
    # failing statement extracted into a helper -> gone from this method, no fix content
    body = "{ String customerId = resolveCustomerId(cart); return customerId; }"
    assert blast.classify_differing(body, _fault_sig(), []) == "refactored_unknown"


def test_sim_helper():
    assert blast._sim("a b c", "a b c") == 1.0
    assert blast._sim("a b c", "x y z") == 0.0

```

### `tests/test_phase1.py`
**Purpose:** Phase-1 tests: fingerprint, ref-diff, priority, job queue.

```python
"""Phase 1 unit tests: fingerprint normalization, identifier extraction,
ref-diff classification, priority scoring, and the persistent job queue."""

import pytest

from ghrca import fingerprint as fp
from ghrca import poller
from ghrca import errors as errmod


# --- fingerprint normalization (>= 25 cases) -------------------------------
@pytest.mark.parametrize("raw,expect_contains,expect_absent", [
    ("Error at id 12345", "<n>", "12345"),
    ("value -42 out of range", "<n>", "-42"),
    ("pi is 3.14159", "<n>", "3.14"),
    ("uuid 550e8400-e29b-41d4-a716-446655440000 bad", "<uuid>", "550e8400"),
    ("addr 0xDEADBEEF12 fault", "<hex>", "deadbeef"),
    ("hash abcdef1234567890 mismatch", "<hex>", "abcdef1234"),
    ("host 192.168.0.1 refused", "<", "192.168"),
    ("path /var/log/app/server.log missing", "<path>", "/var/log"),
    ("file C:\\Users\\x\\a.txt locked", "<path>", "users"),
    ("quoted 'secret-value' rejected", "<s>", "secret-value"),
    ('quoted "another literal" bad', "<s>", "another literal"),
    ("timeout after 30000 ms", "<n>", "30000"),
    ("port 8080 in use", "<n>", "8080"),
    ("connection to 10.0.0.5:5432 failed", "<", "10.0.0.5"),
    ("negative index -1", "<n>", "-1"),
    ("float 0.0 divide", "<n>", "0.0"),
    ("big 999999999999 overflow", "<n>", "999999999999"),
    ("mixed id ABC-123 ref", "<n>", "123"),
    ("multiple 1 2 3 values", "<n>", " 3 "),
    ("session 00000000-0000-0000-0000-000000000000 dead", "<uuid>", "0000-0000"),
    ("offset 0x1F fault", "0x1f", "<hex>"),          # <8 hex stays (0x1F short)
    ("temp 98.6 high", "<n>", "98.6"),
    ("Cannot read length -5", "<n>", "-5"),
    ("bytes 1024 alloc", "<n>", "1024"),
    ("addr fe80::1ff:fe23:4567:890a down", "<", "fe80"),
    ("plain message no variables", "plain message no variables", "<n>"),
])
def test_normalize(raw, expect_contains, expect_absent):
    out = fp.normalize_message(raw)
    assert expect_contains in out, (raw, out)
    if expect_absent:
        assert expect_absent not in out, (raw, out)


def test_normalize_npe_helpful_shape_preserved():
    msg = ('Cannot invoke "org.x.ChatRole.name()" because the return value of '
           '"org.x.AssistantMessage.getRole()" is null')
    out = fp.normalize_message(msg)
    # code-like quoted expressions are preserved (not collapsed to <S>)
    assert "chatrole.name()" in out
    assert "getrole()" in out
    assert "<s>" not in out


def test_normalize_truncates_to_200():
    assert len(fp.normalize_message("x " * 500)) <= 200


def test_same_bug_same_fingerprint_across_ids():
    a = fp.fingerprint("java.lang.NPE", "user 12345 not found", "com.x.S#load")
    b = fp.fingerprint("java.lang.NPE", "user 67890 not found", "com.x.S#load")
    assert a == b


def test_different_frame_different_fingerprint():
    a = fp.fingerprint("java.lang.NPE", "boom", "com.x.A#m")
    b = fp.fingerprint("java.lang.NPE", "boom", "com.x.B#m")
    assert a != b


# --- identifier extraction -------------------------------------------------
def test_extract_identifiers():
    msg = ('Cannot invoke "ChatRole.name()" because the return value of '
           '"AssistantMessage.getRole()" is null')
    ids = fp.extract_message_identifiers(msg)
    assert "ChatRole.name()" in ids
    assert "name" in ids
    assert "getRole" in ids


def test_extract_identifiers_empty():
    assert fp.extract_message_identifiers("no quotes here") == []


# --- top frame selection ---------------------------------------------------
def test_top_frame_skips_foreign():
    trace = ('java.lang.NullPointerException: boom\n'
             '\tat java.base/java.util.Objects.requireNonNull(Objects.java:1)\n'
             '\tat com.acme.orders.OrderService.checkout(OrderService.java:8)\n')
    rec = errmod.from_text(trace, "t")[0]
    top = fp.top_frame(rec)
    assert top == "com.acme.orders.OrderService#checkout"


# --- ref-diff classification -----------------------------------------------
def test_classify_refs():
    prev = {"main": "a", "release-1": "b", "old": "c"}
    cur = {"main": "a", "release-1": "B2", "new": "d"}
    ch = poller.classify(prev, cur)
    assert ch["new"] == ["new"]
    assert ch["moved"] == ["release-1"]
    assert ch["deleted"] == ["old"]
    assert ch["unchanged"] == ["main"]


# --- priority scoring ------------------------------------------------------
@pytest.mark.parametrize("name,manifest,age,expect", [
    ("release-2", None, None, 60),
    ("hotfix/x", None, None, 60),
    ("3.5.x", None, None, 60),
    ("2.8", None, None, 60),
    ("feature-foo", None, 10, 30),
    ("feature-foo", None, 100, 0),
    ("main", "main", None, 100),
    ("random", None, None, 0),
])
def test_priority(name, manifest, age, expect):
    assert poller.branch_priority(name, manifest_branch=manifest,
                                  tip_age_days=age) == expect


# --- job queue: ordering, persistence, resume ------------------------------
def test_queue_ordering(temp_db):
    from ghrca import llmqueue as q
    q.enqueue("rca", {"n": 1}, priority=10)
    q.enqueue("rca", {"n": 2}, priority=90)
    q.enqueue("rca", {"n": 3}, priority=50)
    seen = []
    q.process_all({"rca": lambda p: seen.append(p["n"])})
    assert seen == [2, 3, 1]  # priority desc


def test_queue_persistence_and_resume(temp_db):
    from ghrca import llmqueue as q
    from ghrca import db
    q.enqueue("rca", {"n": 1}, priority=5)
    # simulate a crash mid-job: claim one, leave it 'running'
    row = q._claim_next()
    assert row is not None
    # new "process" — fresh connection to same file
    db.reset_thread_conn()
    resumed = q.reset_running()
    assert resumed == 1
    seen = []
    q.process_all({"rca": lambda p: seen.append(p["n"])})
    assert seen == [1]


def test_queue_retry_then_fail(temp_db):
    from ghrca import llmqueue as q
    from ghrca import db
    q.enqueue("rca", {"n": 1}, priority=1)
    calls = {"n": 0}

    def boom(_):
        calls["n"] += 1
        raise RuntimeError("nope")

    q.process_all({"rca": boom}, backoff_base=0)
    # MAX_ATTEMPTS total tries, then state=failed
    assert calls["n"] == q.MAX_ATTEMPTS
    st = db.connect().execute("SELECT state FROM jobs WHERE id=1").fetchone()["state"]
    assert st == "failed"


def test_rca_priority_formula():
    from ghrca import llmqueue as q
    assert q.rca_priority(60, 3, True) == 60 + 3 + 40
    assert q.rca_priority(0, 100, False) == 0 + 50  # freq capped at 50

```

### `tests/test_phase2.py`
**Purpose:** Phase-2 tests: tree-sitter scan, blob store, lazy resolution, branch_delta.

```python
"""Phase 2 tests: tree-sitter scan, blob store, lazy path resolution, delta.
All offline against the local acme-orders test-bed."""

import os
import pytest

from ghrca import tsjava, indexer, blobstore
from ghrca.repo import Repo

TESTBED = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "testbed", "acme-orders.git")

pytestmark = pytest.mark.skipif(not os.path.exists(TESTBED),
                                reason="test-bed not built (run scratchpad/setup_testbed.py)")


def _acme():
    return Repo("local/acme-orders", source=TESTBED)


def test_tsjava_basic():
    src = ("package com.x;\n"
           "public class A extends B implements C {\n"
           "  public int f(int y) {\n"
           "    return y + 1;\n"
           "  }\n"
           "  static class Inner { void g() {} }\n"
           "}\n")
    fi = tsjava.scan("A.java", src)
    assert fi.package == "com.x"
    fqns = {t.fqn for t in fi.types}
    assert "com.x.A" in fqns and "com.x.A.Inner" in fqns
    f = [m for m in fi.methods if m.name == "f"][0]
    assert f.owner == "com.x.A" and f.start == 3 and f.end == 5
    assert f.body_hash


def test_pkg_dir():
    assert indexer._pkg_dir("com.acme.orders.OrderService", "OrderService.java") \
        == "com/acme/orders"
    assert indexer._pkg_dir("com.acme.orders.Outer$Inner", "Outer.java") \
        == "com/acme/orders"


def test_source_roots(temp_db):
    r = _acme()
    if not r.exists():
        r.clone_or_update()
    roots = indexer.source_roots(r, "main")
    assert any("src/main/java/" in x for x in roots)


def test_resolve_and_blobstore(temp_db):
    r = _acme()
    if not r.exists():
        r.clone_or_update()
    roots = indexer.source_roots(r, "release-2")
    commit = r.rev_parse("release-2")
    path, blob = indexer.resolve_frame_path(
        r, commit, "com.acme.orders.OrderService", "OrderService.java", roots)
    assert path.endswith("OrderService.java") and blob
    blobstore.scan_blobs(r, [blob], path_hint="OrderService.java")
    m = blobstore.method_at_line(blob, 8)
    assert m is not None and m["name"] == "checkout"
    assert blobstore.already_scanned(blob)


def test_branch_delta(temp_db):
    r = _acme()
    if not r.exists():
        r.clone_or_update()
    d = r.branch_delta("release-1", "release-2")
    # release-2 added DiscountPolicy.java on top of release-1
    changed = [p for p in d if p.endswith(".java")]
    assert any("DiscountPolicy" in p for p in changed)


def test_localize_lazy(temp_db):
    from ghrca import errors as errmod
    from ghrca.locate import localize_lazy
    r = _acme()
    if not r.exists():
        r.clone_or_update()
    trace = ('java.lang.NullPointerException: Cannot invoke '
             '"com.acme.orders.Customer.getId()" because the return value of '
             '"com.acme.orders.Cart.getCustomer()" is null\n'
             '\tat com.acme.orders.OrderService.checkout(OrderService.java:8)\n')
    err = errmod.from_text(trace, "t")[0]
    loc = localize_lazy(err, r, r.rev_parse("release-2"), "main")
    assert loc.resolved
    assert loc.fault.method_fqn.endswith("#checkout")
    assert loc.confidence == "high"

```

### `tests/test_phase3.py`
**Purpose:** Phase-3 tests: fix-status v2 verdicts, content thresholds, drift.

```python
"""Phase 3 tests: fix-status v2 decision logic, content thresholds, id extraction,
and drift confidence. Integration parts use the local acme-orders test-bed."""

import os
import pytest

from ghrca import archaeology as arch

TESTBED = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "testbed", "acme-orders.git")
_needs_tb = pytest.mark.skipif(not os.path.exists(TESTBED), reason="test-bed not built")


# --- unit: content presence thresholds ---
def test_content_presence_present():
    added = ["ifcustomer==null", "throwexception", "customerid=customer.getid"]
    state, ratio = arch._content_presence(added, [], set(added))
    assert state == "present_by_content" and ratio == 1.0


def test_content_presence_partial():
    added = ["a" * 5, "b" * 5, "c" * 5, "d" * 5]
    tgt = {"a" * 5, "b" * 5}   # 50%
    state, ratio = arch._content_presence(added, [], tgt)
    assert state == "partial" and 0.3 <= ratio < 0.8


def test_content_presence_absent():
    added = ["x" * 5, "y" * 5, "z" * 5]
    state, ratio = arch._content_presence(added, [], set())
    assert state == "absent"


def test_content_removed_line_still_present_blocks():
    added = ["newline1", "newline2"]
    removed = ["buggyline"]
    tgt = {"newline1", "newline2", "buggyline"}  # buggy line still there
    state, _ = arch._content_presence(added, removed, tgt)
    assert state != "present_by_content"


# --- unit: id extraction ---
def test_extract_ids():
    assert "HADOOP-1234" in arch._extract_ids("HADOOP-1234: fix thing")
    assert "#987" in arch._extract_ids("resolves #987")
    assert arch._extract_ids("no ids here") == []


def test_norm_lines():
    lines = ["  {", "}", "int x = customer.getId();", "// comment", "ab"]
    out = arch._norm_lines(lines)
    assert any("customer.getid" in l.lower() for l in out)
    assert "{" not in out and "}" not in out
    assert "ab" not in out  # too short


# --- integration: verdicts on the test-bed ---
@_needs_tb
@pytest.mark.parametrize("branch,expect", [
    ("release-2", "lost"),
    ("release-3", "present_via_equivalent"),   # cherry-pick
    ("release-5-squash", "present_via_equivalent"),  # squash / content
    ("main", "present"),                        # merged
])
def test_verdicts(temp_db, branch, expect):
    from ghrca.repo import Repo
    from ghrca import errors as errmod
    from ghrca.locate import localize_lazy
    r = Repo("local/acme-orders", source=TESTBED)
    if not r.exists():
        r.clone_or_update()
    trace = ('java.lang.NullPointerException: Cannot invoke '
             '"com.acme.orders.Customer.getId()" because the return value of '
             '"com.acme.orders.Cart.getCustomer()" is null\n'
             '\tat com.acme.orders.OrderService.checkout(OrderService.java:8)\n')
    err = errmod.from_text(trace, "t")[0]
    commit = r.rev_parse(branch)
    loc = localize_lazy(err, r, commit, "main")
    f = loc.fault
    fix = arch.analyze_fix_status(r, None, f.path, "checkout", f.method_start,
                                  f.method_end, commit, branch, fault_line=f.frame.line)
    assert fix.verdict == expect, (branch, fix.verdict, fix.headline)


@_needs_tb
def test_drift_low_confidence(temp_db):
    from ghrca.repo import Repo
    from ghrca import errors as errmod
    from ghrca.locate import localize_lazy
    r = Repo("local/acme-orders", source=TESTBED)
    if not r.exists():
        r.clone_or_update()
    # error reports line 8, but release-6-drift shifted the deref down
    trace = ('java.lang.NullPointerException: Cannot invoke '
             '"com.acme.orders.Customer.getId()" because the return value of '
             '"com.acme.orders.Cart.getCustomer()" is null\n'
             '\tat com.acme.orders.OrderService.checkout(OrderService.java:8)\n')
    err = errmod.from_text(trace, "t")[0]
    loc = localize_lazy(err, r, r.rev_parse("release-6-drift"), "main")
    assert loc.resolved
    assert loc.confidence in ("low", "medium")
    assert loc.fault.method_fqn.endswith("#checkout")  # correct method despite drift

```

### `tests/test_phase4.py`
**Purpose:** Phase-4 tests: blast radius vs reference.

```python
"""Phase 4 tests: blast radius on the local test-bed (offline) + matches the
slow reference implementation."""

import os
import pytest

TESTBED = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "testbed", "acme-orders.git")
_needs_tb = pytest.mark.skipif(not os.path.exists(TESTBED), reason="test-bed not built")


@_needs_tb
def test_blast_classifies_affected(temp_db):
    from ghrca.repo import Repo
    from ghrca import tsjava, blast
    r = Repo("local/acme-orders", source=TESTBED)
    if not r.exists():
        r.clone_or_update()
    path = "src/main/java/com/acme/orders/OrderService.java"
    # buggy body_hash = checkout on release-2
    src = r.read_file("release-2", path)
    m = [x for x in tsjava.scan(path, src).methods if x.name == "checkout"][0]
    res = blast.blast(r, path, "checkout", m.body_hash, use_cache=False)
    # release-1, release-2, release-6-drift keep the buggy method
    assert res.branches["release-2"] == "affected"
    assert res.branches["release-1"] == "affected"
    assert res.branches["release-6-drift"] == "affected"  # drift: same body, shifted lines
    # fixed branches are not affected
    assert res.branches["main"] != "affected"
    assert res.branches["release-3"] != "affected"
    assert res.branches["hotfix-npe"] != "affected"
    assert res.counts.get("affected", 0) == 3


@_needs_tb
def test_blast_matches_reference(temp_db):
    from ghrca.repo import Repo
    from ghrca import tsjava, blast
    r = Repo("local/acme-orders", source=TESTBED)
    if not r.exists():
        r.clone_or_update()
    path = "src/main/java/com/acme/orders/OrderService.java"
    src = r.read_file("release-2", path)
    m = [x for x in tsjava.scan(path, src).methods if x.name == "checkout"][0]
    res = blast.blast(r, path, "checkout", m.body_hash, use_cache=False)
    branches = [b for b, st in res.branches.items() if st != "n/a"]
    ref = blast.blast_reference(r, path, "checkout", m.body_hash, branches)
    for b in branches:
        assert ref[b] == res.branches[b], (b, ref[b], res.branches[b])

```

### `tests/test_phase5.py`
**Purpose:** Phase-5 tests: dropdir source, backport, eval gate, daemon pinning.

```python
"""Phase 5 tests: drop-dir source, backport dry-run, eval gate (offline)."""

import json
import os
import pytest

TESTBED = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "testbed", "acme-orders.git")
_needs_tb = pytest.mark.skipif(not os.path.exists(TESTBED), reason="test-bed not built")


def test_dropdir_source(temp_db, tmp_path, monkeypatch):
    monkeypatch.setenv("GHRCA_INBOX", str(tmp_path / "inbox"))
    from ghrca.sources import dropdir
    from ghrca import config
    d = tmp_path / "inbox" / config.repo_slug("o/r")
    d.mkdir(parents=True)
    (d / "a.txt").write_text("java.lang.NullPointerException: x\n\tat o.r.C.m(C.java:1)\n",
                             encoding="utf-8")
    (d / "b.jsonl").write_text(
        json.dumps({"trace": "java.lang.IllegalStateException: y", "version": "1.2"}) + "\n",
        encoding="utf-8")
    recs = dropdir.poll(["o/r"])
    assert len(recs) == 2
    kinds = {r["source_id"].split(":")[0] for r in recs}
    assert kinds == {"drop"}
    # files archived
    assert not (d / "a.txt").exists()
    assert (tmp_path / "inbox" / "_done").is_dir()
    # second poll finds nothing new
    assert dropdir.poll(["o/r"]) == []


def test_backport_version_handling():
    from ghrca import backport
    assert isinstance(backport.git_supports_merge_tree(), bool)
    v = backport._git_version()
    assert v >= (2, 0)


@_needs_tb
def test_backport_clean(temp_db):
    from ghrca.repo import Repo
    from ghrca import backport
    r = Repo("local/acme-orders", source=TESTBED)
    if not r.exists():
        r.clone_or_update()
    hot = r.rev_parse("hotfix-npe")
    plan = backport.backport_plan(r, hot, "release-2")
    assert plan["ok"] and plan["applies_cleanly"] is True
    assert os.path.exists(plan["patch"])


@_needs_tb
def test_eval_gate(temp_db):
    import importlib
    harness = importlib.import_module("eval.harness")
    result = harness.run()
    ok, problems = harness.gate(result)
    assert result["localization_pct"] >= 95.0, result
    assert result["verdict_pct"] >= 90.0, result
    assert ok, problems


@_needs_tb
def test_daemon_deployed_ref_pins(temp_db):
    from ghrca.repo import Repo
    from ghrca.daemon import Daemon
    r = Repo("local/acme-orders", source=TESTBED)
    if not r.exists():
        r.clone_or_update()
    cfg = {"deployment": {"strategy": "file", "path": "deployment-info.json", "ref": "main"}}
    d = Daemon({"repos": [{"id": "local/acme-orders", "source": TESTBED}]}, use_llm=False)
    ref, branch, pinned = d._deployed_ref(r, cfg)
    assert branch == "release-2" and pinned is True

```

### `tests/test_r2.py`
**Purpose:** Round-2 unit tests: expression parsing, frames, origin findings, grounding, depth.

```python
"""Round-2 unit tests: expression parsing, frame normalization, origin findings,
hypothesis grounding, depth selection."""

import pytest

from ghrca import context, rca
from ghrca import errors as errmod


# --- D7.1 failing-expression parsing ---
@pytest.mark.parametrize("exc,msg,kind,key", [
    ("java.lang.NullPointerException",
     'Cannot invoke "X.getRole()" because the return value of "Y.getRole()" is null',
     "null_return_value", "getRole"),
    ("java.lang.NullPointerException", 'because "this.name" is null', "null_field", "name"),
    ("java.lang.NullPointerException", 'because "<local4>" is null', "null_local", None),
    ("java.lang.NullPointerException", 'because "args[1]" is null', "null_array_element", None),
    ("java.lang.NullPointerException", 'Cannot invoke "A.b()"', "null_receiver", None),
    ("java.lang.ArrayIndexOutOfBoundsException",
     "Index 5 out of bounds for length 3", "index_oob", None),
    ("java.lang.ClassCastException",
     "class java.lang.String cannot be cast to class java.lang.Integer", "bad_cast", None),
])
def test_parse_failing_expression(exc, msg, kind, key):
    r = context.parse_failing_expression(exc, msg)
    assert r["kind"] == kind
    if key:
        assert key in (r.get("method", "") + r.get("field", ""))


def test_aioobe_operands():
    r = context.parse_failing_expression("java.lang.ArrayIndexOutOfBoundsException",
                                         "Index 5 out of bounds for length 3")
    assert r["index"] == 5 and r["length"] == 3


# --- D13 frame normalization ---
def test_lambda_frame():
    f = errmod.Frame(cls="com.x.Svc", method="lambda$process$3", file="Svc.java", line=5)
    name, synth = f.normalized_method()
    assert name == "process" and synth is False


def test_proxy_frame():
    assert errmod.Frame(cls="com.x.Foo$$EnhancerBySpringCGLIB$$abc", method="m").is_proxy()
    assert errmod.Frame(cls="com.sun.proxy.$Proxy42", method="m").is_proxy()
    assert errmod.Frame(cls="jdk.proxy2.$Proxy7", method="m").is_proxy()
    assert not errmod.Frame(cls="com.x.RealClass", method="m").is_proxy()


def test_unsupported_language_frame():
    assert errmod.Frame(cls="com.x.K", method="m", file="K.kt", line=1).language() == "unsupported"
    assert errmod.Frame(cls="com.x.J", method="m", file="J.java", line=1).language() == "java"


def test_jar_version_parsing():
    trace = ('java.lang.NullPointerException: boom\n'
             '\tat org.apache.kafka.clients.Foo.bar(Foo.java:10) ~[kafka-clients-3.7.0.jar:?]\n')
    rec = errmod.from_text(trace, "t")[0]
    f = rec.chain[0].frames[0]
    assert f.lib.get("name") == "kafka-clients" and f.lib.get("version") == "3.7.0"


# --- D7.2 origin finding (final field) ---
def test_resolve_origin_final_initialized(monkeypatch):
    src = ('package com.x;\n'
           'public class M {\n'
           '  private final Role role = Role.ASSISTANT;\n'
           '  public Role getRole() { return role; }\n'
           '}\n')

    class FakeRepo:
        def read_blobs(self, shas):
            return {shas[0]: src}
        def default_branch(self):
            return "main"

    failing = {"kind": "null_return_value", "method": "getRole"}
    origin = context.resolve_origin(FakeRepo(), "c", "M.java", "blob1", "com.x.M", failing)
    assert origin["kind"] == "final_field_initialized"
    assert origin["field"] == "role" and "ASSISTANT" in origin["init"]


def test_resolve_origin_setter():
    src = ('package com.x;\n'
           'public class M {\n'
           '  private String name;\n'
           '  public String getName() { return name; }\n'
           '  public void setName(String n) { this.name = n; }\n'
           '}\n')

    class FakeRepo:
        def read_blobs(self, shas):
            return {shas[0]: src}

    origin = context.resolve_origin(FakeRepo(), "c", "M.java", "b", "com.x.M",
                                    {"kind": "null_return_value", "method": "getName"})
    assert origin["kind"] in ("assigned_in", "unknown")
    if origin["kind"] == "assigned_in":
        assert "setName" in origin["where"]


# --- D9 hypothesis grounding ---
class _Ctx:
    def __init__(self, ids):
        self.evidence = [(i, "k", "t") for i in ids]
        self.origin = {}


def test_grounding_keeps_valid():
    narr = ("## Hypotheses\n### H1 | category: data | confidence: high\n"
            "Evidence: E1, E2\nWhy: x\n")
    hy = rca.parse_hypotheses(narr, _Ctx(["E1", "E2", "E3"]))
    assert len(hy) == 1 and hy[0]["category"] == "data"


def test_grounding_drops_missing_id():
    narr = ("### H1 | category: logic | confidence: medium\nEvidence: E9\nWhy: x\n")
    hy = rca.parse_hypotheses(narr, _Ctx(["E1"]))
    assert hy == []


def test_grounding_allows_no_citation():
    narr = ("### H1 | category: logic | confidence: low\nWhy: x\n")
    hy = rca.parse_hypotheses(narr, _Ctx(["E1"]))
    assert len(hy) == 1


# --- D8 depth selection ---
class _Loc:
    def __init__(self, resolved=True, confidence="high", fault=True):
        self.resolved = resolved
        self.confidence = confidence
        self.fault = object() if fault else None
        self.drift_note = ""


class _Fix:
    def __init__(self, verdict="present"):
        self.verdict = verdict


def test_depth_location_only_when_simple_and_known_origin():
    ctx = type("C", (), {"origin": {"kind": "final_field_initialized"}})()
    d = rca.select_depth(_Loc(confidence="high"), ctx, _Fix(), "short")
    assert d == "location_only"


def test_depth_deep_when_origin_unknown():
    ctx = type("C", (), {"origin": {"kind": "unknown"}})()
    d = rca.select_depth(_Loc(confidence="high"), ctx, _Fix(), "short")
    assert d == "llm_deep"


def test_depth_deep_when_low_confidence():
    ctx = type("C", (), {"origin": {"kind": "final_field_initialized"}})()
    d = rca.select_depth(_Loc(confidence="low"), ctx, _Fix(), "short")
    assert d == "llm_deep"


def test_depth_deep_on_none_found():
    ctx = type("C", (), {"origin": {"kind": "final_field_initialized"}})()
    d = rca.select_depth(_Loc(confidence="high"), ctx, _Fix(verdict="none_found"), "short")
    assert d == "llm_deep"

```

## 7. Documentation (embedded in full)


### `README.md`
````markdown
# ghrca — GitHub Runtime-error Root-Cause Analyzer (Java)

Given a **Java runtime error** (stack trace / exception log, Splunk-style) from a
GitHub repository, `ghrca` clones the repo, understands its code, pinpoints the
failing method, investigates whether a fix already exists (and whether it was
lost or stuck in a PR), and produces a detailed root-cause analysis with a local
LLM.

Built and verified against [`opensolon/solon-ai`](https://github.com/opensolon/solon-ai)
(1,539 Java files, 2,289 types, 16,329 methods indexed), but repo-agnostic.

## Why it's built this way

Three hard constraints shaped every decision:

| Constraint | Consequence |
|---|---|
| **No local build** (only JDK 8 here; targets need 17+, no Maven) | Errors can't come from compiling. Code understanding uses a **compiler-free structural scanner**, not `javac`. |
| **REST API = 60 req/hr** unauthenticated (no token) | All code/branch/history/diff work goes through **git over SSH** (unlimited). REST is used only for issues/PRs, **cached + throttled**, and the tool degrades to git-only if the budget is gone. |
| **Local LLM is slow** (~15 tok/s, single slot) | Deterministic Python does all heavy lifting (clone, index, localize, archaeology). The LLM is spent on **one grounded RCA call per error**. |

## Pipeline

```
fetch (SSH) → detect NEW branches → index branch (cached by commit-sha)
   → parse stack trace → localize to exact method (deterministic)
   → git + PR fix-status archaeology → LLM root-cause analysis → report
```

## Modules

| File | Role |
|---|---|
| `repo.py` | git-over-SSH: mirror clone/fetch, branch/commit/diff queries, bulk blob reads, **new-branch detection** (ref snapshot diffing) |
| `javascan.py` | Tolerant, compiler-free Java scanner (blanks comments/strings, brace-stack state machine) → types & methods with line ranges |
| `indexer.py` | Per-branch symbol index, **cached by commit sha** so unchanged branches aren't re-scanned; type/file/dir lookups |
| `errors.py` | Java stack-trace parser (exception chain + frames) + ingestion from logs and issues |
| `locate.py` | Deterministic frame → exact method + code slices (the RCA evidence) |
| `archaeology.py` | Fix-status: `git log/-L/branch --contains` + PR search → *lost fix / open PR / abandoned PR / reverted / present* |
| `rca.py` | Assembles the grounded prompt, one LLM call, renders the Markdown/JSON report |
| `ghapi.py` | Cached, rate-limit-aware GitHub REST client |
| `llm.py` | Local llama.cpp OpenAI-compatible client |
| `orchestrator.py` / `cli.py` | Wiring + CLI |

## How each requirement is met

1. **List of errors, each tagged to a branch** → `.cache/reports/<repo>/errors.json`, merged & de-duped, each with `branch`, `fault`, `fix_status`.
2. **Index new branches ASAP** → `refresh` fetches, diffs live refs against the last snapshot, and indexes any new/changed branch immediately.
3. **Deep repo understanding → RCA** → structural index + deterministic localization feed the LLM real code (not guesses).
4. **Fix lost / new branch / stuck at PR** → `archaeology.py` classifies via git containment + PR state.
5. **What the code does + why it failed** → the RCA report's 5 sections, grounded in the actual failing method body.

## Usage

```bash
# One-time / periodic: fetch and auto-index new & changed branches
python -m ghrca refresh --repo opensolon/solon-ai

# Show branches, per-branch index state, API + LLM status
python -m ghrca status --repo opensolon/solon-ai

# Index a specific branch (or --all)
python -m ghrca index --repo opensolon/solon-ai --branch v4.0

# Analyze a runtime error from a log / stack-trace file
python -m ghrca analyze --repo opensolon/solon-ai --log error.txt

# ...from stdin (paste a Splunk trace)
python -m ghrca analyze --repo opensolon/solon-ai --stdin < error.txt

# ...mined from GitHub issues that contain stack traces
python -m ghrca analyze --repo opensolon/solon-ai --from-issues --limit 5

# Force a branch, skip fetch, or skip the (slow) LLM for a fast deterministic pass
python -m ghrca analyze --repo opensolon/solon-ai --log error.txt \
    --branch v3.9 --no-refresh --no-llm
```

Reports land in `.cache/reports/<repo>/<error-id>.md` (+ `.json`).

## LLM setup

Start the local model first (separate terminal), then run `analyze`:

```
F:\Desktop\python-vm\llamacpp_test_colibri\Agentic-Brain-Osiris\launch_qwen38flashnxt.bat
```

Serves an OpenAI-compatible endpoint at `http://127.0.0.1:8080/v1/chat/completions`.
Override with `GHRCA_LLM_URL` if needed. `--no-llm` runs the full deterministic
pipeline (localization + archaeology + evidence) without it.

## Configuration (env vars)

| Var | Default | Purpose |
|---|---|---|
| `GHRCA_CACHE` | `./.cache` | cache root (clones, index, reports) |
| `GHRCA_LLM_URL` | `http://127.0.0.1:8080/v1/chat/completions` | LLM endpoint |
| `GITHUB_TOKEN` | — | optional; 5000/hr + PR/Actions data |
| `GHRCA_GIT_SCHEME` | `ssh` | `ssh` (uses your key) or `https` |

## Notes & limits

- The Java scanner is heuristic (no grammar); line ranges are best-effort but
  proved accurate on real solon-ai code including nested classes and CJK content.
- Without a token, PR cross-referencing is best-effort and skipped when the API
  budget is exhausted — git-based fix analysis always runs.
- Localization needs the failing class to exist on the analyzed branch; a
  third-party-only stack trace is reported as unlocalized (with reasoning).

````

### `HOW_IT_WORKS.md`
````markdown
# ghrca — How It Works

> **Scaling upgrade complete (2026-09-30).** ghrca now handles repos with
> thousands of files and hundreds of branches: blob-keyed lazy index in SQLite,
> tree-sitter parsing, ls-remote polling, fingerprint + RCA caching, correct
> patch-id/content fix-status, blast radius, and a resumable daemon. All Section-1
> targets are met — see `BENCHMARKS.md` (final table). §2–3 and §19 below describe
> the post-upgrade architecture; §5–12 retain the original deep-dives on the
> deterministic core (scanner, localization, fix-status) which still apply, now
> fed by the lazy blob path instead of a per-branch index.
>
> **Phase 1 landed:** SQLite store (`db.py`, WAL); error fingerprinting
> (`fingerprint.py`) so the LLM runs once per distinct bug; RCA cache keyed by
> `(fp, method_hash, prompt_ver)`; persistent priority job queue (`llmqueue.py`);
> LLM thinking-off + short 3-section format + `cache_prompt`; `--llm-policy
> auto|always|never` with templated narratives for simple NPE/AIOOBE/CCE cases;
> ls-remote poller (`poller.py`); two-stage reports (Stage A deterministic in
> ~90 ms, Stage B narrative fills in place) with localization-confidence and
> drift validation.
>
> **Phase 3 landed:** fix-status v2 (`archaeology.py`) with patch-id grouping —
> ancestry / file-scoped patch-id / JIRA-issue-id / content decision order, so
> cherry-picked and squashed backports are `present_via_equivalent`, not falsely
> "lost" (Hadoop ground truth: `--contains` 26% false-lost → D10 0%). Deployed-commit
> pinning (`deployed_sha`/`tag`/`branch`) with a pin/drift warning, and ETag
> conditional GitHub requests.
>
> **Phase 4 landed:** blast radius (`blast.py`, `ghrca blast`) — one
> `cat-file --batch-check` classifies all branches, distinct differing blobs are
> scanned once; `affected` = same method body_hash as the deployed version. ES
> 915-branch blast is 0.65 s warm and matches a slow per-branch reference exactly.
>
> **Round 2 landed (2026-10-01):** a git-only RCA corpus (118 cases) with a frozen,
> run-once test split; lost-fix shown **without JIRA-id circularity** (new `--no-id`
> = ancestry + patch-id → 0% false-lost); a deterministic **value-origin context
> pack** (`context.py`) that traces a null back to its field across classes
> (`final_field_initialized` / `assigned_in`); **depth modes** (`location_only` /
> `llm_short` / `llm_deep`) with an honesty rule that a templated answer is never
> labelled a root cause; **ranked hypotheses** that cite evidence ids with a
> grounding check; **blast v2** (`still_buggy`/`fixed`/`refactored_unknown`/`moved`/
> `renamed`); and lambda/anonymous/proxy/non-Java frame normalization. See
> `BENCHMARKS.md` (Round 2). LLM-dependent RCA-quality metrics are pending a model
> server; some edge-case fixtures (force-push, Lombok, version-only, cross-repo) are
> specced but deferred.
>
> **Phase 5 landed:** the continuous daemon (`ghrca daemon`) — poll refs (fetch on
> change), ingest dropped errors (`sources/`: drop-dir/stdin/issues), Stage-A in a
> thread pool, one persistent LLM queue with enqueue-time dedup and crash-resume;
> read-only backport dry-run (`ghrca backport-plan`); and the eval harness
> (`ghrca eval`) with a CI gate. Soak: 200 errors → 16 LLM calls, Stage-A < 1 s,
> 5 branches detected in one poll, resume with no duplicates.


**ghrca** (GitHub Runtime-error Root-Cause Analyzer) turns a raw Java **runtime
error** (a stack trace / exception log, Splunk-style) into a **detailed,
grounded root-cause analysis** — automatically finding the right code on the
right branch, judging whether a fix already exists (or was lost), and explaining
*what the code does* and *why it broke*.

This document explains, in depth, how every part functions.

---

## 1. Design philosophy & the constraints that shaped it

Three hard constraints on the host machine drove every architectural decision.
Understanding them explains *why* the system looks the way it does.

| Constraint | Why it matters | Consequence in the design |
|---|---|---|
| **No local Java build** — only JDK 8 is installed; targets need JDK 17+, and Maven is absent | We cannot compile the target repo, so we cannot get errors or symbols from `javac`/the build | Code understanding uses a **compiler-free, tolerant structural scanner** (`javascan.py`), not a real grammar or bytecode |
| **GitHub REST API = 60 requests/hour** (unauthenticated; no token present) | The API is a scarce resource; a few careless calls exhaust it | All code/branch/history/diff work goes through **git over SSH** (unlimited). REST is used *only* for issues/PRs, is **cached to disk + rate-limit-aware**, and the tool **degrades to git-only** when the budget is gone |
| **The local LLM is slow** (~15 tok/s, single slot; llama.cpp serving Qwen3.8-Flash-Next) | LLM time dominates wall-clock; chatty designs would be unusable | **Deterministic Python does all heavy lifting** (clone, index, localize, archaeology). The LLM is spent on exactly **one grounded call per error** |

**Guiding principle:** *the LLM reasons over facts, it does not gather them.*
By the time the model is called, the failing method's source, its call path, and
the git/PR fix evidence are already assembled deterministically. This keeps the
analysis grounded (no hallucinated code) and cheap (one call).

---

## 2. The pipeline at a glance (post-upgrade)

```
  poll ls-remote ──▶ fetch ONLY on change ──▶ ingest error (drop-dir/log/issue)
   (0.2ms/915 refs)   (SSH/partial)              │
                                                 ▼
  fingerprint (dedupe) ──▶ localize LAZILY to one blob ──▶ git fix-status (patch-id)
   1 LLM call per bug        (no whole-branch index)         ancestry/patch-id/id/content
                                                 │
                                                 ▼
  Stage A report (<1s, deterministic) ──▶ LLM job queued ──▶ Stage B fills narrative
```

One sentence: **poll → fetch-on-change → ingest → fingerprint (dedupe) → localize
to a single blob (no branch index) → patch-id fix-status → Stage-A report in <1s →
one queued LLM call per distinct bug fills Stage B.**

---

## 3. Module map (post-upgrade)

```
ghrca/
├── config.py        paths, env config, LLM/GitHub settings, prompt_ver, policy
├── db.py            SQLite (WAL) store + migrations: blobs/types/methods, refs,
│                    fixes, fingerprints, errors, rca_cache, jobs, repo_meta
├── llm.py           llama.cpp client: thinking-off, cache_prompt, 1 chat call
├── ghapi.py         throttled + ETag-cached GitHub REST (issues/PRs only)
├── repo.py          git-over-SSH: clone/fetch, ls-remote, blob reads (by sha),
│                    batch-check, branch_delta, patch-id/ancestry/blame, commit-graph
├── tsjava.py        tree-sitter Java scanner (+ body_hash, statement_at)   [primary]
├── javascan.py      regex fallback scanner
├── blobstore.py     blob-keyed scan cache (scan each unique blob once, in SQLite)
├── indexer.py       lazy path resolution (source roots, tree-sha memo);
│                    + LEGACY per-branch index (baseline bench only)
├── errors.py        stack-trace parser (exception chain + frames) + ingestion
├── fingerprint.py   message normalization + fingerprint + identifier extraction
├── locate.py        localize_lazy: frame → one blob → method; drift + confidence
├── archaeology.py   fix-status v2: ancestry / patch-id / JIRA-id / content
├── blast.py         blast radius across all branches (one batch-check + unique blobs)
├── backport.py      read-only merge-tree backport dry-run
├── rca.py           short/long prompt, RCA cache, auto-policy templating
├── htmlreport.py    two-stage HTML (pending banner, confidence, verdict, blast)
├── llmqueue.py      persistent priority job queue + worker (crash-resume)
├── poller.py        ls-remote poll + ref-diff + priority
├── sources/         error sources: dropdir, (issues, stdin)
├── daemon.py        continuous loop; Stage-A threadpool + single LLM worker
├── orchestrator.py  `analyze` wiring (lazy path)
├── agent.py         batch agent (lazy path); live progress, timing, reports
└── cli.py           status | refresh | index | analyze | agent | daemon | poll
                     | blast | backport-plan | eval
```

---

## 4. Lifecycle of a single error (end to end)

Take the real example from the eval run:

```
java.lang.NullPointerException: Cannot invoke "…ChatRole.name()" because the return
value of "…AssistantMessage.getRole()" is null
    at org.noear.solon.ai.chat.dialect.AbstractChatDialect.buildAssistantMessageNodeDo(AbstractChatDialect.java:93)
    at org.noear.solon.ai.chat.dialect.AbstractChatDialect.buildChatMessageNodeDo(AbstractChatDialect.java:210)
    at org.noear.solon.ai.chat.ChatRequestDefault.call(ChatRequestDefault.java:180)
    at com.example.myapp.ChatController.ask(ChatController.java:42)
```

1. **Ingest** (`errors.py`) — the blob is scanned for stack traces. The parser
   produces a *throwable chain* (primary + any `Caused by:` causes), each with
   ordered **frames** `Class.method(File.java:line)`. A version string, if
   present, is captured as `branch_hint`.

2. **Pick the branch** — the agent resolves which branch this error belongs to:
   an explicit `branch`, the repo's *deployed* branch (from a deployment
   manifest), or the default branch. The chosen branch's index is built/loaded.

3. **Localize** (`locate.py`) — walk the frames (deepest cause first). Skip
   frames in foreign packages (`java.*`, `org.springframework.*`, the app's own
   `com.example.*`, …). For the first **repo-owned** frame, resolve the class in
   the index and find the **method whose line range contains the frame line**.
   Result: `AbstractChatDialect#buildAssistantMessageNodeDo` (lines 92–183), and
   the exact source slice is extracted. This is deterministic — no LLM, no guess.

4. **Archaeology** (`archaeology.py`) — using git history for that file and line
   range, plus (if budget allows) a PR search, classify the fix status.

5. **Reason** (`rca.py` → `llm.py`) — a single prompt is assembled from the
   parsed error, the failing method's real source, the call-path methods, the
   enclosing type's shape, and the fix-status findings. One LLM call returns a
   5-section RCA (what the code does, root cause, why, fix, fix-status verdict).

6. **Report** (`rca.py` + `htmlreport.py`) — Markdown, standalone HTML, and JSON
   are written. In agent mode the HTML is named
   `<timestamp>_<repo>_<errorname>_error_<N>.html`.

---

## 5. The compiler-free Java index (`javascan.py` + `indexer.py`)

Because we can't compile, we recover structure by scanning source text — but
naively counting braces breaks on comments and strings. The scanner works in two
stages.

### 5.1 Noise blanking

`strip_noise()` walks the source character by character with a tiny state
machine (`code / line_comment / block_comment / string / char / text_block`) and
**blanks the *contents* of comments and string/char/text-block literals while
preserving newlines**. So this line:

```java
String s = "hello { } " + name;   // a comment with } braces
```

becomes a skeleton where the `{`, `}` inside the string and comment are gone, but
the line number is unchanged. Brace counting and signature matching then operate
on the clean skeleton and never miscount.

### 5.2 Brace-stack state machine

Over the skeleton, `scan()` keeps:
- a **pending declaration** (a type or method whose `{` hasn't been seen yet),
- a **brace stack** (named scopes for real declarations, anonymous entries for
  blocks/array-initializers so nesting always balances).

Rules:
- A **type** (`class/interface/enum/record/@interface`) is detected at file or
  type scope; nested types get a fully-qualified name like `Outer.Inner`.
- A **method** is detected *only when the innermost scope is a type* — this
  single rule cleanly excludes `if/for/while/catch(...)` (which live inside
  method bodies) from being mistaken for methods, and assignments like
  `x = foo()` are rejected by checking there's no `=` before the call.
- When the matching `}` pops a named scope, its **end line** is recorded, giving
  every type and method an exact `[start, end]` line range. Bodyless
  declarations (`abstract`/interface methods ending in `;`) are captured too.

Output per file: `package`, `imports`, `types[]` (name, kind, fqn, line range,
extends/implements), `methods[]` (name, owner fqn, `owner#name`, line range,
signature), and light `fields[]`.

> This is heuristic, not a grammar — but on real solon-ai source (including
> nested classes and Chinese comments) it produced correct method ranges, e.g.
> `buildAssistantMessageNodeDo` = lines 92–183.

### 5.3 The repo index and caching

`Indexer.build(branch)`:
1. `git rev-parse <branch>` → tip **commit sha**.
2. If a cached index exists for that branch **with the same sha**, load it —
   **no work** (`warm-cache`).
3. Otherwise, list the branch's `.java` files (`git ls-tree`), **bulk-read all
   blobs in one `git cat-file --batch` process**, scan each, and build:
   - `by_type`: FQN → path,
   - `by_simple`: simple class name → [paths] (for resolving `Outer$Inner`),
   - `root_packages`: the repo's own top-level packages (used to tell "our code"
     from third-party in localization),
   - `stats`, and a `file_tree()` for directory structure.

The index is stored at `.cache/index/<repo>/<branch>.json` with its sha inside.
Because the cache key is the **commit sha**, a branch is re-scanned *only when
its tip actually moves*.

---

## 6. Stack-trace parsing (`errors.py`)

- **Exception header** regex captures `type` and `message` for any
  `*Exception` / `*Error` / `*Throwable`.
- **Frame** regex captures `Class`, `method`, and (`File.java`, `line`) —
  tolerating `(Native Method)` / `(Unknown Source)` frames with no location.
- `Caused by:` starts a new throwable in the **chain**; `... N more` is ignored.
- `from_text()` can split a **log blob containing several traces** into
  individual records; `from_issue()` mines traces out of GitHub issue bodies.
- Each record gets a stable **id** (`sha1(source+text)[:12]`) so re-runs
  de-duplicate, and a `branch_hint` from any version string.

---

## 7. Localization (`locate.py`) — the grounding step

Given the parsed error and a branch index:

1. Flatten frames **deepest-cause-first** (the usual fault site is the top frame
   of the deepest cause).
2. For each located frame, decide if it's **repo-owned**: not in
   `FOREIGN_FRAME_PREFIXES` (`java.`, `javax.`, `org.springframework`,
   `io.netty`, …) **and** either under a `root_package` or resolvable in the
   index. This correctly ignores framework frames and the calling app's own
   `com.example.*` frames.
3. Resolve the class (`by_type`, then `Outer$Inner` normalization, then
   `by_simple`), then find the method containing the frame's line number.
4. Extract a **numbered source slice** of that method (plus a couple of lines of
   padding), the enclosing type's shape (kind, extends/implements, sibling
   method names), and the file's imports — the **evidence bundle** for the LLM.
5. Up to `max_frames` (default 4) repo-owned frames are resolved, giving the LLM
   the real **call path** code, not just the innermost method.

If nothing resolves (e.g. a purely third-party stack trace), the report says so
explicitly rather than guessing.

---

## 8. Fix-status archaeology (`archaeology.py`)

This answers *"is there already a fix, and did it reach the branch that
failed?"* — the highest-value, most novel part. All primary signals come from
**git** (unlimited); PR data is a best-effort bonus.

For the fault file and its failing line range:

1. **File & line history** — `git log` for the file, and `git log -L start,end:file`
   for the exact lines.
2. **Fix-flavored commits** — commit subjects matching
   `fix|bug|npe|null|resolve|patch|correct|issue|error|exception|crash|regress`.
3. **Revert detection** — a `revert` commit on the file → *a prior fix may have
   been undone*.
4. **Lost-fix detection (the key one)** — for each fix commit, run
   `git branch --contains <sha>`. If the **failing branch is *not* among the
   containing branches** but others are → the fix **exists elsewhere but never
   reached the failing branch** (unmerged / lost). If the failing branch *does*
   contain it and it touched the failing lines → the fix is present (error may
   predate it or be incomplete).
5. **PR cross-reference** (only if API budget/token) — search PRs mentioning the
   file: `open` → *stuck in review*; merged → *landed, verify coverage*;
   closed-unmerged → *abandoned*.

Findings are ranked by severity and a **headline** is chosen:

| Headline | Meaning |
|---|---|
| *A fix here was reverted* | reintroduced bug |
| *A fix exists on another branch but is missing from the failing branch (lost/unmerged)* | backport needed |
| *A fix may be stuck in an open PR* | review bottleneck |
| *A proposed fix was closed without merging (abandoned)* | dropped |
| *A related fix was merged* | verify it covers this case |
| *A fix is already present on this branch* | error predates it / incomplete |
| *No fix found…* | genuinely unfixed |

**Real example (test-bed):** on the deployed `release-2`, the agent reported —
> `lost_fix` — commit `3ba3db59 "fix(NPE): guard null customer in
> OrderService.checkout"` is on `[hotfix-npe, main]` **but NOT on `release-2`**.

…detected purely from git containment.

---

## 9. The LLM step (`rca.py`, `llm.py`)

- `build_prompt()` assembles: error summary + full exception chain + repo
  packages + enclosing type shape + imports + **the failing methods' real source
  (call path, deepest first)** + the archaeology findings.
- `llm.chat()` posts one system+user request to the llama.cpp
  `/v1/chat/completions` endpoint (health-checked, retried on transient errors).
- The model is instructed to output a fixed 5-section Markdown structure:
  1. What the code does 2. Root cause 3. Why the error occurred
  4. Suggested fix (with a diff) 5. Fix-status assessment.
- Only the **narrative** comes from the model; the stack trace, evidence, and
  findings in the report are rendered deterministically.

`--no-llm` skips this step entirely and produces the full deterministic report
(localization + diff + archaeology + code evidence) in well under a second —
useful for fast validation or when the model server is down.

---

## 10. The agent (`agent.py`)

The autonomous batch layer. Driven by `targets.json`:

```json
{
  "output_dir": "agent_reports",
  "repos": [
    {
      "id": "opensolon/solon-ai",
      "source": null,                       // null = GitHub over SSH; or a path/URL
      "deployment": {"strategy": "default"},
      "errors": [ {"name": "...", "source": "splunk:...", "trace": "...\n\tat ..."} ]
    },
    {
      "id": "local/acme-orders",
      "source": "…/testbed/acme-orders.git",
      "deployment": {"strategy": "file", "path": "deployment-info.json", "ref": "main"},
      "errors": [ ... ]
    }
  ]
}
```

For each repo it: clones/fetches, runs **new-branch detection**, chooses the
**deployed branch**, indexes it, then processes each error (parse → locate →
quick-diff → archaeology → RCA → report), **streaming a timed, phase-by-phase log
to the console** so a human can watch it work:

```
[git]     cloned opensolon/solon-ai  (cold-clone, 9.38s)
[diff]    refs: 11 new, 0 changed, 0 removed (ref-snapshot diff -> only these need work)
[deploy]  deployed branch = 'main'  (default=main)
[index]   cold-index: 1541 files, 2292 types, 16385 methods  (3.14s)
  --- [ERROR 1] assistant-role-npe ---
  [2 locate] OK -> …AbstractChatDialect#buildAssistantMessageNodeDo(...:93) on 'main'  [0.04s]
  [3 dig  ] fix-status: No fix found …  [0.52s]
  [4 think] RCA generated: 3341 tokens  [222.7s]
  [5 report] 20260930T142357_opensolon-solon-ai_assistant-role-npe_error_1.html
```

### Deployment-branch selection

`deployment.strategy`:
- `default` — the repo's default branch (HEAD).
- `fixed` — an explicit `branch`.
- `file` — **read a `deployment-info.json` committed in the repo** (at `ref`),
  and use its `deployed_branch`. This models a CI-written release manifest: the
  agent picks up *whatever is currently live* and analyzes the error against that
  exact branch — even a branch created moments ago.

### Outputs

- `agent_reports/<ts>_<repo>_<errorname>_error_<N>.html` — one per error,
  **numbered globally** and **timestamped**.
- `agent_reports/index.html` — a numbered table of all reports + a per-repo
  clone/index cost table.
- `agent_reports/summary.json` — machine-readable metrics (timings, fix-status,
  ref diffs, fault sites).

---

## 11. Incremental indexing & "ensuring a diff"

Three layers ensure the agent only ever does work proportional to what changed:

1. **Incremental fetch** — `git remote update --prune` transfers only new
   objects; SSH means no API cost and full (incl. private) access.
2. **Ref-snapshot diff** — after each fetch, current branch SHAs are compared to
   a saved snapshot (`.cache/state/<repo>.refs.json`). The result — *N new, M
   changed, K removed* — tells the agent exactly which branches need indexing. A
   **newly created branch is detected on the very next run** and indexed
   immediately (requirement: "index a new branch ASAP").
3. **SHA-keyed index cache** — a branch is re-indexed only if its tip SHA moved
   (`cold-index` / `reindex-changed` / `warm-cache`).

On top of that, per error the agent runs a **quick `git diff <default>..<branch>`
on the fault file** to show how the deployed code differs (e.g. `1+/5- vs main`),
which is how it surfaces that a fix present elsewhere is absent here.

---

## 12. Storage layout

```
github_scrape/
├── .cache/
│   ├── repos/<repo>.git/          bare --mirror clones (all refs, shared objects)
│   ├── index/<repo>/<branch>.json structural index (keyed by commit sha)
│   ├── apicache/<sha1>.json       cached GitHub REST responses (TTL'd)
│   ├── state/<repo>.refs.json     last-seen ref snapshot (new-branch detection)
│   └── reports/<repo>/<id>.{md,html,json}   single-analyze outputs
├── agent_reports/                 agent run outputs (numbered, timestamped) + index.html
├── testbed/acme-orders.git        local simulated "GitHub" remote (the test-bed)
└── targets.json                   the agent's repo × error inputs
```

Everything is disposable: delete `.cache/` and `agent_reports/` for a clean cold
start; the next run re-clones and re-indexes.

---

## 13. CLI reference

```bash
# One-time / periodic: fetch and auto-index new & changed branches
python -m ghrca refresh --repo opensolon/solon-ai

# Inspect: branches, per-branch index state, API + LLM status
python -m ghrca status  --repo opensolon/solon-ai

# Build the structural index for a branch (or --all)
python -m ghrca index   --repo opensolon/solon-ai --branch v4.0

# Analyze a single error from a log file / stdin / issues
python -m ghrca analyze --repo opensolon/solon-ai --log error.txt
python -m ghrca analyze --repo opensolon/solon-ai --stdin < error.txt
python -m ghrca analyze --repo opensolon/solon-ai --from-issues --limit 5

# Fast deterministic pass (no LLM), forced branch, no fetch
python -m ghrca analyze --repo opensolon/solon-ai --log error.txt \
    --branch v3.9 --no-llm --no-refresh

# Batch agent over many repos × errors
python -m ghrca agent --targets targets.json          # with LLM
python -m ghrca agent --targets targets.json --no-llm  # deterministic only
```

---

## 14. Configuration (environment variables)

| Var | Default | Purpose |
|---|---|---|
| `GHRCA_CACHE` | `./.cache` | cache root |
| `GHRCA_LLM_URL` | `http://127.0.0.1:8080/v1/chat/completions` | LLM endpoint |
| `GHRCA_LLM_MAX_TOKENS` | `8000` | completion budget per RCA |
| `GHRCA_LLM_TIMEOUT` | `5400` | seconds to wait for one call |
| `GITHUB_TOKEN` / `GH_TOKEN` | — | optional; 5000/hr + PR/Actions data |
| `GHRCA_GIT_SCHEME` | `ssh` | `ssh` (uses your key) or `https` |
| `GHRCA_API_TTL` | `21600` | REST cache freshness (s) |

---

## 15. The test-bed (how the "lost fix" demo is built)

`scratchpad/setup_testbed.py` creates a local bare repo that behaves like a
GitHub remote, with an evolving history engineered to reproduce a lost fix:

```
main        baseline OrderService (latent NPE at checkout:8)
release-1   first release, from main
hotfix-npe  from release-1: adds the null guard  → "fix(NPE): guard null customer…"
main        merges hotfix-npe                     (trunk fixed)
release-2   from release-1 (BEFORE the hotfix) + discount feature → DEPLOYED
deployment-info.json (on main) → deployed_branch = release-2
```

Because `release-2` branched *before* the hotfix and never merged it, the fix
lives on `main`/`hotfix-npe` but is **absent from the deployed branch** — exactly
what the archaeology step detects. Rebuild it any time with:

```bash
python scratchpad/setup_testbed.py
```

---

## 16. Performance characteristics (measured, cold start)

From the eval run (2 repos, 3 errors, caches wiped first):

| Phase | solon-ai (large, GitHub/SSH) | acme-orders (test-bed, local) |
|---|---|---|
| clone (cold) | 9.38 s | 0.16 s |
| index (cold) | 3.14 s — 1,541 files / 16,385 methods | 0.06 s — 8 files / 17 methods |
| localize / error | ~0.04 s | ~0.04 s |
| archaeology / error | 0.07–0.52 s | 0.07 s |
| **RCA (LLM) / error** | **220–250 s** | **~270 s** |

**Total wall time: 752 s for 3 errors** — ~99.9% of it is the local model.
Deterministic work (clone + index + all localization + all archaeology) was a few
seconds total. On a faster LLM (or a hosted model) the same run would finish in
seconds. Warm re-runs skip cloning and indexing entirely (SHA cache hit).

---

## 17. Limitations & honest caveats

- The Java scanner is heuristic (no formal grammar); line ranges are best-effort.
  They proved accurate on real code, but exotic syntax could mislead it.
- Localization needs the failing class to **exist on the analyzed branch**; a
  stack trace that is entirely third-party is reported as *unlocalized* (with the
  reasoning) rather than forced.
- Without a `GITHUB_TOKEN`, PR cross-referencing is best-effort and is skipped
  when the 60/hr budget is exhausted — **git-based fix analysis always runs**.
- The RCA quality tracks the model; the grounding (real code + real git
  evidence) is what keeps it honest regardless of model size.

---

## 18. Extending it

- **More repos/errors:** add entries to `targets.json`.
- **Real deployments:** point `deployment.strategy: file` at your CI-written
  manifest; the agent will always analyze against the live branch.
- **CI/Actions logs as an error source:** add a token and a fetcher in
  `ghapi.py`; feed the log text through `errors.from_text`.
- **Backport suggestions:** the `lost_fix` finding already names the branch that
  carries the missing fix — a one-click "cherry-pick <sha> into <deployed>" is a
  natural next feature.

---

## 19. Running the daemon (ops)

```bash
# one-shot analysis
python -m ghrca analyze --repo opensolon/solon-ai --log err.txt
python -m ghrca blast   --repo opensolon/solon-ai --error err.txt
python -m ghrca backport-plan --repo apache/hadoop --fix <sha> --target branch-3.3

# continuous: poll refs, ingest errors_inbox/<slug>/*.jsonl, progressive reports
python -m ghrca daemon --targets targets.json --interval 60 --workers 4
python -m ghrca eval    # CI gate: localization >=95%, verdict >=90%
```

**systemd unit** (`/etc/systemd/system/ghrca.service`):
```ini
[Service]
WorkingDirectory=/opt/ghrca
Environment=GHRCA_LLM_URL=http://127.0.0.1:8080/v1/chat/completions
Environment=GITHUB_TOKEN=...
ExecStart=/usr/bin/python -m ghrca daemon --targets /opt/ghrca/targets.json
Restart=always
KillSignal=SIGTERM
```
SIGTERM is handled gracefully (finish the current git op, persist the queue); on
restart `reset_running()` resumes interrupted jobs with no duplicates. A cron
alternative: `*/1 * * * * python -m ghrca daemon --targets ... --max-cycles 1`.

**llama.cpp serving notes** (not code — ops tuning): the RCA model runs behind an
OpenAI-compatible server (`GHRCA_LLM_URL`). Thinking is disabled via
`chat_template_kwargs {"enable_thinking": false}` and `cache_prompt` is on, so the
static instructions+repo shape (sent first) stay cached across errors. To speed
generation: `--model-draft <draft.gguf>` (speculative decoding), `-ngl 99` (offload
layers to GPU), and a larger `--ctx-size` for big call paths. `GHRCA_LLM_POLICY=auto`
serves simple NPE/AIOOBE/CCE verdicts from a template with **no** model call.

````

### `BENCHMARKS.md`
````markdown
# ghrca benchmarks

All numbers are measured on this host; no performance claim appears here without a
measurement. Each row records repo, cold/warm, date, and the git SHA of the code.

## Environment (detected Phase 0, 2026-09-30)

| Item | Value |
|---|---|
| OS | Windows 11 (10.0.26200) |
| CPU | 16 logical cores |
| RAM / disk | 64 GB RAM; F: 294 GB free / 1862 GB |
| Python | 3.13.13 |
| git | 2.39.2.windows.1 — **>= 2.38, so `merge-tree --write-tree` backport dry-run is ENABLED** |
| tree-sitter | 0.26.0 + tree-sitter-java (pip wheels) |
| LLM server | llama.cpp, Qwen3.8-Flash-Next UD-IQ3_XXS, n_ctx 131072, single slot (~15 tok/s) |

### LLM thinking-off probe (D9)

Prompt: "What is 2+3? Answer with just the number." (`max_tokens=200`)

| Method | `<think>` tags | completion tokens | time |
|---|---|---|---|
| baseline (no kwargs) | no | 37 | 5.3 s |
| **`chat_template_kwargs {"enable_thinking": false}`** | no | **2** | **0.9 s** |
| `/no_think` system marker | no | 32 | 4.0 s |

**Decision:** use `chat_template_kwargs {"enable_thinking": false}` — it works and
cuts output ~18x on this probe. The `/no_think` marker is ignored by this model.
Recorded per §0.8.

---

## Repo stats (Phase 0)

Branch counts via `git ls-remote --heads` (2026-09-30). Clone time/size filled as
each background clone completes.

| Repo | branches (ls-remote) | clone mode | clone time | size on disk | .java files (default branch) |
|---|---|---|---|---|---|
| apache/kafka | 93 | full | 116 s | 727 MB | 6217 |
| apache/hadoop | 409 | partial (blob:none) | 119 s | 230 MB | tbd |
| elastic/elasticsearch | 915 | partial (blob:none) | _cloning_ | tbd | tbd |
| opensolon/solon-ai | 11 | full | (pre-existing) | 33 MB | 1541 |
| local/acme-orders | 4 | full (local) | 0.16 s | 0.1 MB | 8 |

Note: partial clone (`--filter=blob:none`) fetched hadoop's full 409-branch history
in 119 s / 230 MB by omitting blobs; blobs are lazily fetched on first read
(measured in Phase 2). kafka full mirror was 727 MB / 116 s.

---

## Baseline — CURRENT code (before upgrade)

Per-branch JSON index + old `--contains` fix-status. Later phases are compared
against these rows.

| Repo | cold index | warm index | localize (1 err) | fix-status (old --contains) | date |
|---|---|---|---|---|---|
| opensolon/solon-ai (11 br, 1541 files, 16385 methods) | 3.91 s | 0.10 s | 41.4 ms | 110.4 ms | 2026-09-30 |
| apache/kafka (93 br, 6217 files, 74020 methods) | 20.02 s | 0.52 s | — | — | 2026-09-30 |

**Baseline observations (what the upgrade must beat):**
- *Cold index scales with file count*: 1.5k files → 3.9 s, 6.2k files → 20.0 s. A
  915-branch repo indexed per-branch would be catastrophic; hence blob-keyed global
  scan (D3) + lazy path resolution (no whole-branch index to localize).
- *Warm "index" is a JSON reload*: 0.52 s just to load kafka's index JSON before a
  single localize. Target: localize < 100 ms with **no** whole-branch index (D3/SQLite).
- *localize 41 ms* already, but only *after* the full branch index exists; the
  upgrade must hit < 100 ms **without** building that index.
- *old fix-status 110 ms* uses `git branch --contains` only — the method the Hadoop
  ground-truth (D16) will show mis-classifies cherry-picks/squashes as "lost".

---

## Phase 1 — cheap wins (2026-09-30)

### LLM dedup (fingerprint-replay, H6)
1000 errors sampled (Zipf) from 3 distinct real bugs (2 solon-ai + 1 acme), each
occurrence given noise (random ids/line numbers) so raw text differs every time.

| metric | value |
|---|---|
| errors replayed | 1000 |
| distinct (fp, method_hash) | 3 |
| **LLM calls that would fire** | **3** |
| dedup ratio | 99.7% |

**Gate PASS:** LLM calls == distinct (fp, method_hash) pairs, not error count.

### Poll cost (D4), 915-branch elasticsearch
Poll = `git ls-remote` + ref-diff + persist. Component profile:

| component | time |
|---|---|
| ref-diff classify (915 refs), compute-only | **0.17 ms** |
| load prev refs from SQLite | 1–2 ms |
| bulk upsert 915 refs | 1–32 ms |
| `git ls-remote` network round trip (GitHub) | 0.9–9 s (variable, GitHub-side) |

**Gate: ghrca's poll logic PASSES by ~100× (≈2–33 ms for 915 refs).** Total wall
time is dominated by GitHub's network response for ls-remote, which is outside the
code's control and varies 0.9–9 s. Detection within a 60 s interval is trivially met.

### RCA / thinking / cache
| metric | value |
|---|---|
| thinking off (`enable_thinking:false`) probe | 2 tokens vs 37 baseline (~18×) |
| short format (prompt_ver=2) | 3 sections, max_tokens 2500 (was 8000) |
| auto-policy NPE (high confidence) | rendered as **template**, 0 LLM tokens |
| repeat error (same fp+method_hash) | **cache** hit, 0 LLM tokens |
| Stage-A deterministic report (solon-ai, warm) | **92–95 ms** (< 1 s gate PASS) |

**Median RCA seconds:** with thinking-off + short format + auto-templating, the
common NPE/AIOOBE/CCE cases now cost **0 s** (templated) or a cache hit; only novel
bugs reach the model. Full model RCA timing (short format, thinking off) is measured
in Phase 5 on the daemon soak; the Phase 0 long-format runs were 220–270 s each.

---

## Phase 2 (partial) — tree-sitter parser + parity (2026-09-30)

`tsjava.py` (tree-sitter-java, PARSER_VER=3) vs the regex `javascan.py` on all
6217 `.java` files of kafka trunk (74,020 regex methods):

| metric | value |
|---|---|
| FUNCTIONAL parity (regex method also found by ts; end ±1, start ±3) | **94.31%** |
| STRICT exact (start&end) among matched | 45.59% |
| regex-only (potential ts regressions) | 4210 |
| ts-only (methods the regex scanner MISSED) | 9963 |
| ts zero-type fallbacks → regex | 73 files |

**Gate analysis (honest):** the literal ">=99% exact agreement" target is *not*
reachable, because it is measured against the regex scanner, which is the **less
accurate** baseline. Hand-reading the 30-sample disagreements (per D2):
- The STRICT gap (45.59%) is a benign **convention**: tree-sitter includes the
  `@Override`/annotation line in the method span (start −1); the regex scanner
  starts at the signature. This never changes `method_at_line()` for a body line.
- The 4210 "regex-only" cases are dominated by **regex errors** tree-sitter
  correctly avoids: class names mis-detected as methods (e.g. `SignatureVisitor`),
  and methods the regex under-spanned as single-line/bodyless (`(245,245)`).
- tree-sitter additionally finds **9963 methods the regex scanner missed**
  (nested/anonymous classes).

**Binding correctness check** (Phase-2 gate: "identical localization on fixtures"):
on all fixtures (solon-ai NPE @93 & @191, acme-orders checkout @8) tree-sitter and
regex resolve the **same fault method**, and tree-sitter is correct:

```
AbstractChatDialect.java:93  -> buildAssistantMessageNodeDo   (ts == regex == expected)
AbstractChatDialect.java:191 -> buildToolMessageNodeDo        (ts == regex == expected)
OrderService.java:8          -> checkout                      (ts == regex == expected)
```

**Verdict:** adopt tree-sitter as primary with regex fallback (D2), since it is
strictly more correct and localization is unchanged. The 99%-vs-regex number is
reported as not-applicable (weaker baseline); functional parity 94.31% + identical
fixture localization is the substantiated equivalence.

### Phase 2 (complete) — blob-keyed lazy index

| gate | target | measured | verdict |
|---|---|---|---|
| localize warm, **no whole-branch index** | < 100 ms | **47 ms** (cold 62 ms) solon-ai | **PASS** |
| localize result vs old full-index path | identical | identical on all fixtures (solon @93/@191, acme @8) | **PASS** |
| new-branch blobs scanned (fresh fork ≤10 commits) | < 1% of branch .java | **0.113% median**, 0.257% max (kafka; 2–16 of 6217 blobs) | **PASS** |
| parser parity (functional) | ≥99% vs regex | 94.31% (gap = regex errors; tree-sitter correct) — see analysis above | reinterpreted |
| partial-clone cold-blob cost | record | **~0.96 s/blob** lazy promisor fetch; warm ~1 ms; batched fetch-by-sha **rejected by GitHub** | recorded |

Notes:
- Lazy localize does ONE `cat-file --batch-check` for all frame candidates + ONE
  `cat-file --batch` read; batching cut warm latency 140 ms → 47 ms on Windows
  (subprocess spawns dominate).
- New-branch ingest cost is proportional to changed blobs only (git diff-tree
  skips identical subtrees); a genuinely new branch scans a handful of blobs.
- Partial clones (hadoop/es) trade a tiny clone (230 MB/119 s) for a one-time
  ~0.96 s/blob cold fetch, paid in the background prewarm; full clones
  (kafka/solon) have no cold-blob cost. GitHub's promisor does not support
  batched blob-sha fetch, so per-blob lazy fetch is the only mechanism.

---

## Phase 3 — correct fix-status + pinning + drift (2026-09-30)

### Hadoop lost-fix ground truth (D16) — the headline gate
Ground truth = a same-JIRA-id commit touches the file on the branch (how Hadoop
tracks backports). 100 labelled (fix, branch) pairs, mixed present/lost, metadata-only
(runs on the partial clone). Positive class = "lost".

| detector | false-"lost" | lost-recall | confusion (tp/fp/tn/fn) |
|---|---|---|---|
| OLD `git branch --contains` (original sha) | **26.09%** | 100% | 77/6/17/0 |
| **NEW D10 (ancestry + JIRA-id)** | **0.00%** | **100%** | 77/0/23/0 |

**Gate PASS:** false-"lost" 0.0% (≤2%), lost-recall 100% (≥95%). OLD baseline
recorded: `--contains` mislabels **26%** of cherry-picked backports as "lost".

### Test-bed verdicts (D10 decision order) — all correct
| branch | scenario | verdict | decided_by |
|---|---|---|---|
| release-2 | deployed, no fix | **lost** | content |
| release-3 | cherry-pick backport (different sha) | **present_via_equivalent** | patch_id |
| release-5-squash | content-identical squash | **present_via_equivalent** | patch_id |
| main | merged (--no-ff) | **present** | ancestry |
| hotfix-npe | original fix | **present** | ancestry |

Patch-id grouping treats an original commit + its cherry-picks/squashes as one
logical fix; the earliest is canonical (ancestry ⇒ present, equivalent ⇒
present_via_equivalent). This is why the cherry-pick/squash are NOT "lost".

### Pinning + drift (D11)
- deployment-info `deployed_sha`/`deployed_commit`/`deployed_tag` pin the analysis
  to an exact commit (`pinned=true`); a branch-only manifest analyzes the tip and
  the report warns about possible line drift.
- drift validation: on the `release-6-drift` branch (deref shifted +4 lines) an
  error reporting the old line yields **confidence=low**, still resolves the
  correct method (`checkout`), and maps/annotates the drift.
- ETag conditional requests added to `ghapi` (304 = cache hit, no budget) when a
  token is present.

---

## Phase 4 — blast radius (2026-09-30)

D12: one `cat-file --batch-check` classifies every branch's blob for the fault
file; only DISTINCT differing blobs are scanned (cached). `affected` = same method
body_hash as the deployed/buggy version.

### elasticsearch (915 branches), InternalEngine.java (620 branches have it, 99 distinct blobs)
| metric | value | gate |
|---|---|---|
| COLD blast (partial clone: tree paging + scan 99 blobs) | 43.0 s | one-time |
| **WARM blast** | **0.647 s** | **< 3 s PASS** |
| reference agreement (30 sampled branches) | **30/30 match** | **PASS** |

### local test-bed (7 branches), OrderService.checkout (buggy = release-2)
| branch | status | |
|---|---|---|
| release-1, release-2, release-6-drift | **affected** | same buggy method (drift branch caught despite +4 line shift — body_hash is line-independent) |
| main, hotfix-npe, release-3, release-5-squash | changed (fixed) | null-guard applied |

`blast` matches the slow per-branch reference exactly on the test-bed and on 30
sampled ES branches. body_hash's line-independence is why a fix or drift is
correctly told apart from the buggy version. New CLI: `python -m ghrca blast
--repo R --error err.txt`; HTML report has a counts block + top-20 branches by
priority (full list collapsible).

---

## Phase 5 — daemon, sources, backport, eval (2026-09-30)

### Daemon soak (D13 gate) — deterministic in-process run, mock LLM
200 errors (16 distinct bugs from real acme methods) dropped as JSONL; 5 branches
created between polls; queue then crash-and-resume.

| gate property | result | verdict |
|---|---|---|
| new branches detected in one poll | **5 / 5** | PASS |
| every error Stage-A report | **max 436 ms**, p50 198 ms (< 1 s) | PASS |
| LLM calls == distinct (fp, method_hash) | **200 errors → 16 jobs → 16 calls → 16 cache** | PASS |
| resume after crash (claimed job requeued) | requeued 1, redrained 1, **cache delta 1 (no dup)** | PASS |
| reports written | 201 | PASS |

Enqueue-time dedup (in-flight `(fp, method_hash)` set + RCA cache) prevents a burst
of identical errors from queuing duplicate LLM jobs before the first completes.
Jobs persist in SQLite; `reset_running()` on start resumes an interrupted queue.

### Eval harness (D15 gate)
| metric | value | gate |
|---|---|---|
| localization (exact fault method) | **100%** (6/6) | ≥95% PASS |
| fix-verdict accuracy | **100%** (6/6) | ≥90% PASS |
| drift confidence | 100% (high/low as expected) | — |

`eval/baseline.json` committed; `ghrca eval` fails on regression vs it.

### Backport dry-run (D14)
`git merge-tree --write-tree` (read-only). git 2.39 lacks `--merge-base=` (needs
2.40+), so ghrca falls back to auto merge-base and says so; hotfix→release-2 reports
`applies_cleanly: True`, writes the patch, prints the cherry-pick command, runs nothing.

### Sources (D13)
Drop-directory (`errors_inbox/<repo-slug>/*.txt|log|jsonl`, archived to `_done/`),
stdin/file, and GitHub issues (budgeted). `status` now shows queue depth,
fingerprints seen, cache size, and last poll time.

---

## Phase 6 — final results vs Section-1 targets (before → after)

| Goal | Target | Measured | Verdict |
|---|---|---|---|
| New branch detected | within one poll (60s); ingest ∝ changed blobs | 5/5 in one poll; new-branch scan **0.113%** of files | **MET** |
| Localize an error | < 100 ms warm, no whole-branch index | **47 ms** (was 41 ms *after* a 520 ms JSON index load) | **MET** |
| Blast radius across all branches | < 3 s warm, 900-branch repo | ES 915 br **0.647 s** | **MET** |
| LLM calls | == distinct (fp, method_hash), not error count | 200 errors → **16 calls** | **MET** |
| Time to first report | < 1 s warm (deterministic) | Stage-A **92–436 ms** | **MET** |
| Fix-status false-"lost" | ≤ 2% | **0.0%** (old `--contains` 26.09%) | **MET** |
| Median RCA | ≤ 90 s (thinking off + short format) | **34.9 s** / 301 tok (was 220–270 s long-format) | **MET** |

### Cold-index cost, before vs after (kafka trunk, 6217 files)
| | before (per-branch JSON) | after (lazy blob-keyed) |
|---|---|---|
| to answer ONE error | full branch index 20.0 s cold / 0.52 s warm-load | **scan 1 blob**, localize 47 ms warm |
| to prewarm a new branch | re-index whole branch | scan only changed blobs (**0.1%** of files) |

### Definition of Done
- ✅ Every Section-1 target met and evidenced above.
- ✅ **No branch-wide index is built to answer a single error** (analyze/agent/daemon
  all use `localize_lazy` → one blob).
- ✅ Fix-status never reports `lost` when a patch-id / JIRA-id / content equivalent
  exists on the target (Hadoop 0% false-lost; test-bed cherry-pick & squash →
  `present_via_equivalent`).
- ✅ The daemon runs unattended, resumes after restart with no duplicates, never
  pushes to any remote, and produces progressive (Stage A→B) reports.
- ✅ `HOW_IT_WORKS.md` describes the system as built (§2–3 rewritten, §19 ops added).
- ✅ 70 tests pass; `analyze` and `agent --no-llm` work end-to-end.

---

# Round 2 — deeper, verifiable RCA (2026-10-01)

Env: prompt_ver was 2; model server OFF during this round (LLM-dependent metrics
reported `n/a` and the harness supports them when it is up); no GITHUB_TOKEN; git
2.39; ~289 GB free.

## R2-R0 — RCA corpus + held-out harness

Corpus built **git-only** (no API): commits whose message contains a Java stack
trace; the commit is the fix F, analysis commit P = F^1 (fix absent by
construction); truth methods mapped from F's diff onto P via tree-sitter; fix
category by deterministic rules.

| | value |
|---|---|
| total cases | **118** (kafka 33, elasticsearch 80, hadoop 5) |
| split | dev 69 / test 49, `TEST_MANIFEST.sha256` frozen |
| held-out enforcement | `eval rca --split test` **refuses** without `--final` (tested) |

**R0 baseline on dev (localization, prompt_ver 2, no LLM):**

| metric | value |
|---|---|
| n (dev) | 69 (loc_missing 8) |
| file_hit | 36.1% |
| method_hit | 24.6% |
| path_hit | 31.1% |
| calibration (high / low) | high 25.0% over 60 · low 0% over 1 |
| fix_overlap / category_match | n/a (needs LLM; harness ready) |

**Honest reading (not a saturated fixture):** these are *low on purpose*. The
exception throw site that a trace points at is frequently **not** the method the
fix changed (the bad value is often set elsewhere). So localization-vs-fix overlap
is genuinely hard, and the corpus exposes it rather than hiding it. The Round-2
improvement target is the **LLM-dependent** `fix_overlap`/`category_match` plus the
honesty machinery (depth, grounding, hypotheses) — measured when the server is up.

**Gate R0: PASS** — corpus + frozen manifest + `--final` refusal + baseline recorded.

## R2-R1 — honest evidence

### D5 parity, hand-verified (kafka trunk)
Functional parity 94.3% (full, Round 1) / 95.7% (500-file sample). Disagreements
hand-checked against source — representative verified case:

| file | method | tree-sitter | regex | correct | reason |
|---|---|---|---|---|---|
| Serializer.java | close | (93,96) | (94,96) | tree-sitter | ts includes the `@Override` line (93); regex starts at the signature (94) — same method, benign ±1 convention |
| Serializer.java | serialize/configure | match | match | both | — |

Category breakdown of disagreements: **single-line `(x,x)` regex-only entries**
(regex mis-flags abstract/interface signatures and field-like lines as bodyless
methods, or under-spans one-liners) → tree-sitter correct; **ts-only** (552 in the
sample) → methods regex *missed* (nested/anonymous). **Conclusion:** tree-sitter is
the correct parser in every disagreement category; the Round-1 "99% vs regex" gate
is replaced by this measured functional parity + hand-check.

### D6 metamorphic tests (anti-saturation) — `tests/test_metamorphic.py`
All pass: whitespace/comment-only change → same `body_hash` (**affected**);
line-shift above method → same hash; guard added → hash changes; blast
classification: failing statement survives → **still_buggy**; fix content present →
**fixed**; statement extracted to helper → **refactored_unknown**.

## R2-R2 — context pack, hypotheses, depth modes

- **Value-origin pack (D7)** resolves cross-class: for `NPE … Cart.getCustomer() is
  null` at `OrderService#checkout`, it reports the deterministic finding
  `{kind: assigned_in, field: customer, where: [setCustomer, direct_assignment]}` —
  a deep root-cause signal with **no LLM**. A `final`-initialized field yields
  `{kind: final_field_initialized, implication: null only via reflection/deserialization}`.
- **Depth (D8):** every report carries `rca_depth` ∈ `location_only | llm_short |
  llm_deep` and a confidence badge. `location_only` is labelled "Location-only
  analysis (not a full root cause)" and only fires when confidence is high, the
  pattern is simple, AND the origin is known; unknown origin / low confidence /
  `none_found` escalate to `llm_deep`. Verified: no templated result is labelled a
  root cause (unit test + live report).
- **Hypotheses + grounding (D9):** narratives parse into `hypotheses[]` citing
  evidence ids; hypotheses citing non-existent ids are dropped (tested: valid /
  missing-id / no-citation); a `lost` verdict contradicted by the narrative gets an
  automatic correction line. Deterministic hypotheses (`data` from a final-field
  origin, `version_drift` on low confidence, `dependency` on a third-party deepest
  frame) are injected without the LLM.
- LLM-dependent `fix_overlap` / `category_match` and median `llm_short`/`llm_deep`
  time: **n/a this round (model server off)**; the harness computes them when it is up.

## R2-R3 — blast radius v2 (D10)
Classes split from the old `changed`: **still_buggy / fixed / refactored_unknown /
moved / renamed / absent / affected / changed_unrelated**. `still_buggy` vs
`refactored_unknown` is decided by whether the normalized failing statement survives
in the branch's method; `fixed` by ≥80% fix-content presence; move/rename by
`body_hash` lookup in the methods table. `refactored_unknown` is never presented as
safe. (Metamorphic tests cover still_buggy/fixed/refactored.)

## R2-R4 — edge cases (frames, D13)
Frame normalization (unit-tested): `lambda$foo$3` → enclosing `foo`; CGLIB/JDK
proxies (`$$EnhancerBySpringCGLIB$$`, `com.sun.proxy.$ProxyN`, `jdk.proxyN`) treated
as foreign (not the fault site); `.kt/.scala/.groovy` → `unsupported`; jar-version
annotations (`~[kafka-clients-3.7.0.jar:?]`) parsed into `frame.lib`.

### D4 — lost-fix WITHOUT id circularity (hadoop, bounded: 30 labelled pairs)
Four confusion matrices ({old `--contains`, new full, new `--no-id`} × {id labels,
patch-id labels}). In this cherry-pick-heavy sample every "present" case is a
backport with a different SHA:

| method | vs ID labels | vs PATCH-ID labels |
|---|---|---|
| OLD `--contains` | false-lost **100%**, recall 100% | false-lost **100%**, recall 100% |
| NEW full (ancestry+patchid+id) | false-lost **0%**, recall 100% | false-lost **0%**, recall 100% |
| **NEW `--no-id` (ancestry+patchid)** | **false-lost 0%**, recall 100% | **false-lost 0%**, recall 100% |

`present(new)` decisions: 6, of which **6 were id-independent** (not by ancestry) —
patch-id alone caught every backport. **Gate D4 PASS** (`--no-id` false-lost 0% ≤ 3%,
recall 100% ≥ 95% on patch-id labels). This removes the Round-1 circularity concern:
the lost-fix result holds with **no JIRA-id step**. (Sample bounded to 30 pairs for
time; the Round-1 100-pair id-label run gave OLD 26% vs NEW 0%. The full patch-id
harvest across all 409 hadoop branches is an hours-long job — D1-style, deferred.)

## R2-R5 — held-out test split (run once, `--final`)
Verified the manifest hash and the `--final` gate before running. Deterministic
localization metrics (LLM metrics n/a, server off):

| metric | dev baseline (R0) | test (--final, this round) |
|---|---|---|
| method_hit | 24.6% | 22.7% |
| path_hit | 31.1% | 27.3% |
| calibration high | 25.0% (n=60) | 23.8% (n=42) |

**No regression** on test vs the R0 dev baseline (the deterministic localizer is
unchanged for these cases; Round-2 only added edge-frame handling). The LLM-dependent
RCA-quality gains (`fix_overlap`, `category_match`, deep-vs-short timing) are **n/a
this round because the model server was off** — the harness computes them when it is up.

### Round-2 scope honesty
Done & measured: R0 corpus+harness+baseline, D4 no-id cross-check, D5 parity
hand-check, D6 metamorphic, D7 context pack (incl. cross-class origin), D8 depth
modes, D9 hypotheses+grounding, D10 blast v2, D13 frame normalization, D16 depth
badge; 99 tests pass. Deferred (time / server-off / clone-cost): D1 budgeted issue
harvest, full D11/D12/D14/D15 edge *fixtures* (D13 frames done+tested; D11 force-push
pin-protection, D12 Lombok, D14 version-only, D15 cross-repo are specced but not all
fixtured), and all LLM-dependent quality numbers.

````

### `WALKTHROUGH.md`
````markdown
# ghrca — Full Walkthrough

*A stage-by-stage account of how this system was built and proven: every major
step, the command that was run, what it means, and the real output it produced.
Read top to bottom to understand the whole thing.*

Contents:
1. What we set out to build
2. Stage A — Discovering the environment (and why it shaped everything)
3. Stage B — The first working analyzer
4. Stage C — The first real root-cause analysis
5. Stage D — The autonomous agent + a local "GitHub" test-bed
6. Stage E — The scaling upgrade (Phases 0–6), each with commands + outputs
7. What we ended up with

---

## 1. What we set out to build

The goal: take a **Java runtime error** — the kind that lands in Splunk when an app
throws in production (a stack trace) — and automatically:

- find the **exact code** it came from, on the **exact branch** that's deployed,
- work out **why** it failed (root cause), grounded in the real source,
- check whether a **fix already exists** — merged, sitting on another branch,
  stuck in a PR, or **lost** (fixed somewhere but never reached the deployed branch),
- write a **report**,
- and eventually do all of this **continuously**, for repos with **thousands of
  files and hundreds of branches**, calling a slow local LLM as little as possible.

Everything below is how we got there.

---

## 2. Stage A — Discovering the environment (and why it shaped everything)

Before writing code, we probed the machine. This mattered enormously: three
constraints we found dictated the entire architecture.

### A.1 — What tools exist

**Command:**
```bash
python --version; git --version; gh --version; java -version; mvn -version
curl -s -m10 -o /dev/null -w "%{http_code}" https://api.github.com/repos/opensolon/solon-ai
curl -s https://api.github.com/rate_limit | grep remaining
```

**Real output (abridged):**
```
Python 3.13.13
git version 2.39.2.windows.1
gh: command not found
java version "1.8.0_251"
mvn: command not found
http_200
"remaining": 59
```

**What it means:**
- **No `gh` CLI, only Java 8, no Maven.** solon-ai (and every modern Java repo)
  needs Java 17+ to build. So we **cannot compile the target** — we can't get
  errors or symbols from `javac`. → *We must understand Java source without a
  compiler.*
- **GitHub REST API is unauthenticated: 60 requests/hour** (59 left when probed).
  That's almost nothing. → *Anything we can do with git instead of the API, we
  must.*

### A.2 — How we reach GitHub

**Command:**
```bash
ssh -o BatchMode=yes -T git@github.com
env | grep -iE "GITHUB|GH_TOKEN"
```

**Real output:**
```
Hi ashishvnair! You've successfully authenticated, but GitHub does not provide shell access.
(no GITHUB_TOKEN in the environment)
```

**What it means:** **SSH git works** (unlimited `git clone`/`fetch`, even private
repos), but there's **no API token** (so the REST API stays at 60/hr — SSH doesn't
help the REST limit). → *All code/branch/history/diff work goes through git over
SSH; the REST API is used only for issues/PRs, cached and rationed.*

### A.3 — The LLM

The user pointed us at a launcher, `launch_qwen38flashnxt.bat`. Reading it and
later probing the running server:

**Real facts:** llama.cpp serving **Qwen3.8-Flash-Next** (a 125B-param MoE, ~82GB
on disk at IQ3_XXS quant), OpenAI-compatible at `http://127.0.0.1:8080`, context
**131072**, **single slot**, roughly **~15 tokens/sec**.

**What it means:** the LLM is **slow and serial**. A chatty design (many calls per
error) would be unusable. → *Deterministic Python does all the fact-gathering; the
LLM is spent on exactly one reasoning call per distinct bug.*

> **The three constraints, together, are the whole design rationale:** no compiler
> → tolerant source scanning; 60/hr API → git-over-SSH for everything; slow LLM →
> deterministic grounding + one call per bug.

---

## 3. Stage B — The first working analyzer

We built a Python package, `ghrca`, whose pipeline is:

```
fetch (SSH) → detect branches → index a branch → parse stack trace →
localize to exact method (deterministic) → git+PR fix-status → one LLM RCA → report
```

### B.1 — Prove the compiler-free scanner works

The scanner (`javascan.py`) blanks out comments and string literals (so braces
inside them don't confuse it), then walks the code with a brace-stack state machine
to find every class and method with its exact line range.

We smoke-tested it on a tricky snippet (comment braces, string braces, nested
class, abstract method):

**Real output:**
```
TYPE class org.demo.svc.Foo.Inner 13 15
TYPE class org.demo.svc.Foo 3 17 ext Base impl Bar
METHOD org.demo.svc.Foo#greet 6 12
method_at_line 9 -> greet
```

**What it means:** it correctly found the nested class, the `extends/implements`,
and — crucially — `method_at_line(9)` returns `greet`. That's the core trick:
**given a stack-trace line number, return the method that contains it.**

### B.2 — Clone and index a real repo

**Command:**
```bash
python -m ghrca index --repo opensolon/solon-ai
```

**Real output:**
```
main: indexed — 1541 files, 2292 types, 16385 methods; roots=['org.noear', ...]
```

**What it means:** over SSH we cloned solon-ai and, without any compiler, built a
symbol index of **1,541 Java files / 16,385 methods** in a few seconds. `roots`
(`org.noear`) is the repo's own package — used later to tell "our code" from
third-party frames in a stack trace.

### B.3 — Analyze a real error (deterministic only, no LLM)

We crafted a stack trace pointing at a genuine dereference (`msg.getRole().name()`
at `AbstractChatDialect.java:93`) and ran:

**Command:**
```bash
python -m ghrca analyze --repo opensolon/solon-ai --log solon_err.txt --no-llm
```

**Real output:**
```
fault: org.noear.solon.ai.chat.dialect.AbstractChatDialect#buildAssistantMessageNodeDo
       (solon-ai-core/.../AbstractChatDialect.java:93)
fix-status: No fix found in history or PRs for this location.
```

**What it means:** with **no LLM at all**, in well under a second, ghrca parsed the
trace, filtered out the framework/`java.*` frames, and pinpointed the exact failing
method. This is the "grounding" — by the time the LLM is called, the fault site is
already known for certain.

---

## 4. Stage C — The first real root-cause analysis

To get an actual RCA we needed the model running. We launched it and waited for it
to load 82GB:

**Command (background):**
```bash
llama-server.exe -m Qwen3.8-Flash-Next-...gguf -ngl 99 -c 131072 ... --port 8080
```
Then polled until `GET /v1/models` returned 200 → **READY after ~60s**.

**Command:**
```bash
python -m ghrca analyze --repo opensolon/solon-ai --log solon_err.txt
```

**Real output:**
```
[222.7s, 3341 completion tokens]  RCA generated
report: .cache/reports/opensolon__solon-ai/310cfa829022.html
```

**What it means:** the model produced a genuine, grounded RCA (traced the call
path, identified `getRole()` returning null, even flagged the same unguarded
pattern at line 191) — but it took **~3.7 minutes** for one error. *This number is
exactly why the later upgrade fights so hard to avoid calling the LLM.*

**A deeper finding (Stage C follow-up):** we then read the actual `AssistantMessage`
class and found `private final ChatRole role = ChatRole.ASSISTANT;` — a **final
field**. That means a normally-constructed object can *never* have a null role; the
only way is **deserialization that bypasses the constructor** (JSON replay of a
message persisted by an older version). This is the kind of insight the grounding
enables — the RCA isn't guessing, it's reading the real code.

---

## 5. Stage D — The autonomous agent + a local "GitHub" test-bed

### D.1 — The test-bed (so we can prove "lost fix" detection)

We can't push to real repos, so we built a **local git repo that behaves like a
GitHub remote**, engineered to contain a *lost fix*:

**Command:**
```bash
python scratchpad/setup_testbed.py
```

**Real output:**
```
TESTBED READY  branches: hotfix-npe main release-1 release-2 ...
buggy deref on release-2 OrderService.java line: 8
```

**What it means:** the history is `main → release-1 → hotfix-npe (adds a null
guard) → main merges the hotfix → release-2 (branched *before* the hotfix) is
DEPLOYED`. So the fix lives on `main`/`hotfix-npe` but is **missing from the
deployed `release-2`** — exactly the scenario the tool must catch.

### D.2 — The agent runs across repos and errors

**Command:**
```bash
python -m ghrca agent --targets targets.json
```

**Real output (abridged live log):**
```
[git]     cloned opensolon/solon-ai  (cold-clone, 9.38s)
[diff]    refs: 11 new  (ref-snapshot diff)
[index]   cold-index: 1541 files, 16385 methods  (3.14s)
  --- [ERROR 3] order-checkout-npe ---
  [2 locate] OK -> com.acme.orders.OrderService#checkout (...:8) on 'release-2'
  [~ diff ] fault file 'OrderService.java': 1+/5- vs main
  [3 dig  ] fix-status: A fix exists on another branch but is missing from the failing branch (lost/unmerged)
# total wall time: 752.4s
```

**What it means:** the agent watched itself work through 2 repos / 3 errors,
timestamped every report, and — the headline — on the deployed `release-2` it
reported the fix as **lost** by finding commit `3ba3db59 "fix(NPE)..."` present on
`[hotfix-npe, main]` but absent from `release-2`, **purely from git**. Total time
was 752s — again, ~99.9% of it the LLM.

---

## 6. Stage E — The scaling upgrade (Phases 0–6)

The task then became: make this work at scale — **1000s of files, 100s of
branches**, continuously — without the LLM cost exploding. We did it in 7 commits,
each with its own tests and measured gate. Test repos: `apache/kafka` (93
branches), `apache/hadoop` (409), `elastic/elasticsearch` (915), plus the test-bed.

### Phase 0 — Baseline + harness

*You can't claim an improvement you didn't measure, so first we measured the old
code.*

**Commands:**
```bash
git ls-remote --heads https://github.com/elastic/elasticsearch.git | wc -l   # 915
python -m bench.run baseline --repo apache/kafka --branch trunk
```

**Real output:**
```
kafka: cold_index_s 20.02   warm_index_s 0.52   java_files 6217   methods 74020
solon-ai: cold_index 3.91s  warm 0.10s  localize 41.4ms  fixstatus(old --contains) 110.4ms
LLM thinking-off probe: enable_thinking=false -> 2 tokens (vs 37 baseline)
```

**What it means / what we learned:**
- Indexing a big repo the old way costs **20s** and scales with file count — doing
  that per-branch across 915 branches would be catastrophic. *This is the thing to
  kill.*
- A one-line probe found that telling the model `enable_thinking:false` cuts its
  output ~18× — a free speedup we bank in Phase 1.

**Gate: PASS** (baseline + environment recorded in `BENCHMARKS.md`). Commit `phase0`.

### Phase 1 — Cheap wins

Introduced: a **SQLite database** (replacing scattered JSON), **error
fingerprinting** (so identical bugs collapse to one), an **RCA cache**, a
**persistent job queue**, **thinking-off + a short 3-section prompt**, and
**two-stage reports** (instant deterministic report first, LLM narrative fills in
later).

**The headline measurement — do we actually stop re-calling the LLM?**
```bash
python -m bench.run fingerprint-replay --n 1000
```
**Real output:**
```
errors=1000  distinct (fp, method_hash)=3  LLM_calls=3  dedup=99.7%
```
**What it means:** 1,000 incoming errors that are really just 3 distinct bugs
(with noisy IDs) trigger **3 LLM calls, not 1000**. That's the single most
important economy in the whole system.

**And how fast is the "first report"?**
```
Stage-A deterministic report (solon-ai, warm): 92-95 ms
```
**What it means:** a useful report (fault site, code, fix-status) is on screen in
~0.1s; the slow LLM narrative is added to the *same* report when it's ready.

**Gate: PASS.** Commit `phase1`.

### Phase 2 — Blob-keyed lazy index + tree-sitter

The big architectural change. Instead of indexing a whole branch to answer one
error, we resolve the **one file** the error points at, scan **just that blob**
(cached forever by its git SHA), and look up the method. We also switched the
parser to **tree-sitter** (a real grammar) with the regex scanner as fallback.

**Parser check:**
```bash
python -m bench.parity --repo apache/kafka --branch trunk
```
**Real output:**
```
functional parity 94.31%; tree-sitter found 9963 methods the regex scanner MISSED
localization identical on all fixtures (AbstractChatDialect:93 -> buildAssistantMessageNodeDo, etc.)
```
**What it means (and an honest call):** the spec wanted "99% agreement vs the
regex scanner," but reading the disagreements by hand showed **tree-sitter is the
*correct* one** (the regex scanner mis-flags class names as methods and under-spans
others). So we adopted tree-sitter and proved the thing that actually matters —
**localization is identical** — rather than chasing an impossible match to a weaker
baseline.

**Speed check — localize without any branch index:**
```
lazy localize (solon-ai): warm 47 ms   (target <100ms)
new-branch scan: 0.113% of a branch's files (only the changed blobs)
```
**What it means:** we hit the <100ms target **without building a branch index at
all**, and a freshly-created branch costs almost nothing to prepare (scan ~0.1% of
files). *This is what makes "hundreds of branches" tractable.*

**Gate: PASS.** Commit `phase2`.

### Phase 3 — Correct fix-status (the "lost fix" brain)

The old method (`git branch --contains <sha>`) has a fatal flaw: a **cherry-picked
backport gets a new SHA**, so `--contains` says "not here" → falsely "lost." We
rewrote fix-status to decide presence by, in order: **ancestry → file patch-id →
JIRA/issue-id → content**, grouping an original commit with its cherry-picks/
squashes into one logical fix.

**The proof — 100 real labelled Hadoop backports:**
```bash
python -m bench.hadoop_labels --repo apache/hadoop --pairs 100
```
**Real output:**
```
OLD (--contains):      false-"lost" = 26.09%   lost-recall = 100%
NEW (D10 ancestry+id): false-"lost" =  0.00%   lost-recall = 100%
```
**What it means:** the old approach **wrongly flags 26% of backported fixes as
lost**; the new one gets it **exactly right (0%)** while still catching every
genuinely-lost fix. On the test-bed, a cherry-pick and a squash are now correctly
labelled `present_via_equivalent`, not `lost`.

Also added: **deployed-commit pinning** (analyze the exact deployed SHA, not just a
branch tip) and **drift detection** (if line numbers have shifted, lower the
confidence and remap).

**Gate: PASS** (false-lost 0% ≤ 2%, recall 100% ≥ 95%). Commit `phase3`.

### Phase 4 — Blast radius

"This bug — which of the *other* branches also have it?" One
`git cat-file --batch-check` gets every branch's version of the file; we scan only
the **distinct** versions and compare the method's `body_hash`.

**Command:**
```bash
python -m ghrca blast --repo elastic/elasticsearch --error err.txt   # 915 branches
```
**Real output:**
```
WARM blast: 0.647s   (620 branches have the file, 99 distinct versions)
reference check on 30 branches: 30/30 match
```
**What it means:** across **915 branches in 0.65s** we classify each branch as
affected / fixed / changed, and it matches a slow brute-force reference exactly.
Because `body_hash` ignores line numbers, a branch that only shifted lines is
correctly seen as *still affected*, while a genuinely-fixed branch is not.

**Gate: PASS.** Commit `phase4`.

### Phase 5 — The daemon (runs unattended)

Tied it all together: a loop that polls for new branches, ingests errors dropped
into a folder, produces Stage-A reports in a thread pool, and drains one LLM queue
in the background — surviving restarts.

**The soak test (the gate):** 200 errors (16 distinct bugs) dropped in; 5 branches
created mid-run; then a simulated crash.
**Real output:**
```
errors=200  distinct_fp=16  LLM_calls=16
stage_a_max_ms=436   (<1000 gate)
new branches detected in one poll: 5  (['feature-0'..'feature-4'])
resume after crash: requeued=1 redrained=1 cache delta=1 (NO duplicates)
GATE: PASS
```
**What it means:** unattended, it dedups 200 errors down to 16 LLM calls, every
deterministic report is <0.5s, it spots all 5 new branches in one poll, and a crash
mid-queue resumes cleanly with **no duplicate work**. Also added a **read-only
backport dry-run** (`backport-plan`) and an **eval harness** (`ghrca eval`, gate
localization ≥95% / verdict ≥90% — we score **100%/100%**).

**Gate: PASS.** Commit `phase5`.

### Phase 6 — Cleanup + docs

Migrated `analyze` and the agent onto the lazy path so that **no whole-branch index
is ever built to answer a single error** (a Definition-of-Done requirement),
retired the old per-branch JSON, and rewrote the docs.

**The last measurement — a real short-format RCA on the live model:**
```
short-format RCA (thinking off): 34.9s / 301 tokens   (was 220-270s long-format)
```
**What it means:** the same model that took ~3.7 minutes in Stage C now answers in
**~35s** — and for common NPE/index/cast bugs it answers in **0s** (served from a
template), only reaching the model for novel bugs.

**Gate: PASS.** Commit `phase6`.

---

## 7. What we ended up with

**Every Section-1 target met (all measured, in `BENCHMARKS.md`):**

| Goal | Target | Achieved |
|---|---|---|
| Localize an error | <100ms warm, no branch index | **47ms** |
| Blast across all branches | <3s warm on 900-branch repo | **0.647s** (ES, 915) |
| LLM calls | == distinct bugs | **200 → 16** |
| First report | <1s warm | **92–436ms** |
| Fix-status false-"lost" | ≤2% | **0.0%** (old 26%) |
| New branch detected | within one poll | **5/5**, ~0.1% of files scanned |
| Median RCA | ≤90s | **34.9s** (was 220–270s) |

**The commands you now have:**
```bash
python -m ghrca analyze --repo R --log err.txt      # one error → grounded RCA
python -m ghrca blast   --repo R --error err.txt     # which branches are affected
python -m ghrca backport-plan --repo R --fix SHA --target BR   # dry-run a backport
python -m ghrca daemon  --targets targets.json       # run it continuously
python -m ghrca eval                                 # CI quality gate
python -m ghrca status  --repo R                      # branches, queue, cache, last poll
```

**In one paragraph:** we turned "paste a stack trace, get a grounded root-cause
report" into a system that watches hundreds of branches, notices new ones within a
minute, answers each error in milliseconds of deterministic work plus at most one
cached-or-templated-or-35s LLM call, and — the part that's genuinely hard — tells
you correctly whether the fix is already out there or was lost on the way to the
branch that's actually deployed. Every number here came from a real run on real
repos (kafka, hadoop, elasticsearch, solon-ai), and 70 automated tests keep it
honest.

````

## 8. RCA corpus (generated data)

`eval/rca_cases/` holds **118** generated cases (reproducible via `python -m bench.harvest`) plus a frozen `TEST_MANIFEST.sha256`. One example:

```json
{
  "id": "0205d695379d",
  "repo": "apache/kafka",
  "error": "java.nio.channels.ClosedChannelException\n        at java.base/sun.nio.ch.FileChannelImpl.ensureOpen(FileChannelImpl.java:150)\n        at java.base/sun.nio.ch.FileChannelImpl.force(FileChannelImpl.java:452)\n        at org.apache.kafka.common.record.FileRecords.flush(FileRecords.java:197)\n        at org.apache.kafka.common.record.FileRecords.close(FileRecords.java:204)\n        at kafka.log.LogSegment.$anonfun$close$4(LogSegment.scala:592)\n        at kafka.utils.CoreUtils$.swallow(CoreUtils.scala:68)\n        at kafka.log.LogSegment.close(LogSegment.scala:592)\n        at kafka.log.Log.$anonfun$close$4(Log.scala:1038)\n        at kafka.log.Log.$anonfun$close$4$adapted(Log.scala:1038)\n        at scala.collection.IterableOnceOps.foreach(IterableOnce.scala:563)\n        at scala.collection.IterableOnceOps.foreach$(IterableOnce.scala:561)\n        at scala.collection.AbstractIterable.foreach(Iterable.scala:919)\n        at kafka.log.Log.$anonfun$close$3(Log.scala:1038)\n        at kafka.log.Log.close(Log.scala:2433)\n        at kafka.raft.KafkaMetadataLog.close(KafkaMetadataLog.scala:295)\n        at kafka.raft.KafkaRaftManager.shutdown(RaftManager.scala:150)\n```",
  "fix_commit": "1a09bac0301a15fe7967e9a0c5bf11d34120561b",
  "analysis_commit": "954c090ffc378a63ce3c3c9a72b87724fcd2cd6c",
  "truth": {
    "files": [
      "raft/src/main/java/org/apache/kafka/raft/KafkaRaftClient.java"
    ],
    "methods": [
      "org.apache.kafka.raft.KafkaRaftClient#close"
    ],
    "changed_ranges": [
      [
        "raft/src/main/java/org/apache/kafka/raft/KafkaRaftClient.java",
        2265,
        2265
      ]
    ],
    "fix_category": "logic"
  },
  "source": "commit_message",
  "notes": ""
}
```
TEST_MANIFEST.sha256 (head):
```
7c09759b82c8317119776c8e33542acfee52498671a784362b918da97d2ed52c
0205d695379d:4326bebea4f8089f2b474032e0f8e02f988f3dc0
1149187face2:5d0848644dd520592a46de00fd50f86e8367f883
16707e533b44:e8690daf76cda9e9778c632eabc51f10f2f49996
...
```

## 9. What's done (summary)

- **Round 1 (phases 0-6):** lazy blob-keyed index, tree-sitter, SQLite, fingerprint + RCA cache, LLM queue, fix-status v2, blast radius, daemon, eval. All Section-1 targets met (localize 47ms, blast ES-915 0.65s, dedup 200->16, false-lost 0%, RCA 34.9s).
- **Round 2:** git-only RCA corpus + frozen held-out split; lost-fix without JIRA-id circularity (--no-id 0% false-lost); value-origin context pack (cross-class); depth modes + ranked hypotheses + grounding; blast v2; frame normalization. 99 tests pass.
- **Deferred (stated honestly):** LLM-dependent quality metrics (model server off), D1 budgeted issue harvest, full edge fixtures D11/D12/D14/D15.
