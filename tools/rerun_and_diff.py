#!/usr/bin/env python3
"""Re-run every study, diff every published number, and say which prose to edit.

Why this exists
---------------
Three methodology fixes in `research/_core/` change numbers that are committed
in `expected_output.json` and quoted in the study READMEs. The fixes cannot be
verified on a machine without market-data access, so this script does the whole
job in one pass on a machine that has it:

    python tools/rerun_and_diff.py              # run + report, change nothing
    python tools/rerun_and_diff.py --accept     # ...and refresh expected_output.json

It reports EVERY numeric leaf that moved, not just the handful each study's own
gate checks, because the READMEs quote far more numbers than the gate does. For
each changed value it then greps the markdown for the old figure and prints the
file:line to edit, so nothing published silently disagrees with the JSON.

Exit code is 0 if the run completed, 1 if any study failed to execute.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STUDIES = sorted(p for p in (REPO / "research").glob("[0-9][0-9]_*") if p.is_dir())
DOCS = sorted(REPO.glob("**/*.md"))

TOL_REPORT = 1e-6      # anything moving by more than this is listed
TOL_GATE = 1e-3        # the repository's own drift threshold


def flatten(obj, prefix=""):
    """Every numeric leaf, as {dotted.path: value}. Lists index by position."""
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(flatten(v, f"{prefix}.{k}" if prefix else str(k)))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.update(flatten(v, f"{prefix}[{i}]"))
    elif isinstance(obj, bool):
        pass
    elif isinstance(obj, (int, float)):
        out[prefix] = float(obj)
    return out


def run_study(d: Path, timeout: int):
    t0 = time.time()
    try:
        p = subprocess.run([sys.executable, "run.py"], cwd=d, capture_output=True,
                           text=True, timeout=timeout)
        return p.returncode, p.stdout + p.stderr, time.time() - t0
    except subprocess.TimeoutExpired:
        return -1, f"TIMEOUT after {timeout}s", time.time() - t0


def renderings(v: float):
    """How a number of this size plausibly appears in prose.

    Deliberately narrow. A loose match on something like "0.22" hits every
    unrelated table in the repository, which buries the real edits — so each
    rendering is anchored on non-digit boundaries at match time, and 2-decimal
    forms are only offered for values that actually round cleanly there.
    """
    out = set()
    for dp in (3, 4):
        out.add(f"{v:.{dp}f}")
        out.add(f"{v:+.{dp}f}")
    if abs(round(v, 2) - v) < 5e-4:          # 0.368 -> don't also chase "0.37"
        out.add(f"{v:.2f}")
        out.add(f"{v:+.2f}")
    for dp in (1, 2):
        out.add(f"{v * 100:.{dp}f}%")
        out.add(f"{v * 100:+.{dp}f}%")
    return {t for t in out if not re.fullmatch(r"[+-]?0\.0+%?", t)}


def docs_for(study: Path):
    """Where a study's numbers are allowed to appear."""
    docs = list(study.glob("*.md"))
    for extra in ("research/README.md", "README.md", "PORTFOLIO_MANAGER_PROFILE.md",
                  "results/README.md", "methodology/STRATEGY_WHITEPAPER.md"):
        p = REPO / extra
        if p.exists():
            docs.append(p)
    return docs


