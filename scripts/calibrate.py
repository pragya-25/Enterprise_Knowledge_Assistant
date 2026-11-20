"""
Pick the "I couldn't find this" threshold for the reranker.

    python -m scripts.calibrate

Compares the top reranker score for questions the documents CAN answer
(from eval/testset.json) against questions they CANNOT, then suggests a cut-off.
"""
import json
from pathlib import Path

import numpy as np

from app.retrieval.pipeline import retrieve_mode

TESTSET = Path(__file__).resolve().parents[1] / "eval" / "testset.json"

OUT_OF_SCOPE = [
    "What is the capital of France?",
    "How do I bake a chocolate cake?",
    "Who won the cricket world cup?",
    "What is the price of Bitcoin today?",
    "Explain quantum computing in simple words",
    "Where can I find the best pizza in Delhi?",
    "How do I train a puppy to sit?",
    "What will the weather be tomorrow?",
    "Write a poem about the ocean",
    "How do I fix my car engine?",
    "What is the meaning of life?",
    "Who is the richest person in the world?",
]


def top_score(q):
    res = retrieve_mode(q, "admin", "rerank", 5)
    return res[0]["score"] if res else -99.0


def main():
    tests = json.loads(TESTSET.read_text(encoding="utf-8"))
    inside = np.array([top_score(t["q"]) for t in tests])
    outside = np.array([top_score(q) for q in OUT_OF_SCOPE])

    print(f"In-scope  (n={len(inside)}):  min {inside.min():.2f}  "
          f"5th pct {np.percentile(inside, 5):.2f}  median {np.median(inside):.2f}")
    print(f"Out-scope (n={len(outside)}): max {outside.max():.2f}  "
          f"median {np.median(outside):.2f}")
    print("\nOut-of-scope scores, highest first:")
    for q, s in sorted(zip(OUT_OF_SCOPE, outside), key=lambda x: -x[1])[:5]:
        print(f"   {s:6.2f}  {q}")

    low_in, high_out = np.percentile(inside, 5), outside.max()
    if low_in > high_out:
        thr = (low_in + high_out) / 2
        print(f"\nClean gap. Suggested RERANK_MIN_SCORE={thr:.2f}")
    else:
        thr = high_out + 0.5
        print(f"\nThe two groups overlap a little. Suggested RERANK_MIN_SCORE={thr:.2f} "
              "(blocks all off-topic questions, may refuse a few borderline real ones)")
    print("Add this line to your .env file.")


if __name__ == "__main__":
    main()
