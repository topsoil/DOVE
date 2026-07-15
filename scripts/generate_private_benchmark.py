from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dove.benchmark_loader import load_models
from dove.private_document_benchmark import (
    generate_direct_document_benchmark,
    generate_private_document_benchmark,
)
from dove.schemas import ModelConfig


def _select_model(args: argparse.Namespace) -> ModelConfig:
    if args.ollama_model:
        return ModelConfig(
            name=f"ollama:{args.ollama_model}", provider="ollama",
            model=args.ollama_model, base_url=args.ollama_url,
            temperature=args.temperature, timeout=args.timeout,
            context_window=args.ollama_context,
            max_output_tokens=args.max_output_tokens,
        )
    models = load_models(args.models)
    model = next((m for m in models if m.name == args.model), None) if args.model else models[0]
    if model is None:
        raise ValueError(f"Model named {args.model!r} was not found in {args.models}")
    updates = {}
    if args.max_output_tokens:
        updates["max_output_tokens"] = args.max_output_tokens
    if args.structured_outputs:
        updates["structured_outputs"] = True
    return model.model_copy(update=updates) if updates else model


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate human-review DOVE candidates from a document directory"
    )
    parser.add_argument("--strategy", choices=["direct", "wiki"], default="wiki",
                        help="direct is fast; wiki builds a persistent resumable knowledge layer")
    parser.add_argument("--documents", required=True, help="Directory containing PDF/Markdown files")
    parser.add_argument("--domain", required=True, help="Domain label stored on every question")
    parser.add_argument("--subdomains", default="", help="Comma-separated topics to emphasize")
    parser.add_argument("--n", type=int, required=True, help="Exact number of questions to save")
    parser.add_argument("--output", required=True, help="DOVE-compatible JSON output path")
    parser.add_argument("--workspace", help="Private work directory; defaults beside output")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--ollama-model", help="Local Ollama model, for example qwen3:4b")
    source.add_argument("--models", help="DOVE model YAML for Ollama or OpenAI-compatible APIs")
    parser.add_argument("--model", help="Name from --models; defaults to the first entry")
    parser.add_argument("--ollama-url", default="http://localhost:11434")
    parser.add_argument("--ollama-context", type=int, help="Ollama num_ctx; 8192 is a useful 4B default")
    parser.add_argument("--max-output-tokens", type=int, help="Cap model output tokens")
    parser.add_argument("--structured-outputs", action="store_true",
                        help="Request strict JSON Schema from a supporting remote model")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--max-rounds", type=int, default=8)
    parser.add_argument("--parallel", type=int,
                        help="Concurrent question calls (default: direct=4, wiki=1)")
    parser.add_argument("--wiki-chunk-chars", type=int, default=24000,
                        help="Source characters per wiki compiler call")
    parser.add_argument("--question-context-chars", type=int, default=40000,
                        help="Compiled wiki characters per question call")
    parser.add_argument("--source-chunk-chars", type=int, default=40000,
                        help="Source characters per direct-mode call")
    args = parser.parse_args()

    output = Path(args.output)
    suffix = "wiki" if args.strategy == "wiki" else "direct_work"
    workspace = Path(args.workspace) if args.workspace else output.with_name(f"{output.stem}_{suffix}")
    model = _select_model(args)
    parallel = args.parallel if args.parallel is not None else (4 if args.strategy == "direct" else 1)
    common = dict(
        documents_dir=args.documents, output=output, workspace=workspace, model=model,
        domain=args.domain, count=args.n, subdomains=args.subdomains,
        batch_size=args.batch_size, max_rounds=args.max_rounds, parallel=parallel,
    )
    if args.strategy == "wiki":
        items = generate_private_document_benchmark(
            **common, wiki_chunk_chars=args.wiki_chunk_chars,
            question_context_chars=args.question_context_chars,
        )
    else:
        items = generate_direct_document_benchmark(
            **common, source_chunk_chars=args.source_chunk_chars,
        )
    print(f"Saved {len(items)} DOVE-compatible candidates to {output}")
    print(f"Strategy: {args.strategy}")
    print(f"Workspace: {workspace}")
    print(f"Experience log: {workspace / 'experience_log.json'}")
    print("Review status: corpus_generated (human curation required before gold use)")


if __name__ == "__main__":
    main()
