"""Validate model registry against filesystem."""

import os
import sys
from ruamel.yaml import YAML

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from llm_local.catalog import format_targets

yaml = YAML()

FORMAT_GLOBS = {"safetensors": ".safetensors", "gguf": ".gguf", "pytorch": ".bin"}
VALID_TARGETS = {"vllm", "sglang", "llama.cpp", "ollama", "mlx"}
FORMAT_TARGETS = format_targets()


def model_targets(model):
    targets = model.get("serving_targets")
    if targets:
        return targets
    target = model.get("serving_target")
    return [target] if target else []


def validate(registry_path, metadata_only=False):
    if not os.path.isfile(registry_path):
        print(f"ERROR: Registry not found: {registry_path}")
        return 1

    # Repo root is parent of models/
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(registry_path)))

    with open(registry_path) as f:
        data = yaml.load(f)

    models = (data or {}).get("models", [])
    print(f"[*] Validating {len(models)} model(s) from {registry_path}\n")
    errors = 0

    for m in models:
        mid, path, fmt = m.get("id", "?"), m.get("path", ""), m.get("format", "")
        abs_path = os.path.join(repo_root, path)
        print(f"  {mid:20s} {path} ... ", end="")

        if not metadata_only:
            if not os.path.isdir(abs_path):
                print("MISSING")
                errors += 1
                continue

            ext = FORMAT_GLOBS.get(fmt)
            if ext and not any(f.endswith(ext) for f in os.listdir(abs_path)):
                print(f"WARN: no {ext} files")
                errors += 1
                continue

        unknown_targets = [target for target in model_targets(m) if target not in VALID_TARGETS]
        if unknown_targets:
            print(f"WARN: invalid target(s): {', '.join(unknown_targets)}")
            errors += 1
            continue

        compatible_targets = FORMAT_TARGETS.get(fmt)
        incompatible_targets = [
            target for target in model_targets(m)
            if compatible_targets is not None and target not in compatible_targets
        ]
        if incompatible_targets:
            allowed = ", ".join(sorted(compatible_targets))
            print(f"WARN: {fmt} incompatible with target(s): {', '.join(incompatible_targets)}; allowed: {allowed}")
            errors += 1
            continue

        print("OK")

    print()
    if errors:
        print(f"[-] {errors} issue(s) found.")
        return 1
    print("[+] All models validated successfully.")
    return 0


if __name__ == "__main__":
    metadata_only = "--metadata-only" in sys.argv
    args = [arg for arg in sys.argv[1:] if arg != "--metadata-only"]
    path = args[0] if args else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "registry.yaml")
    sys.exit(validate(path, metadata_only=metadata_only))
