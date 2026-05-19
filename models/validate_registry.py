"""Validate model registry against filesystem."""

import os
import sys
from ruamel.yaml import YAML

yaml = YAML()

FORMAT_GLOBS = {"safetensors": ".safetensors", "gguf": ".gguf", "pytorch": ".bin"}
VALID_TARGETS = {"vllm", "sglang", "llama.cpp", "ollama", "mlx"}


def model_targets(model):
    targets = model.get("serving_targets")
    if targets:
        return targets
    target = model.get("serving_target")
    return [target] if target else []


def validate(registry_path):
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

        print("OK")

    print()
    if errors:
        print(f"[-] {errors} issue(s) found.")
        return 1
    print("[+] All models validated successfully.")
    return 0


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "registry.yaml")
    sys.exit(validate(path))
