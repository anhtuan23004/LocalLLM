"""Serving preset commands for workflow-level model switching."""

import shutil
import subprocess
import sys
from pathlib import Path

from ruamel.yaml import YAML

from manage import RUNTIME_ENV_MAP, resolve_model, select_model


yaml = YAML()
ROOT = Path(__file__).resolve().parents[1]
PRESETS_FILE = ROOT / "models" / "presets.yaml"
STATE_DIR = ROOT / "config" / "active"
ACTIVE_FILE = STATE_DIR / "serving.yaml"
LITELLM_DIR = ROOT / "serving" / "litellm"

LITELLM_MODEL_KEYS = {
    "ollama": "OLLAMA_LITELLM_MODEL",
    "vllm": "VLLM_LITELLM_MODEL",
    "sglang": "SGLANG_LITELLM_MODEL",
    "llama.cpp": "LLAMA_CPP_LITELLM_MODEL",
    "mlx": "MLX_LITELLM_MODEL",
}


def load_presets():
    if not PRESETS_FILE.is_file():
        print(f"ERROR: presets file not found: {PRESETS_FILE}")
        sys.exit(1)
    with PRESETS_FILE.open() as handle:
        data = yaml.load(handle) or {}
    return data.get("presets", []) or []


def find_preset(preset_id):
    for preset in load_presets():
        if preset.get("id") == preset_id:
            return preset
    print(f"ERROR: unknown serving preset '{preset_id}'. Available presets:")
    for preset in load_presets():
        print(f"  {preset.get('id')}")
    sys.exit(1)


def list_presets():
    presets = load_presets()
    if not presets:
        print("No serving presets configured.")
        return
    print(f"{'ID':20s} {'RUNTIME':12s} {'MODEL':30s} GATEWAY_ALIAS")
    for preset in presets:
        model = model_label(preset)
        gateway = preset.get("gateway") or {}
        print(
            f"{preset.get('id','?'):20s} {preset.get('runtime','?'):12s} "
            f"{model:30s} {gateway.get('alias','-')}"
        )


def show_preset(preset_id):
    preset = find_preset(preset_id)
    yaml.dump(preset, sys.stdout)


def model_label(preset):
    model = preset.get("model") or {}
    if isinstance(model, str):
        return model
    return model.get("id") or model.get("name") or "?"


def litellm_model_string(preset):
    gateway = preset.get("gateway") or {}
    provider = gateway.get("provider")
    model = gateway.get("model")
    if not provider or not model:
        print(f"ERROR: preset '{preset.get('id')}' needs gateway.provider and gateway.model")
        sys.exit(1)
    return f"{provider}/{model}"


def active_state_for(preset):
    gateway = preset.get("gateway") or {}
    return {
        "active": {
            "preset_id": preset.get("id"),
            "runtime": preset.get("runtime"),
            "model": preset.get("model") or {},
            "gateway": {
                "alias": gateway.get("alias"),
                "provider": gateway.get("provider"),
                "model": gateway.get("model"),
                "litellm_model": litellm_model_string(preset),
            },
        }
    }


def write_active_state(state):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with ACTIVE_FILE.open("w") as handle:
        yaml.dump(state, handle)


def load_active_state():
    if not ACTIVE_FILE.is_file():
        print(f"ERROR: active config not found: {ACTIVE_FILE}")
        print("Run: ./llm-local preset apply <id>")
        sys.exit(1)
    with ACTIVE_FILE.open() as handle:
        return yaml.load(handle) or {}


def show_active():
    yaml.dump(load_active_state(), sys.stdout)


def ensure_env_file(env_dir):
    env_file = env_dir / ".env"
    if env_file.is_file():
        return env_file
    example = env_dir / ".env.example"
    if not example.is_file():
        print(f"ERROR: missing env file and example: {env_file}")
        sys.exit(1)
    shutil.copy2(example, env_file)
    return env_file


def update_env(env_file, replacements):
    existing = set()
    new_lines = []
    for line in env_file.read_text().splitlines(keepends=True):
        key = line.split("=", 1)[0].strip()
        if key in replacements:
            new_lines.append(f"{key}={replacements[key]}\n")
            existing.add(key)
        else:
            new_lines.append(line)
    for key, value in replacements.items():
        if key not in existing:
            new_lines.append(f"{key}={value}\n")
    env_file.write_text("".join(new_lines))


def restart_compose(relative_dir):
    subprocess.run(["docker", "compose", "up", "-d"], cwd=ROOT / relative_dir, check=True)


