from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dove.benchmark_loader import load_models
from dove.question_generator import generate_questions, save_questions


def main():
    parser = argparse.ArgumentParser(description="Generate human-review candidates")
    parser.add_argument("--mode", choices=["domain", "wiki", "corpus"], required=True)
    parser.add_argument("--domain", required=True)
    parser.add_argument("--subdomains", default="")
    parser.add_argument("--n", type=int, required=True)
    parser.add_argument("--models", default="config/models.yaml")
    parser.add_argument("--model")
    parser.add_argument("--wiki", help="Compiled wiki workspace for wiki/corpus mode")
    parser.add_argument("--corpus", help="Deprecated alias: use --wiki after build_wiki.py")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    models = load_models(args.models)
    model = next((m for m in models if m.name == args.model), models[0])
    wiki = args.wiki or args.corpus
    if args.mode in {"wiki", "corpus"} and not wiki:
        parser.error("--wiki is required for private-document generation")
    items = generate_questions(model, args.domain, args.n, args.subdomains, wiki)
    save_questions(items, args.output)
    print(f"Saved {len(items)} non-gold candidates to {args.output}; human review required")


if __name__ == "__main__":
    main()


