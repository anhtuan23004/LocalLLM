"""Assemble models/registry.yaml from per-model sidecar files."""

import os
import sys
from ruamel.yaml import YAML

yaml = YAML()
yaml.default_flow_style = False

HEADER = "# Model Registry — LLM-Local\n# Auto-generated from per-model sidecar files.\n\n"


def normalize_model(data):
    """Keep legacy serving_target entries compatible with serving_targets."""
    targets = data.get("serving_targets")
    legacy_target = data.get("serving_target")

    if not targets and legacy_target:
        data["serving_targets"] = [legacy_target]
    elif targets and not legacy_target:
        data["serving_target"] = targets[0]

    return data


def collect_sidecars(base_dir):
    models = []
    for entry in sorted(os.listdir(base_dir)):
        sidecar = os.path.join(base_dir, entry, "model.yaml")
        if os.path.isfile(sidecar):
            with open(sidecar) as f:
                data = yaml.load(f)
            if data:
                models.append(normalize_model(data))
    return models


def assemble(base_dir):
    models = collect_sidecars(base_dir)
    registry_path = os.path.join(base_dir, "registry.yaml")
    with open(registry_path, "w") as f:
        f.write(HEADER)
        yaml.dump({"models": models}, f)
    print(f"[+] Wrote {registry_path} with {len(models)} model(s)")


if __name__ == "__main__":
    base = sys.argv[1] if len(sys.argv) > 1 else "models"
    assemble(base)
