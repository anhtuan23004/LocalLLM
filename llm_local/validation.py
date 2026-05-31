"""Executable validation ladder for LLM-Local."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from ruamel.yaml import YAML

from .catalog import (
    ROOT,
    compose_files,
    host_port,
    image_specs,
    is_floating_tag,
    network_name,
    runtime_check_services,
    service,
    service_dir,
    validation_commands,
)


class ValidationRunner:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def check(self, label: str, command: Sequence[str], cwd: Path | None = None) -> None:
        result = subprocess.run(command, cwd=cwd or ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if result.returncode == 0:
            print(f"  PASS {label}")
            self.passed += 1
        else:
            print(f"  FAIL {label}")
            self.failed += 1

    def check_python(self, label: str, code: str) -> None:
        self.check(label, [sys.executable, "-c", code])

    def section(self, title: str) -> None:
        print(f"=== {title} ===")

    def finish(self) -> int:
        print("")
        print(f"Results: {self.passed} passed, {self.failed} failed")
        return 1 if self.failed else 0


def run_quick(include_runtime: bool = False) -> int:
    runner = ValidationRunner()
    check_catalog(runner)
    check_compose(runner)
    check_models(runner, metadata_only=True)
    check_scripts(runner)
    check_dashboards(runner)
    check_makefile(runner)
    check_images(runner)
    if include_runtime:
        check_runtime(runner)
    else:
        runner.section("Runtime Checks")
        print("  skipped (run ./llm-local validate quick --runtime to check live services)")
    return runner.finish()


def run_integration() -> int:
    runner = ValidationRunner()
    check_catalog(runner)
    check_compose(runner)
    check_models(runner, metadata_only=True)
    return runner.finish()


def run_platform() -> int:
    runner = ValidationRunner()
    check_runtime(runner)
    return runner.finish()


def run_release() -> int:
    runner = ValidationRunner()
    check_catalog(runner)
    check_compose(runner)
    check_models(runner, metadata_only=False)
    check_scripts(runner)
    check_dashboards(runner)
    check_makefile(runner)
    check_images(runner)
    check_runtime(runner)
    return runner.finish()


def check_catalog(runner: ValidationRunner) -> None:
    runner.section("Runtime Catalog")
    runner.check_python(
        "runtime catalog loads",
        "from llm_local.catalog import load_catalog; assert load_catalog()['services']",
    )
    runner.check_python(
        "validation command registry loads",
        "from llm_local.catalog import validation_commands; assert validation_commands()",
    )


def check_compose(runner: ValidationRunner) -> None:
    runner.section("Compose Configs")
    for compose_file in compose_files():
        runner.check(str(compose_file.relative_to(ROOT)), ["docker", "compose", "-f", str(compose_file), "config"])


def check_models(runner: ValidationRunner, *, metadata_only: bool) -> None:
    runner.section("Model Registry")
    runner.check("registry.yaml exists", ["test", "-f", "models/registry.yaml"])
    runner.check("presets.yaml exists", ["test", "-f", "models/presets.yaml"])
    runner.check("convert.sh executable", ["test", "-x", "models/convert.sh"])
    runner.check("validate_registry.py exists", ["test", "-f", "models/validate_registry.py"])
    command = [sys.executable, "models/validate_registry.py"]
    label = "registry metadata validates" if metadata_only else "registry files validate"
    if metadata_only:
        command.append("--metadata-only")
    runner.check(label, command)
    runner.check("serving presets list", [sys.executable, "models/presets.py", "list"])
    runner.check(
        "serving preset dry run",
        [sys.executable, "models/presets.py", "apply", "chat-small", "--dry-run", "--render"],
    )
    runner.check(
        "serving preset add syntax",
        [
            "sh",
            "-c",
            "tmp=$(mktemp -d); cp models/presets.yaml \"$tmp/presets.yaml\"; "
            "LLM_LOCAL_PRESETS_FILE=\"$tmp/presets.yaml\" "
            f"{sys.executable} models/presets.py add --from-ollama smoke-model:latest "
            "--alias local-ollama --id smoke-model >/dev/null; rm -rf \"$tmp\"",
        ],
    )


def check_scripts(runner: ValidationRunner) -> None:
    runner.section("Scripts")
    runner.check("convert.sh syntax", ["bash", "-n", "models/convert.sh"])
    runner.check("validate_registry.py syntax", [sys.executable, "-m", "py_compile", "models/validate_registry.py"])
    runner.check("presets.py syntax", [sys.executable, "-m", "py_compile", "models/presets.py"])
    runner.check("preflight.py syntax", [sys.executable, "-m", "py_compile", "scripts/preflight.py"])
    runner.check("llm_local package syntax", ["sh", "-c", f"{sys.executable} -m py_compile llm_local/*.py"])
    runner.check("llm-local shim syntax", ["bash", "-n", "llm-local"])
    runner.check("ocr-extract app syntax", ["sh", "-c", "python3 -m py_compile clients/ocr-extract/src/*.py"])
    runner.check("ollama_exporter.py syntax", [sys.executable, "-m", "py_compile", "observation/scripts/ollama_exporter.py"])
    runner.check("run_lm_eval.sh syntax", ["sh", "-n", "evaluation/scripts/run_lm_eval.sh"])
    runner.check("mlx serve.sh syntax", ["bash", "-n", "serving/mlx/serve.sh"])
    runner.check("smoke.sh syntax", ["bash", "-n", "scripts/smoke.sh"])


def check_dashboards(runner: ValidationRunner) -> None:
    runner.section("Dashboards")
    runner.check("Grafana dashboard JSON", [sys.executable, "-m", "json.tool", "observation/grafana/dashboards/llm-local-overview.json"])


def check_makefile(runner: ValidationRunner) -> None:
    runner.section("Makefile")
    runner.check("make help", ["make", "help"])


def check_images(runner: ValidationRunner) -> None:
    runner.section("Image Pins")
    failures: list[str] = []
    for service_id, image in image_specs():
        spec = service(service_id)
        tag = str(image.get("default_tag", ""))
        if not tag:
            failures.append(f"{service_id}: missing default image tag")
        elif is_floating_tag(tag):
            failures.append(f"{service_id}: floating default tag {tag}")
        compose_file = spec.get("compose_file")
        if compose_file:
            image_value = compose_image_value(ROOT / str(compose_file), service_id, spec)
            if not image_value:
                failures.append(f"{service_id}: compose image field not found")
            else:
                repository = str(image.get("repository"))
                if repository not in image_value:
                    failures.append(f"{service_id}: compose image does not use {repository}")
                if tag and tag not in image_value:
                    failures.append(f"{service_id}: compose image does not include catalog default tag {tag}")
        env_key = image.get("tag_env")
        if env_key:
            example = service_dir(service_id) / ".env.example"
            if example.exists():
                values = parse_env_file(example)
                if env_key in values and values[env_key] != tag:
                    failures.append(
                        f"{service_id}: {example.relative_to(ROOT)} {env_key}={values[env_key]} "
                        f"does not match catalog default {tag}"
                    )
    if failures:
        for failure in failures:
            print(f"  FAIL {failure}")
            runner.failed += 1
    else:
        print("  PASS runtime catalog image defaults are pinned")
        runner.passed += 1


def compose_image_value(compose_file: Path, service_id: str, spec: dict[str, object]) -> str | None:
    data = YAML().load(compose_file.read_text()) or {}
    services = data.get("services") or {}
    candidates = [service_id, str(spec.get("container") or ""), service_id.replace(".", "-")]
    for candidate in candidates:
        if candidate and candidate in services:
            image = services[candidate].get("image")
            return str(image) if image else None
    return None


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def check_runtime(runner: ValidationRunner) -> None:
    runner.section("Runtime Network")
    runner.check(f"{network_name()} exists", ["docker", "network", "inspect", network_name()])

    runner.section("Runtime Guardrails")
    runner.check("guardrails pass", [sys.executable, "scripts/preflight.py", "--all"])

    runner.section("Runtime Health")
    for service_id in runtime_check_services():
        spec = service(service_id)
        check = spec.get("runtime_check") or {}
        container = spec.get("container")
        required = bool(check.get("required"))
        healthy_states = set(check.get("healthy_states") or ["healthy", "running"])
        if container:
            shell = (
                f"docker inspect {container} >/dev/null 2>&1"
                + ("" if required else " || exit 0")
                + f"; status=$(docker inspect --format='{{{{if .State.Health}}}}{{{{.State.Health.Status}}}}{{{{else}}}}{{{{.State.Status}}}}{{{{end}}}}' {container} 2>/dev/null); "
                + "case \"$status\" in "
                + "|".join(sorted(healthy_states))
                + ") exit 0 ;; *) exit 1 ;; esac"
            )
            runner.check(f"{service_id} health", ["sh", "-c", shell])

        endpoint = check.get("host_endpoint")
        if endpoint:
            port = host_port(service_id)
            if port is not None:
                url = str(endpoint).format(host_port=port)
                shell = f"curl -sf {json.dumps(url)}" + ("" if required else " >/dev/null 2>&1 || exit 0")
                runner.check(f"{service_id} endpoint", ["sh", "-c", shell])


def print_registry() -> int:
    commands = validation_commands()
    print("Validation commands:")
    for name, spec in commands.items():
        print(f"  {name}: {spec.get('command')} ({spec.get('ladder_level')})")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    command = args.pop(0) if args else "quick"
    if command == "quick":
        include_runtime = "--runtime" in args
        return run_quick(include_runtime=include_runtime)
    if command == "integration":
        return run_integration()
    if command == "platform":
        return run_platform()
    if command == "release":
        return run_release()
    if command == "images":
        runner = ValidationRunner()
        check_images(runner)
        return runner.finish()
    if command == "list":
        return print_registry()
    print("Usage: python -m llm_local.validation [quick|integration|platform|release|images|list] [--runtime]")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
