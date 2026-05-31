"""Serving preset commands for workflow-level model switching."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

from ruamel.yaml import YAML

if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from llm_local.catalog import gateway_alias, litellm_model_keys
from manage import RUNTIME_ENV_MAP, resolve_model, select_model


yaml = YAML()
ROOT = Path(__file__).resolve().parents[1]
PRESETS_FILE = Path(os.environ.get("LLM_LOCAL_PRESETS_FILE", ROOT / "models" / "presets.yaml"))
STATE_DIR = ROOT / "config" / "active"
ACTIVE_FILE = STATE_DIR / "serving.yaml"
LITELLM_DIR = ROOT / "serving" / "litellm"

LITELLM_MODEL_KEYS = litellm_model_keys()


def load_presets():
    if not PRESETS_FILE.is_file():
        print(f"ERROR: presets file not found: {PRESETS_FILE}")
        sys.exit(1)
    with PRESETS_FILE.open() as handle:
        data = yaml.load(handle) or {}
    return data.get("presets", []) or []


def save_presets(presets):
    with PRESETS_FILE.open("w") as handle:
        yaml.dump({"presets": presets}, handle)


def find_preset(preset_id):
    for preset in load_presets():
        if preset.get("id") == preset_id:
            return preset
    print(f"ERROR: unknown serving preset '{preset_id}'. Available presets:")
    for preset in load_presets():
        print(f"  {preset.get('id')}")
    sys.exit(1)


def preset_exists(preset_id):
    return any(preset.get("id") == preset_id for preset in load_presets())


def slug(value):
    result = []
    for char in value.lower():
        if char.isalnum():
            result.append(char)
        elif result and result[-1] != "-":
            result.append("-")
    return "".join(result).strip("-")


def default_preset_id(runtime, model_name):
    prefix = "chat" if runtime == "ollama" else runtime.replace(".", "-")
    return f"{prefix}-{slug(model_name)}"


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


def preset_for_registry_model(preset_id, model_id, runtime, alias=None):
    match = resolve_model(model_id, runtime=runtime)
    gateway_model = match.get("repo", model_id)
    resolved_alias = alias or gateway_alias(runtime) or f"local-{runtime.replace('.', '-')}"
    return {
        "id": preset_id,
        "description": f"{model_id} through {runtime} and the {resolved_alias} LiteLLM alias.",
        "runtime": runtime,
        "model": {
            "type": "registry",
            "id": model_id,
        },
        "gateway": {
            "alias": resolved_alias,
            "provider": "openai",
            "model": gateway_model,
        },
        "requires": [
            runtime,
            "litellm",
        ],
    }


def preset_for_ollama_model(preset_id, model_name, alias=None):
    resolved_alias = alias or gateway_alias("ollama") or "local-ollama"
    return {
        "id": preset_id,
        "description": f"{model_name} through Ollama and the {resolved_alias} LiteLLM alias.",
        "runtime": "ollama",
        "model": {
            "type": "ollama",
            "name": model_name,
        },
        "gateway": {
            "alias": resolved_alias,
            "provider": "ollama_chat",
            "model": model_name,
        },
        "requires": [
            "ollama",
            "litellm",
        ],
        "optional": [
            "open-webui",
        ],
        "setup_hint": f"docker exec ollama ollama pull {model_name}",
    }


def add_preset(args):
    runtime = "vllm"
    model_id = ""
    ollama_model = ""
    alias = None
    preset_id = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--from-model":
            i += 1
            model_id = args[i] if i < len(args) else ""
        elif arg == "--from-ollama":
            i += 1
            ollama_model = args[i] if i < len(args) else ""
            runtime = "ollama"
        elif arg == "--runtime":
            i += 1
            runtime = args[i] if i < len(args) else ""
        elif arg == "--alias":
            i += 1
            alias = args[i] if i < len(args) else ""
        elif arg == "--id":
            i += 1
            preset_id = args[i] if i < len(args) else ""
        else:
            print(f"ERROR: unknown preset add option: {arg}")
            sys.exit(1)
        i += 1

    if bool(model_id) == bool(ollama_model):
        print("ERROR: use exactly one of --from-model or --from-ollama")
        sys.exit(1)

    model_name = ollama_model or model_id
    preset_id = preset_id or default_preset_id(runtime, model_name)
    if preset_exists(preset_id):
        print(f"ERROR: preset already exists: {preset_id}")
        sys.exit(1)

    if ollama_model:
        preset = preset_for_ollama_model(preset_id, ollama_model, alias=alias)
    else:
        preset = preset_for_registry_model(preset_id, model_id, runtime, alias=alias)
    validate_preset(preset)

    presets = load_presets()
    presets.append(preset)
    save_presets(presets)
    print(f"[+] Added serving preset: {preset_id}")
    print(f"[*] Apply it with: ./llm-local preset apply {preset_id} --render")


def suggest_registry_preset(model_id, runtime):
    preset_id = default_preset_id(runtime, model_id)
    alias = gateway_alias(runtime) or f"local-{runtime.replace('.', '-')}"
    print("")
    print("Suggested preset:")
    print(
        f"./llm-local preset add --from-model {model_id} "
        f"--runtime {runtime} --alias {alias} --id {preset_id}"
    )


def suggest_ollama_preset(model_name):
    preset_id = default_preset_id("ollama", model_name)
    alias = gateway_alias("ollama") or "local-ollama"
    print("")
    print("Suggested preset:")
    print(
        f"./llm-local preset add --from-ollama {model_name} "
        f"--alias {alias} --id {preset_id}"
    )


def suggest_missing_ollama_presets(model_names):
    preset_models = {
        (preset.get("model") or {}).get("name")
        for preset in load_presets()
        if preset.get("runtime") == "ollama"
    }
    missing = [name for name in model_names if name and name not in preset_models]
    if not missing:
        print("[+] All listed Ollama models already have serving presets.")
        return
    for name in missing:
        suggest_ollama_preset(name)



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
    print("Usage: presets.py <list|show|add|apply|active|render|suggest-model|suggest-ollama|suggest-ollama-missing> ...")


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
    elif cmd == "add":
        add_preset(sys.argv[2:])
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
    elif cmd == "suggest-model":
        if len(sys.argv) < 4:
            print("Usage: presets.py suggest-model <model-id> <runtime>")
            sys.exit(1)
        suggest_registry_preset(sys.argv[2], sys.argv[3])
    elif cmd == "suggest-ollama":
        if len(sys.argv) < 3:
            print("Usage: presets.py suggest-ollama <model-name>")
            sys.exit(1)
        suggest_ollama_preset(sys.argv[2])
    elif cmd == "suggest-ollama-missing":
        suggest_missing_ollama_presets(sys.argv[2:])
    else:
        usage()
        sys.exit(1)
