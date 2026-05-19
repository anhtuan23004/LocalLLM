"""Model lifecycle commands: list, rm, select."""

import os
import shutil
import sys
from ruamel.yaml import YAML

yaml = YAML()
yaml.default_flow_style = False

MODELS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(MODELS_DIR)


def load_registry():
    path = os.path.join(MODELS_DIR, "registry.yaml")
    if not os.path.isfile(path):
        return []
    with open(path) as f:
        data = yaml.load(f)
    return (data or {}).get("models", [])


def model_targets(model):
    targets = model.get("serving_targets")
    if targets:
        return targets
    target = model.get("serving_target")
    return [target] if target else []


def has_target(model, target):
    return target in model_targets(model)


def list_models():
    models = load_registry()
    if not models:
        print("No models registered.")
        return
    print(f"{'ID':30s} {'FORMAT':12s} {'SIZE':8s} {'TARGETS':28s} STATUS")
    for m in models:
        targets = ",".join(model_targets(m)) or "?"
        print(f"{m['id']:30s} {m.get('format','?'):12s} "
              f"{str(m.get('size_gb','?'))+' GB':8s} "
              f"{targets:28s} {m.get('status','?')}")


def rm_model(model_id, force=False):
    model_dir = os.path.join(MODELS_DIR, model_id)
    if not os.path.isdir(model_dir):
        print(f"Model directory not found: {model_dir}")
        sys.exit(1)

    if not force:
        answer = input(f"Remove {model_id} and all its files? [y/N] ")
        if answer.lower() != "y":
            print("Aborted.")
            return

    shutil.rmtree(model_dir)
    print(f"[+] Removed {model_dir}")

    sys.path.insert(0, MODELS_DIR)
    from assemble_registry import assemble
    assemble(MODELS_DIR)


def select_model(model_id, restart=False):
    models = load_registry()
    match = next((m for m in models if m["id"] == model_id and has_target(m, "vllm")), None)
    if not match:
        print(f"Model '{model_id}' not found or not targeted for vllm.")
        print("Available:")
        for m in models:
            if has_target(m, "vllm"):
                print(f"  {m['id']}")
        sys.exit(1)

    env_file = os.path.join(ROOT_DIR, "serving", "vllm", ".env")
    if not os.path.isfile(env_file):
        print(f"[!] {env_file} not found. Copy .env.example first.")
        sys.exit(1)

    with open(env_file) as f:
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

    with open(env_file, "w") as f:
        f.writelines(new_lines)
    print(f"[+] Selected {match['id']} ({match['repo']})")

    if restart:
        import subprocess
        subprocess.run(["docker", "compose", "up", "-d"], cwd=os.path.join(ROOT_DIR, "serving", "vllm"))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        list_models()
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "list":
        list_models()
    elif cmd == "rm":
        if len(sys.argv) < 3:
            print("Usage: manage.py rm <model_id>")
            sys.exit(1)
        force = "--force" in sys.argv
        rm_model(sys.argv[2], force=force)
    elif cmd == "select":
        if len(sys.argv) < 3:
            print("Usage: manage.py select <model_id> [--restart]")
            sys.exit(1)
        restart = "--restart" in sys.argv
        select_model(sys.argv[2], restart=restart)
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
