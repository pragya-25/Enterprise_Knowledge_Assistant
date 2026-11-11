"""
Ask a question end to end: role-filtered search -> LLM -> cited answer.

    python -m scripts.ask "How much parental leave do I get?" --role employee
    python -m scripts.ask "What is the anti-harassment policy?" --role hr
    python -m scripts.ask                      # interactive mode
"""
import argparse
from app.generation.answer import answer_question


def show(result, debug):
    print("\n" + result["answer"] + "\n")
    if result["sources"]:
        print("Sources:")
        for s in result["sources"]:
            extra = f"  (score {s['score']}, {s['department']})" if debug else ""
            print(f"  [{s['n']}] {s['title']} > {s['section']}  - {s['file']}{extra}")
    if debug:
        print(f"\n[debug] top retrieval score = {result['top_score']:.3f}")
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question", nargs="?")
    ap.add_argument("--role", default="employee")
    ap.add_argument("--debug", action="store_true", help="show scores")
    args = ap.parse_args()

    if args.question:
        show(answer_question(args.question, args.role), args.debug)
        return

    print(f"Interactive mode as role '{args.role}'. Type 'exit' to quit.")
    while True:
        q = input("\nYou: ").strip()
        if q.lower() in {"exit", "quit", ""}:
            break
        show(answer_question(q, args.role), args.debug)


if __name__ == "__main__":
    main()
