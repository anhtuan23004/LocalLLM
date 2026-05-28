"""Python command layer behind the ./llm-local entrypoint."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from . import validation
from .catalog import ROOT, eval_targets, network_name, service, service_dir, services_by_group, status_services


PYTHON = sys.executable


def usage() -> None:
    targets = "|".join(eval_targets())
    serving = "|".join(services_by_group("serving"))
    print(
        f"""Usage: ./llm-local <command> [args...]

Commands:
  model download <repo-id> [--target TARGET]       Download model from HuggingFace
  model convert <hf2gguf|gguf2ollama> <path>      Convert model format
  model list                                      List registered models
  model select <id> [--runtime RT] [--restart]   Select model for runtime
  model rm <model-id> [--force]                   Remove model and update registry
  model validate [--metadata-only]                Validate model registry
  preset list|show|add|apply|active               Manage serving presets
  ollama pull <model>                             Pull Ollama model and print preset suggestion
  ollama list                                     List Ollama models and suggest missing presets
  config render [--dry-run]                       Render active preset into runtime .env files
  eval run [--target {targets}] [--model NAME] [--num-requests N] [--prompt TEXT] [--api-key KEY]
  eval quality                                    Run lm-eval harness
  serve <{serving}> [up|down]                     Manage serving
  webui [up|down]                                 Manage Open WebUI client
  ocr-extract [up|down]                           Manage OCR extract client
  train [up|down]                                 Manage training
  observe [up|down|batch]                         Manage observability
  guardrails [service|--all]                      Run startup guardrails
  validate [quick|integration|platform|release]   Run validation ladder commands
  status                                          Show service and model status
  smoke [--runtime]                               Alias for validate quick
  help                                            Show this help
