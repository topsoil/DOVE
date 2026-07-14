from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import json
from pathlib import Path
from dove.benchmark_loader import load_models
from dove.llm_wiki import build_wiki


def main():
    parser = argparse.ArgumentParser(description="Compile a Karpathy-style LLM Wiki from private sources")
    parser.add_argument("--corpus", required=True, help="Extracted DOVE corpus JSON")
    parser.add_argument("--models", required=True)
    parser.add_argument("--model", help="Configured model name; defaults to first")
    parser.add_argument("--output", required=True, help="Wiki workspace directory")
    args = parser.parse_args()
    models = load_models(args.models)
    model = next((m for m in models if m.name == args.model), models[0])
    corpus = json.loads(Path(args.corpus).read_text(encoding="utf-8"))
    manifest = build_wiki(corpus, args.output, model)
    print(f"Compiled {len(manifest['pages'])} wiki pages under {args.output}")


if __name__ == "__main__":
    main()