def scan_docs(value: float, study: Path):
    """Find prose quoting `value`, anchored so 0.22 does not match 0.221."""
    hits = []
    pats = renderings(value)
    rx = [re.compile(r"(?<![0-9.])" + re.escape(p) + r"(?![0-9])") for p in sorted(pats)]
    for doc in docs_for(study):
        try:
            lines = doc.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines, 1):
            # normalise the unicode minus the READMEs use in tables
            probe = line.replace("\u2212", "-")
            for pat, r in zip(sorted(pats), rx):
                if r.search(probe):
                    hits.append((doc.relative_to(REPO).as_posix(), i, pat, line.strip()[:100]))
                    break
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--accept", action="store_true",
                    help="overwrite expected_output.json with this run's results")
    ap.add_argument("--only", nargs="*", default=None,
                    help="study folder name fragments to limit the run to")
    ap.add_argument("--timeout", type=int, default=900, help="per-study seconds")
    ap.add_argument("--report", default="rerun_report.md",
                    help="working file, git-ignored; not part of the published repo")
    args = ap.parse_args()

    studies = [d for d in STUDIES
               if not args.only or any(f in d.name for f in args.only)]

    print(f"repo    {REPO}")
    print(f"studies {len(studies)}\n")

    print("=== unit tests ===")
    t = subprocess.run([sys.executable, "research/_core/test_core.py"],
                       cwd=REPO, capture_output=True, text=True)
    print(t.stdout.strip() or t.stderr.strip())
    if t.returncode != 0:
        print("\nCore unit tests FAILED — stopping before touching any study.")
        return 1

    failures, all_changes, lines = [], {}, []

    for d in studies:
        rc, log, secs = run_study(d, args.timeout)
        res_path = d / "sample_output" / "results.json"
        exp_path = d / "expected_output.json"

        if not res_path.exists():
            failures.append(d.name)
            tail = "\n".join(log.strip().splitlines()[-6:])
            print(f"[{d.name}]  DID NOT PRODUCE RESULTS  ({secs:.0f}s)\n{tail}\n")
            continue

        new = flatten(json.loads(res_path.read_text(encoding="utf-8")))
        old = flatten(json.loads(exp_path.read_text(encoding="utf-8"))) if exp_path.exists() else {}

        changed = {k: (old[k], new[k]) for k in new
                   if k in old and abs(new[k] - old[k]) > TOL_REPORT}
        added = sorted(set(new) - set(old))
        dropped = sorted(set(old) - set(new))
        gate = {k: v for k, v in changed.items() if abs(v[1] - v[0]) > TOL_GATE}

        status = "unchanged" if not changed else f"{len(changed)} moved ({len(gate)} past the 1e-3 gate)"
        print(f"[{d.name}]  {status}  ({secs:.0f}s, exit {rc})")
        lines.append(f"\n## {d.name}\n\n- ran in {secs:.0f}s, exit {rc}\n- {status}")
        if added or dropped:
            lines.append(f"- keys added: {added or 'none'}\n- keys dropped: {dropped or 'none'}")

        if changed:
            all_changes[d.name] = changed
            lines.append("\n| metric | committed | this run | delta |\n|---|---|---|---|")
            for k, (o, n) in sorted(changed.items(), key=lambda kv: -abs(kv[1][1] - kv[1][0])):
                mark = " **" if abs(n - o) > TOL_GATE else " "
                lines.append(f"|{mark}`{k}`{mark.strip()} | {o:.6g} | {n:.6g} | {n - o:+.6g} |")

        if args.accept:
            shutil.copyfile(res_path, exp_path)

    # ---- which prose now disagrees with the JSON ----
    print("\n=== prose that quotes a number which moved ===")
    lines.append("\n\n# Prose to update\n")
    seen, found = set(), 0
    by_name = {d.name: d for d in studies}
    for study, changed in all_changes.items():
        for k, (o, n) in changed.items():
            if abs(n - o) <= TOL_GATE:
                continue
            for doc, ln, pat, text in scan_docs(o, by_name[study]):
                key = (doc, ln)
                if key in seen:
                    continue
                seen.add(key)
                found += 1
                print(f"  {doc}:{ln}  quotes {pat}  ({study} {k}: {o:.6g} -> {n:.6g})")
                print(f"      {text}")
                lines.append(f"- `{doc}:{ln}` quotes **{pat}** — {study} `{k}` moved "
                             f"{o:.6g} → {n:.6g}\n  > {text}")
    if not found:
        print("  (nothing — no published figure moved past the gate)")
        lines.append("- nothing: no published figure moved past the 1e-3 gate.")

    header = [f"# Re-run report\n",
              f"- studies run: {len(studies)}",
              f"- studies that changed: {len(all_changes)}",
              f"- studies that failed to run: {failures or 'none'}",
              f"- expected_output.json refreshed: {'yes' if args.accept else 'NO (dry run)'}"]
    (REPO / args.report).write_text("\n".join(header + lines) + "\n", encoding="utf-8")
    print(f"\nreport written to {args.report}")

    if failures:
        print(f"\n{len(failures)} study/studies could not run: {failures}")
        print("Usually a data-source problem, not a code problem — check the log above.")
        return 1
    if not args.accept and all_changes:
        print("\nDry run. Review the report, then re-run with --accept to refresh the "
              "reference outputs, and edit the prose listed above before committing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
