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


RUNTIME_ENV_MAP = {
    "vllm": {
        "dir": "serving/vllm",
        "keys": {"VLLM_MODEL_PATH": "/models/{name}", "VLLM_SERVED_MODEL_NAME": "{repo}"},
    },
    "sglang": {
        "dir": "serving/sglang",
        "keys": {"SGLANG_MODEL_PATH": "/models/{name}"},
    },
    "llama.cpp": {
        "dir": "serving/llama.cpp",
        "keys": {"LLAMA_CPP_MODEL_PATH": "/models/{name}"},
    },
    "mlx": {
        "dir": "serving/mlx",
        "keys": {"MLX_MODEL": "{path}"},
    },
}

FORMAT_TARGETS = {
    "safetensors": {"vllm", "sglang", "mlx"},
    "pytorch": {"vllm", "sglang", "mlx"},
    "gguf": {"llama.cpp", "ollama"},
}


def resolve_model(model_id, runtime="vllm"):
    if runtime not in RUNTIME_ENV_MAP:
        print(f"ERROR: unknown runtime '{runtime}'. Choose from: {', '.join(RUNTIME_ENV_MAP)}")
        sys.exit(1)

    models = load_registry()
    match = next((m for m in models if m["id"] == model_id and has_target(m, runtime)), None)
    if not match:
        print(f"Model '{model_id}' not found or not targeted for {runtime}.")
        print("Available:")
        for m in models:
            if has_target(m, runtime):
                print(f"  {m['id']}")
        sys.exit(1)

    compatible_targets = FORMAT_TARGETS.get(match.get("format", ""))
    if compatible_targets is not None and runtime not in compatible_targets:
        allowed = ", ".join(sorted(compatible_targets))
        print(
            f"ERROR: model '{model_id}' format '{match.get('format')}' "
            f"is not compatible with {runtime}. Allowed runtime(s): {allowed}"
        )
        sys.exit(1)

    return match


def select_model(model_id, runtime="vllm", restart=False):
    match = resolve_model(model_id, runtime=runtime)
    cfg = RUNTIME_ENV_MAP[runtime]
    env_dir = os.path.join(ROOT_DIR, cfg["dir"])
    env_file = os.path.join(env_dir, ".env")

    # Create .env from .env.example if missing
    if not os.path.isfile(env_file):
        example = os.path.join(env_dir, ".env.example")
        if os.path.isfile(example):
            import shutil as _shutil
            _shutil.copy2(example, env_file)
        else:
            print(f"[!] {env_file} not found.")
            sys.exit(1)

    with open(env_file) as f:
        lines = f.readlines()

    name = os.path.basename(match["path"])
    replacements = {
        k: v.format(name=name, repo=match["repo"], path=match["path"])
        for k, v in cfg["keys"].items()
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
    print(f"[+] Selected {match['id']} for {runtime}")

    if restart:
        import subprocess
        if runtime == "mlx":
            print("[*] MLX runs on host — restart manually.")
        else:
            subprocess.run(["docker", "compose", "up", "-d"], cwd=env_dir)


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
            print("Usage: manage.py select <model_id> [--runtime RUNTIME] [--restart]")
            sys.exit(1)
        restart = "--restart" in sys.argv
        runtime = "vllm"
        if "--runtime" in sys.argv:
            idx = sys.argv.index("--runtime")
            if idx + 1 < len(sys.argv):
                runtime = sys.argv[idx + 1]
        select_model(sys.argv[2], runtime=runtime, restart=restart)
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
