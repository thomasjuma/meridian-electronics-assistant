from __future__ import annotations

import shutil
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
PACKAGE_DIR = ROOT_DIR / "lambda-package"
OUTPUT_ZIP = ROOT_DIR / "lambda-deployment.zip"
PYPROJECT_FILE = ROOT_DIR / "pyproject.toml"


def run_command(command: list[str]) -> None:
    subprocess.run(command, check=True)


def read_dependencies() -> list[str]:
    if not PYPROJECT_FILE.exists():
        raise FileNotFoundError(f"Missing {PYPROJECT_FILE}")

    with PYPROJECT_FILE.open("rb") as file:
        pyproject = tomllib.load(file)

    dependencies = pyproject.get("project", {}).get("dependencies", [])
    if not isinstance(dependencies, list):
        raise ValueError("Invalid pyproject dependencies format.")

    # Ensure FastAPI can run behind API Gateway in Lambda.
    if not any(dep.split(">=")[0].strip() == "mangum" for dep in dependencies):
        dependencies.append("mangum>=0.19.0")

    return dependencies


def prepare_workspace() -> None:
    if PACKAGE_DIR.exists():
        shutil.rmtree(PACKAGE_DIR)
    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()
    PACKAGE_DIR.mkdir(parents=True)


def install_dependencies(dependencies: list[str]) -> None:
    print("Installing dependencies...")
    # Some uv-managed interpreters do not ship pip by default.
    # Bootstrap it so packaging works in local and CI runs.
    pip_probe = [sys.executable, "-m", "pip", "--version"]
    try:
        run_command(pip_probe)
    except subprocess.CalledProcessError:
        print("pip not found in current interpreter. Bootstrapping pip with ensurepip...")
        run_command([sys.executable, "-m", "ensurepip", "--upgrade"])

    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        "--target",
        str(PACKAGE_DIR),
        *dependencies,
    ]
    run_command(command)


def prune_package() -> None:
    print("Pruning unnecessary package files...")
    remove_patterns = (
        "__pycache__",
        "*.pyc",
        "*.pyo",
        "*.dist-info",
        "*.egg-info",
    )
    remove_dirs_named = {"tests", "test", ".pytest_cache"}

    for path in PACKAGE_DIR.rglob("*"):
        if not path.exists():
            continue

        if path.is_dir() and path.name in remove_dirs_named:
            shutil.rmtree(path, ignore_errors=True)
            continue

        if path.match("**/__pycache__"):
            shutil.rmtree(path, ignore_errors=True)
            continue

        if path.is_file():
            for pattern in remove_patterns:
                if path.match(pattern) or path.match(f"**/{pattern}"):
                    path.unlink(missing_ok=True)
                    break


def copy_application_files() -> None:
    print("Copying application source files...")
    shutil.copy2(ROOT_DIR / "main.py", PACKAGE_DIR / "main.py")
    shutil.copytree(
        ROOT_DIR / "app",
        PACKAGE_DIR / "app",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )

    lambda_handler = (
        "from mangum import Mangum\n"
        "from main import app\n\n"
        "handler = Mangum(app)\n"
    )
    (PACKAGE_DIR / "lambda_handler.py").write_text(lambda_handler, encoding="utf-8")


def create_zip() -> None:
    print("Creating lambda-deployment.zip...")
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as archive:
        for file in PACKAGE_DIR.rglob("*"):
            if file.is_file():
                archive.write(file, file.relative_to(PACKAGE_DIR))


def main() -> None:
    print("Preparing Lambda deployment package...")
    dependencies = read_dependencies()
    prepare_workspace()
    install_dependencies(dependencies)
    prune_package()
    copy_application_files()
    create_zip()

    size_mb = OUTPUT_ZIP.stat().st_size / (1024 * 1024)
    print(f"Created {OUTPUT_ZIP.name} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()