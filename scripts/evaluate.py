"""
Measure retrieval quality on eval/testset.json.

    python -m scripts.evaluate                      # all three modes
    python -m scripts.evaluate --modes vector       # baseline only
    python -m scripts.evaluate --modes rerank --misses

Hit@5 : % of questions where a correct source file is in the top 5 chunks
MRR   : rewards putting the correct file higher in the list (1.0 = always first)
"""
import argparse
import json
import time
from pathlib import Path

from app.retrieval.pipeline import retrieve_mode

TESTSET = Path(__file__).resolve().parents[1] / "eval" / "testset.json"
K = 5


def run(mode, tests, role, show_misses):
    retrieve_mode("warm up", role, mode, K)          # load models before timing
    hits, rr_sum, latencies, misses = 0, 0.0, [], []
    for t in tests:
        start = time.perf_counter()
        results = retrieve_mode(t["q"], role, mode, K)
        latencies.append(time.perf_counter() - start)

        rank = next((i for i, r in enumerate(results, 1) if r["source"] in t["expected"]), None)
        if rank:
            hits += 1
            rr_sum += 1.0 / rank
        else:
            misses.append((t, results))

    n = len(tests)
    stats = {"mode": mode, "hit": 100 * hits / n, "mrr": rr_sum / n,
             "ms": 1000 * sum(latencies) / n}
    if show_misses:
        print(f"\n--- Misses for {mode} ({len(misses)}) ---")
        for t, results in misses:
            print(f"Q: {t['q']}\n   expected: {t['expected'][0]}")
            for r in results[:3]:
                print(f"   got: {r['source']}")
    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modes", nargs="+", default=["vector", "hybrid", "rerank"])
    ap.add_argument("--role", default="admin", help="admin can read every department")
    ap.add_argument("--misses", action="store_true")
    args = ap.parse_args()

    tests = json.loads(TESTSET.read_text(encoding="utf-8"))
    print(f"{len(tests)} questions, role={args.role}, top-{K} chunks\n")

    rows = [run(m, tests, args.role, args.misses) for m in args.modes]

    print("\n| Method | Hit@5 | MRR@5 | Avg latency |")
    print("|---|---|---|---|")
    for r in rows:
        print(f"| {r['mode']} | {r['hit']:.1f}% | {r['mrr']:.3f} | {r['ms']:.0f} ms |")


if __name__ == "__main__":
    main()
