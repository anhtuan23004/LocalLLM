"""Download models from Hugging Face and register them as per-model sidecars."""

import argparse
import os
import sys
from datetime import date
from huggingface_hub import snapshot_download
from ruamel.yaml import YAML

yaml = YAML()
yaml.default_flow_style = False

FORMAT_EXTENSIONS = [(".safetensors", "safetensors"), (".bin", "pytorch"), (".gguf", "gguf")]
SUPPORTED_TARGETS = ["vllm", "sglang", "llama.cpp", "ollama", "mlx"]
TARGET_MAP = {
    "safetensors": ["vllm", "sglang"],
    "pytorch": ["vllm", "sglang"],
    "gguf": ["llama.cpp", "ollama"],
}


def detect_format(model_dir):
    for ext, fmt in FORMAT_EXTENSIONS:
        if any(f.endswith(ext) for f in os.listdir(model_dir)):
            return fmt
    return "unknown"


def dir_size_gb(path):
    total = sum(
        os.path.getsize(os.path.join(dp, f))
        for dp, _, files in os.walk(path) for f in files
    )
    return round(total / 1e9, 1)


def write_sidecar(model_id, model_dir, target_overrides=None):
    """Write models/<name>/model.yaml sidecar after download."""
    fmt = detect_format(model_dir)
    size = dir_size_gb(model_dir)
    targets = target_overrides or TARGET_MAP.get(fmt, ["vllm"])
    model_name = os.path.basename(model_dir)
    # Store path relative to repo root (models/<name>)
    rel_path = os.path.relpath(model_dir, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    entry = {
        "id": model_name,
        "repo": model_id,
        "format": fmt,
        "size_gb": size,
        "path": rel_path,
        "serving_target": targets[0],
        "serving_targets": targets,
        "quantizations": [],
        "status": "downloaded",
        "downloaded": str(date.today()),
    }

    sidecar_path = os.path.join(model_dir, "model.yaml")
    with open(sidecar_path, "w") as f:
        yaml.dump(entry, f)
    print(f"[+] Wrote sidecar: {sidecar_path}")
    return entry


def download_model(model_id, local_dir, token=None):
    """Download a model from Hugging Face Hub."""
    if not os.path.exists(local_dir):
        os.makedirs(local_dir, exist_ok=True)

    print(f"[*] Starting download for: {model_id}")
    try:
        path = snapshot_download(
            repo_id=model_id,
            local_dir=local_dir,
            local_dir_use_symlinks=False,
            revision="main",
            token=token,
            ignore_patterns=["*.msgpack", "*.h5", "*.ot"],
        )
        print(f"[+] Downloaded to: {path}")
        return path
    except Exception as e:
        print(f"[-] Error downloading model: {e}")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download models from Hugging Face")
    parser.add_argument("model_id", help="HF model ID (e.g., Qwen/Qwen3-VL-4B-Instruct)")
    parser.add_argument("--dir", default="models", help="Base directory for all models")
    parser.add_argument("--token", default=None, help="HF Access Token for gated models")
    parser.add_argument("--target", action="append", choices=SUPPORTED_TARGETS,
                        help="Override serving target. Repeat for multiple targets.")
    parser.add_argument("--force", action="store_true", help="Re-download even if exists")
    args = parser.parse_args()

    model_folder = args.model_id.split("/")[-1]
    final_dir = os.path.join(args.dir, model_folder)

    sidecar = os.path.join(final_dir, "model.yaml")
    if os.path.isfile(sidecar) and not args.force:
        print(f"[*] {model_folder} already downloaded. Use --force to re-download.")
        sys.exit(0)

    result = download_model(args.model_id, final_dir, args.token)
    if result:
        entry = write_sidecar(args.model_id, final_dir, args.target)
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from assemble_registry import assemble
        assemble(args.dir)
        runtime = entry["serving_targets"][0]
        print()
        print("Suggested preset:")
        print(
            f"./llm-local preset add --from-model {entry['id']} "
            f"--runtime {runtime} --alias local-{runtime.replace('.', '-')} "
            f"--id {runtime.replace('.', '-')}-{entry['id'].lower()}"
        )