"""
    )


def run(command: Sequence[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd or ROOT, check=False)
    if check and result.returncode:
        raise SystemExit(result.returncode)
    return result


def ensure_network() -> None:
    inspected = subprocess.run(
        ["docker", "network", "inspect", network_name()],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if inspected.returncode != 0:
        run(["docker", "network", "create", network_name()])


def compose(service_id: str, action: str) -> int:
    spec = service(service_id)
    if service_id == "mlx":
        if action == "up":
            run([PYTHON, "scripts/preflight.py", "mlx"])
            run([str(ROOT / "serving" / "mlx" / "serve.sh")])
            return 0
        if action == "down":
            print("MLX server runs in the foreground; stop its terminal process.")
            return 0
    if action == "up":
        ensure_network()
        run([PYTHON, "scripts/preflight.py", service_id])
        run(["docker", "compose", "up", "-d"], cwd=service_dir(service_id))
        return 0
    if action == "down":
        run(["docker", "compose", "down"], cwd=service_dir(service_id))
        return 0
    print("ERROR: action must be up or down")
    return 1


def model(args: list[str]) -> int:
    if not args:
        usage()
        return 1
    command = args.pop(0)
    if command == "download":
        run([PYTHON, "models/download_model.py", *args])
    elif command == "convert":
        run(["models/convert.sh", *args])
    elif command == "list":
        run([PYTHON, "models/manage.py", "list"])
    elif command == "select":
        run([PYTHON, "models/manage.py", "select", *args])
    elif command == "rm":
        run([PYTHON, "models/manage.py", "rm", *args])
    elif command == "validate":
        run([PYTHON, "models/validate_registry.py", *args])
    else:
        usage()
        return 1
    return 0


def preset(args: list[str]) -> int:
    if not args or args[0] not in {"list", "show", "add", "apply", "active"}:
        usage()
        return 1
    run([PYTHON, "models/presets.py", *args])
    return 0


def ollama(args: list[str]) -> int:
    if not args:
        usage()
        return 1
    command = args.pop(0)
    if command == "pull":
        if not args:
            print("ERROR: ollama pull requires a model name")
            return 1
        model_name = args[0]
        run(["docker", "exec", "ollama", "ollama", "pull", model_name])
        run([PYTHON, "models/presets.py", "suggest-ollama", model_name])
        return 0
    if command == "list":
        output = subprocess.check_output(["docker", "exec", "ollama", "ollama", "list"], text=True)
        print(output, end="")
        models = [line.split()[0] for line in output.splitlines()[1:] if line.split()]
        if models:
            run([PYTHON, "models/presets.py", "suggest-ollama-missing", *models])
        return 0
    usage()
    return 1


def config(args: list[str]) -> int:
    if args[:1] != ["render"]:
        usage()
        return 1
    run([PYTHON, "models/presets.py", "render", *args[1:]])
    return 0


def eval_command(args: list[str]) -> int:
    if not args:
        usage()
        return 1
    command = args.pop(0)
    if command == "quality":
        run(["docker", "compose", "--profile", "quality", "run", "--rm", "lm-eval"], cwd=ROOT / "evaluation")
        return 0
    if command != "run":
        usage()
        return 1

    target = "ollama"
    model_name = ""
    num_requests = ""
    prompt = ""
    api_key = ""
    i = 0
    while i < len(args):
        option = args[i]
        if option in {"--target", "--model", "--num-requests", "--prompt", "--api-key"}:
            if i + 1 >= len(args):
                print(f"ERROR: {option} requires a value")
                return 1
            value = args[i + 1]
            if option == "--target":
                target = value
            elif option == "--model":
                model_name = value
            elif option == "--num-requests":
                num_requests = value
            elif option == "--prompt":
                prompt = value
            elif option == "--api-key":
                api_key = value
            i += 2
            continue
        print(f"Unknown eval run option: {option}")
        return 1

    endpoints = eval_targets()
    if target not in endpoints:
        print(f"ERROR: --target must be one of: {', '.join(endpoints)}")
        return 1
    if target == "litellm" and not api_key:
        api_key = os.environ.get("LITELLM_MASTER_KEY", "sk-local-litellm")

    run_args = ["--endpoint", endpoints[target]]
    if model_name:
        run_args += ["--model-name", model_name]
    if num_requests:
        run_args += ["--num-requests", num_requests]
    if prompt:
        run_args += ["--prompt", prompt]
    if api_key:
        run_args += ["--api-key", api_key]
    run(["docker", "compose", "run", "--rm", "evaluation", *run_args], cwd=ROOT / "evaluation")
    return 0


def observe(args: list[str]) -> int:
    action = args[0] if args else "up"
    if action == "up":
        ensure_network()
        run(["docker", "compose", "up", "-d"], cwd=ROOT / "observation")
    elif action == "down":
        run(["docker", "compose", "down"], cwd=ROOT / "observation")
    elif action == "batch":
        run(["docker", "compose", "--profile", "batch", "run", "--rm", "observation"], cwd=ROOT / "observation")
    else:
        usage()
        return 1
    return 0


def status() -> int:
    print("=== Services ===")
    for service_id in status_services():
        container = service(service_id).get("container")
        result = subprocess.run(
            ["docker", "inspect", "--format={{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}", str(container)],
            text=True,
            capture_output=True,
            check=False,
        )
        state = result.stdout.strip() if result.returncode == 0 else "not running"
        print(f"  {service_id:12s} {state}")
    print("")
    print("=== Models ===")
    run([PYTHON, "models/manage.py", "list"])
    print("")
    print("=== Active Preset ===")
    result = subprocess.run([PYTHON, "models/presets.py", "active"], cwd=ROOT, check=False)
    if result.returncode != 0:
        print("  not set")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    command = args.pop(0) if args else "help"
    if command in {"help", "--help", "-h"}:
        usage()
        return 0
    if command == "model":
        return model(args)
    if command == "preset":
        return preset(args)
    if command == "ollama":
        return ollama(args)
    if command == "config":
        return config(args)
    if command == "eval":
        return eval_command(args)
    if command == "serve":
        service_id = args[0] if args else "ollama"
        action = args[1] if len(args) > 1 else "up"
        if service_id not in services_by_group("serving"):
            print(f"ERROR: service must be one of: {', '.join(services_by_group('serving'))}")
            return 1
        return compose(service_id, action)
    if command == "webui":
        return compose("open-webui", args[0] if args else "up")
    if command == "ocr-extract":
        return compose("ocr-extract", args[0] if args else "up")
    if command == "train":
        return compose("unsloth", args[0] if args else "up")
    if command == "observe":
        return observe(args)
    if command == "guardrails":
        run([PYTHON, "scripts/preflight.py", *args])
        return 0
    if command == "validate":
        return validation.main(args)
    if command == "smoke":
        return validation.main(["quick", *args])
    if command == "status":
        return status()
    print(f"Unknown command: {command}")
    usage()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
