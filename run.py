#!/usr/bin/env python3
"""Project bootstrap and runtime checks for analyse + api stacks."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANALYSE_COMPOSE = ROOT / "analyse" / "docker-compose.yml"
API_COMPOSE = ROOT / "api" / "docker-compose.yml"
API_DIR = ROOT / "api"
VENV_DIR = ROOT / ".venv"
REQUIREMENTS_FILE = ROOT / "requirements.txt"

GO_OWL_NEW = ROOT / "data" / "gene-ontology-01-26" / "data" / "ontology" / "go.owl"
GO_OWL_OLD = ROOT / "data" / "gene-ontology-10-25" / "data" / "ontology" / "go.owl"


def log(msg: str) -> None:
    print(f"[run] {msg}")


def fail(msg: str, code: int = 1) -> None:
    print(f"[run] ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def run_cmd(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        check=False,
        text=True,
        capture_output=capture,
    )
    if check and proc.returncode != 0:
        if capture and proc.stderr:
            fail(f"Command failed ({' '.join(cmd)}): {proc.stderr.strip()}")
        fail(f"Command failed ({' '.join(cmd)}) with exit code {proc.returncode}")
    return proc


def ensure_go_files() -> None:
    missing = [str(p.relative_to(ROOT)) for p in (GO_OWL_NEW, GO_OWL_OLD) if not p.exists()]
    if missing:
        fail(
            "Missing required GO ontology file(s): "
            + ", ".join(missing)
            + ". Please place them under the data/ directory."
        )
    log("GO ontology files found.")


def ensure_venv() -> None:
    if VENV_DIR.exists():
        log(".venv already exists.")
        return
    log("Creating .venv ...")
    run_cmd([sys.executable, "-m", "venv", str(VENV_DIR)])
    log(".venv created.")


def venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def ensure_python_dependencies() -> None:
    if not REQUIREMENTS_FILE.exists():
        fail("requirements.txt not found; cannot install Python dependencies.")
    python_bin = venv_python()
    if not python_bin.exists():
        fail(f"Virtual environment Python not found at {python_bin}")
    log("Installing Python dependencies from requirements.txt ...")
    run_cmd([str(python_bin), "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)])
    log("Python dependencies installed.")


def ensure_env_file() -> None:
    env_path = API_DIR / ".env"
    env_example = API_DIR / ".env.example"
    if env_path.exists():
        log("api/.env already exists.")
        return
    if not env_example.exists():
        fail("api/.env.example not found, cannot create api/.env.")
    env_path.write_text(env_example.read_text(encoding="utf-8"), encoding="utf-8")
    log("api/.env created from api/.env.example.")


def check_docker() -> None:
    run_cmd(["docker", "--version"])
    run_cmd(["docker", "compose", "version"])
    log("Docker and Docker Compose are available.")


def run_analyse_compose() -> None:
    log("Running analyse stack (reasoner one-shot)...")
    run_cmd(
        ["docker", "compose", "-f", str(ANALYSE_COMPOSE), "run", "--rm", "reasoner"],
        cwd=ROOT,
    )
    log("analyse/reasoner completed successfully.")


def run_api_compose() -> None:
    log("Starting api stack (fuseki + loader + rdf-builder + fastapi)...")
    run_cmd(
        ["docker", "compose", "-f", str(API_COMPOSE), "up", "-d", "--build"],
        cwd=ROOT,
    )
    log("api stack started.")


def inspect_container(container_name: str) -> tuple[str, str]:
    proc = run_cmd(
        [
            "docker",
            "inspect",
            "--format",
            "{{.State.Status}}|{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}",
            container_name,
        ],
        capture=True,
        check=False,
    )
    if proc.returncode != 0:
        return "missing", "missing"
    raw = proc.stdout.strip()
    if "|" not in raw:
        return "unknown", "unknown"
    status, health = raw.split("|", 1)
    return status, health


def wait_container(
    *,
    container: str,
    timeout_s: int,
    accepted_statuses: set[str],
    accepted_health: set[str] | None = None,
) -> None:
    started = time.time()
    while True:
        status, health = inspect_container(container)
        if status in accepted_statuses:
            if accepted_health is None or health in accepted_health:
                log(f"{container}: status={status}, health={health}")
                return
        if time.time() - started > timeout_s:
            fail(
                f"Timeout waiting for {container}. "
                f"Last state: status={status}, health={health}"
            )
        time.sleep(2)


def wait_http_ok(url: str, timeout_s: int) -> None:
    started = time.time()
    while True:
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                if 200 <= resp.status < 300:
                    log(f"HTTP check OK: {url} ({resp.status})")
                    return
        except (urllib.error.URLError, TimeoutError):
            pass
        if time.time() - started > timeout_s:
            fail(f"Timeout waiting for HTTP endpoint: {url}")
        time.sleep(2)


def verify_stack() -> None:
    log("Verifying stack health...")
    wait_container(
        container="fuseki",
        timeout_s=180,
        accepted_statuses={"running"},
        accepted_health={"healthy"},
    )
    wait_container(
        container="fuseki-loader",
        timeout_s=180,
        accepted_statuses={"exited"},
    )
    wait_container(
        container="rdf-builder",
        timeout_s=300,
        accepted_statuses={"exited"},
    )
    wait_container(
        container="fastapi",
        timeout_s=180,
        accepted_statuses={"running"},
    )
    wait_http_ok("http://localhost:8000/", timeout_s=90)
    wait_http_ok("http://localhost:3030/$/ping", timeout_s=90)
    log("All checks passed.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bootstrap and run the complete ontology medical app."
    )
    parser.add_argument(
        "--skip-analyse",
        action="store_true",
        help="Skip analyse/reasoner execution.",
    )
    parser.add_argument(
        "--skip-api-up",
        action="store_true",
        help="Skip api docker compose startup.",
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip runtime verification checks.",
    )
    args = parser.parse_args()

    os.chdir(ROOT)
    check_docker()
    ensure_go_files()
    ensure_venv()
    ensure_python_dependencies()

    if not args.skip_analyse:
        run_analyse_compose()

    ensure_env_file()

    if not args.skip_api_up:
        run_api_compose()

    if not args.skip_verify:
        verify_stack()

    log("Project startup completed successfully.")


if __name__ == "__main__":
    main()