def validate_preset(preset):
    preset_id = preset.get("id")
    runtime = preset.get("runtime")
    if runtime not in LITELLM_MODEL_KEYS:
        print(f"ERROR: preset '{preset_id}' has unsupported runtime: {runtime}")
        sys.exit(1)

    model = preset.get("model") or {}
    if not isinstance(model, dict):
        print(f"ERROR: preset '{preset_id}' model must be a mapping")
        sys.exit(1)

    model_type = model.get("type")
    if model_type == "registry":
        model_id = model.get("id")
        if not model_id:
            print(f"ERROR: preset '{preset_id}' registry model needs model.id")
            sys.exit(1)
        if runtime not in RUNTIME_ENV_MAP:
            print(f"ERROR: preset '{preset_id}' uses registry model but runtime '{runtime}' has no env mapping")
            sys.exit(1)
        resolve_model(model_id, runtime=runtime)
    elif model_type == "ollama":
        if runtime != "ollama":
            print(f"ERROR: preset '{preset_id}' uses ollama model type with runtime '{runtime}'")
            sys.exit(1)
        if not model.get("name"):
            print(f"ERROR: preset '{preset_id}' ollama model needs model.name")
            sys.exit(1)
    else:
        print(f"ERROR: preset '{preset_id}' has unsupported model.type: {model_type}")
        sys.exit(1)

    litellm_model_string(preset)


def apply_preset(preset_id, restart=False, pull=False, dry_run=False, render=False):
    preset = find_preset(preset_id)
    validate_preset(preset)
    state = active_state_for(preset)

    if dry_run:
        print(f"[*] Would write active state: {ACTIVE_FILE}")
        yaml.dump(state, sys.stdout)
    else:
        write_active_state(state)
        print(f"[+] Active serving preset: {preset_id}")
        print(f"[+] Wrote {ACTIVE_FILE}")

    if render or restart:
        render_active(state=state, dry_run=dry_run)

    runtime = preset.get("runtime")
    model = preset.get("model") or {}
    if runtime == "ollama" and pull:
        model_name = model.get("name")
        if not model_name:
            print(f"ERROR: preset '{preset_id}' has no Ollama model name to pull")
            sys.exit(1)
        if dry_run:
            print(f"[*] Would pull Ollama model {model_name}")
        else:
            restart_compose("serving/ollama")
            subprocess.run(["docker", "exec", "ollama", "ollama", "pull", model_name], check=True)

    if restart:
        if dry_run:
            print(f"[*] Would restart {runtime} and litellm")
        elif runtime in RUNTIME_ENV_MAP and runtime != "mlx":
            restart_compose(RUNTIME_ENV_MAP[runtime]["dir"])
        elif runtime == "mlx":
            print("[*] MLX runs on host; restart its foreground process manually.")
        if not dry_run:
            restart_compose("serving/litellm")

    if preset.get("setup_hint") and not pull:
        print(f"[*] Setup hint: {preset['setup_hint']}")


def render_active(state=None, dry_run=False):
    if state is None:
        state = load_active_state()
    active = state.get("active") or {}
    runtime = active.get("runtime")
    if runtime not in LITELLM_MODEL_KEYS:
        print(f"ERROR: active runtime is unsupported: {runtime}")
        sys.exit(1)

    model = active.get("model") or {}
    if model.get("type") == "registry":
        model_id = model.get("id")
        if dry_run:
            print(f"[*] Would render runtime model {model_id} for {runtime}")
        else:
            select_model(model_id, runtime=runtime, restart=False)

    gateway = active.get("gateway") or {}
    litellm_model = gateway.get("litellm_model")
    if not litellm_model:
        print("ERROR: active gateway.litellm_model is missing")
        sys.exit(1)
    replacements = {LITELLM_MODEL_KEYS[runtime]: litellm_model}
    if dry_run:
        print(f"[*] Would render LiteLLM env: {replacements}")
        return
    litellm_env = ensure_env_file(LITELLM_DIR)
    update_env(litellm_env, replacements)
    print(f"[+] Rendered LiteLLM {gateway.get('alias')} -> {litellm_model}")


def usage():
    print("Usage: presets.py <list|show|apply|active|render> [preset-id] [--restart] [--pull] [--render] [--dry-run]")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "list":
        list_presets()
    elif cmd == "show":
        if len(sys.argv) < 3:
            usage()
            sys.exit(1)
        show_preset(sys.argv[2])
    elif cmd == "apply":
        if len(sys.argv) < 3:
            usage()
            sys.exit(1)
        apply_preset(
            sys.argv[2],
            restart="--restart" in sys.argv,
            pull="--pull" in sys.argv,
            render="--render" in sys.argv,
            dry_run="--dry-run" in sys.argv,
        )
    elif cmd == "active":
        show_active()
    elif cmd == "render":
        render_active(dry_run="--dry-run" in sys.argv)
    else:
        usage()
        sys.exit(1)
