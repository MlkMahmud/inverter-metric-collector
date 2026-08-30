import os
import re
import subprocess
from typing import Any, List, Literal, Tuple, cast

import tomlkit
from tomlkit.items import Table

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.join(SCRIPT_DIR, "..")
PYPROJECT_PATH = os.path.join(ROOT_DIR, "pyproject.toml")


def exec(command: List[str]) -> str:
    response = subprocess.run(command, capture_output=True)

    if response.returncode != 0:
        raise RuntimeError(
            f"command {' '.join(command)} failed: {response.stderr.decode('ascii')}"
        )

    return response.stdout.decode("ascii")


def get_config() -> tomlkit.TOMLDocument:
    with open(PYPROJECT_PATH, "rb") as f:
        doc = tomlkit.load(f)
        project = cast(Any | None, doc["project"])

        if not project or not isinstance(project, Table):
            raise TypeError("pyproject.toml must contain a [project] table")

        version = project["version"]

        if not version or not isinstance(version, str):
            raise TypeError(
                "pyproject.toml [project] table must contain a 'version' property"
            )

        return doc


def get_bump_type(commit_message: str) -> Literal["major", "minor", "patch"]:
    if re.search(r"BREAKING CHANGE|^feat!:", commit_message, re.IGNORECASE):
        return "major"

    if re.search(r"^feat:", commit_message, re.IGNORECASE):
        return "minor"

    return "minor"


def get_next_version(commit_message: str, current_version: str) -> str:
    bump_type = get_bump_type(commit_message)
    major, minor, patch = parse_version(current_version)

    match bump_type:
        case "major":
            return f"{major + 1}.{minor}.{patch}"
        case "minor":
            return f"{major}.{minor + 1}.{patch}"
        case _:
            return f"{major}.{minor}.{patch + 1}"


def is_worktree_dirty() -> bool:
    return exec(["git", "status", "--porcelain"]) != ""


def parse_version(version: str) -> Tuple[int, int, int]:
    mtch = re.search(r"^(\d+)\.(\d+)\.(\d+)$", version)

    if not mtch:
        raise Exception(
            f'version "{version}" does not match pattern <[0-9]+.[0-9]+[0-9]+>'
        )

    return (int(mtch.group(1)), int(mtch.group(2)), int(mtch.group(3)))


def update_config_project_version(config: tomlkit.TOMLDocument, version: str):
    with open(PYPROJECT_PATH, "w") as f:
        config["project"]["version"] = version
        tomlkit.dump(config, f)


def main():
    if is_worktree_dirty():
        raise RuntimeError("git worktree contains uncommitted changes")

    config = get_config()
    commit_message = exec(["git", "log", "-1", "--pretty=%B"])

    if re.search(r"\[skip ci\]", commit_message, re.IGNORECASE):
        print("skipping version bump.")
        return

    next_version = get_next_version(
        commit_message=commit_message, current_version=config["project"]["version"]
    )

    update_config_project_version(config, next_version)

    exec(["uv", "sync"])
    exec(["git", "add", "."])
    exec(["git", "commit", "-m", f"chore: version {next_version} [skip ci]"])
    exec(["git", "tag", f"v{next_version}"])

    return


if __name__ == "__main__":
    main()
