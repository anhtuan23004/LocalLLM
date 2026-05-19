"""Generate serving/vllm/.env model config from registry.

Usage:
    python serving/vllm/select_model.py [model_id]

Without arguments, lists available vllm-targeted models.
With a model id, updates the .env VLLM_MODEL_PATH and VLLM_SERVED_MODEL_NAME.
"""

import os
import sys
from ruamel.yaml import YAML

yaml = YAML()

REGISTRY = os.path.join(os.path.dirname(__file__), "../../models/registry.yaml")
ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")


def load_vllm_models():
    with open(REGISTRY) as f:
        data = yaml.load(f)
    return [m for m in (data or {}).get("models", []) if has_target(m, "vllm")]


def has_target(model, target):
    targets = model.get("serving_targets")
    if targets:
        return target in targets
    return model.get("serving_target") == target


def list_models():
    models = load_vllm_models()
    if not models:
        print("No vllm-targeted models in registry.")
        return
    print("Available vLLM models:")
    for m in models:
        status = m.get("status", "unknown")
        print(f"  {m['id']:30s} {m['format']:12s} {m.get('size_gb', '?')} GB  [{status}]")


def select_model(model_id):
    models = load_vllm_models()
    match = next((m for m in models if m["id"] == model_id), None)
    if not match:
        print(f"Model '{model_id}' not found or not targeted for vllm.")
        sys.exit(1)

    if not os.path.isfile(ENV_FILE):
        print(f"[!] {ENV_FILE} not found. Copy .env.example first.")
        sys.exit(1)

    with open(ENV_FILE) as f:
        lines = f.readlines()

    container_path = "/models/" + os.path.basename(match["path"])
    replacements = {
        "VLLM_MODEL_PATH": container_path,
        "VLLM_SERVED_MODEL_NAME": match["repo"],
    }

    new_lines = []
    for line in lines:
        key = line.split("=")[0].strip()
        if key in replacements:
            new_lines.append(f"{key}={replacements[key]}\n")
        else:
            new_lines.append(line)

    with open(ENV_FILE, "w") as f:
        f.writelines(new_lines)
    print(f"[+] Updated {ENV_FILE}: serving {match['id']} ({match['repo']})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        list_models()
    else:
        select_model(sys.argv[1])
