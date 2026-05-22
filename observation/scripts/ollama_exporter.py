import json
import os
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434").rstrip("/")
PORT = int(os.environ.get("OLLAMA_EXPORTER_PORT", "9101"))
TIMEOUT_SECONDS = float(os.environ.get("OLLAMA_EXPORTER_TIMEOUT_SECONDS", "5"))


def fetch_json(path):
    url = f"{OLLAMA_BASE_URL}{path}"
    with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def label_value(value):
    return str(value).replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def labels(**values):
    filtered = {k: v for k, v in values.items() if v not in (None, "")}
    if not filtered:
        return ""
    body = ",".join(f'{key}="{label_value(value)}"' for key, value in sorted(filtered.items()))
    return f"{{{body}}}"


def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def collect_metrics():
    started = time.monotonic()
    lines = [
        "# HELP ollama_up Whether the Ollama API is reachable.",
        "# TYPE ollama_up gauge",
        "# HELP ollama_scrape_duration_seconds Time spent scraping Ollama API endpoints.",
        "# TYPE ollama_scrape_duration_seconds gauge",
        "# HELP ollama_models_total Number of models available to Ollama.",
        "# TYPE ollama_models_total gauge",
        "# HELP ollama_loaded_models_total Number of models currently loaded by Ollama.",
        "# TYPE ollama_loaded_models_total gauge",
        "# HELP ollama_model_info Available Ollama model metadata.",
        "# TYPE ollama_model_info gauge",
        "# HELP ollama_loaded_model_info Loaded Ollama model metadata.",
        "# TYPE ollama_loaded_model_info gauge",
        "# HELP ollama_loaded_model_size_bytes Loaded Ollama model size in bytes.",
        "# TYPE ollama_loaded_model_size_bytes gauge",
        "# HELP ollama_loaded_model_size_vram_bytes Loaded Ollama model VRAM size in bytes.",
        "# TYPE ollama_loaded_model_size_vram_bytes gauge",
    ]

    try:
        tags = fetch_json("/api/tags")
        ps = fetch_json("/api/ps")
        available_models = tags.get("models", [])
        loaded_models = ps.get("models", [])

        lines.append("ollama_up 1")
        lines.append(f"ollama_models_total {len(available_models)}")
        lines.append(f"ollama_loaded_models_total {len(loaded_models)}")

        for model in available_models:
            details = model.get("details", {}) or {}
            lines.append(
                "ollama_model_info"
                f"{labels(model=model.get('name'), digest=model.get('digest'), family=details.get('family'), parameter_size=details.get('parameter_size'), quantization_level=details.get('quantization_level'))} 1"
            )

        for model in loaded_models:
            details = model.get("details", {}) or {}
            model_labels = labels(
                model=model.get("name"),
                digest=model.get("digest"),
                family=details.get("family"),
                parameter_size=details.get("parameter_size"),
                quantization_level=details.get("quantization_level"),
                processor=model.get("processor"),
            )
            lines.append(f"ollama_loaded_model_info{model_labels} 1")
            lines.append(f"ollama_loaded_model_size_bytes{model_labels} {number(model.get('size'))}")
            lines.append(f"ollama_loaded_model_size_vram_bytes{model_labels} {number(model.get('size_vram'))}")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        lines.append("ollama_up 0")
        lines.append("ollama_models_total 0")
        lines.append("ollama_loaded_models_total 0")

    duration = time.monotonic() - started
    lines.append(f"ollama_scrape_duration_seconds {duration:.6f}")
    return "\n".join(lines) + "\n"


class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok\n")
            return

        if self.path != "/metrics":
            self.send_response(404)
            self.end_headers()
            return

        body = collect_metrics().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), MetricsHandler)
    print(f"ollama-exporter listening on :{PORT}, scraping {OLLAMA_BASE_URL}", flush=True)
    server.serve_forever()
