from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dove.corpus_ingest import ingest_corpus, save_corpus


def main():
    parser = argparse.ArgumentParser(description="Extract and chunk a private document corpus")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    corpus = ingest_corpus(args.input)
    save_corpus(corpus, args.output)
    print(f"Extracted {len(corpus['documents'])} documents / {len(corpus['chunks'])} chunks")


if __name__ == "__main__":
    main()


