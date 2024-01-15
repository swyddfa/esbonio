#!/usr/bin/env python3
"""Book keeping around making a release.

This script will
- Generate a new version based on the environment (release, dev etc) and the changelog.
- Commit, tag and push the new version (if it's a release)
- Export the tag name and release date for use later on in the pipeline.
"""
import argparse
import io
import json
import os
import pathlib
import re
import subprocess
import sys
from datetime import datetime
from typing import Dict
from typing import Optional
from typing import TypedDict

IS_CI = "CI" in os.environ
IS_PR = os.environ.get("GITHUB_REF", "").startswith("refs/pull/")
IS_DEVELOP = os.environ.get("GITHUB_REF", "") == "refs/heads/develop"
IS_RELEASE = os.environ.get("GITHUB_REF", "") == "refs/heads/release"

ENV = os.environ.get("GITHUB_ENV", "")
STEP_SUMMARY = os.environ.get("GITHUB_STEP_SUMMARY", "")


class Output:
    """An output destination that can be logged to.

    Used to implement the ``echo "string" >> $OUTPUT`` pattern seen in bash
    """

    def __init__(self, dest: str):
        self.dest = dest
        self.fp = None

    def __enter__(self):
        if not self.dest:
            self.fp = io.StringIO()
        else:
            self.fp = open(self.dest, "a")

        return self

    def __exit__(self, exc_type, exc_value, tb):
        if isinstance(self.fp, io.StringIO):
            print(f"Captured output:\n{self.fp.getvalue()}")

        self.fp.close()

    def __rrshift__(self, other: str):
        """Implements the ```"abc" >> dest`` syntax"""
        if not self.fp:
            raise ValueError("No destination supplied!")
        self.fp.write(f"{other}\n")


class Component(TypedDict):
    """Represents a releasable component."""

    name: str
    """The name of the component."""

    bump_breaking: str
    """The version bump kind to use when breaking changes are detected."""

    bump_minor: str
    """The version bump kind to use when minor changes are detected."""

    bump_patch: str
    """The version bump kind to use when patch changes are detected."""

    commit_prefix: str
    """The prefix to give to version bump commit messages for this component."""

    src: str
    """The directory containing the component, relative to repo root."""

    tag_prefix: str
    """The prefix to give to tagged versions of this component."""


COMPONENTS: Dict[str, Component] = {
    c["name"]: c
    for c in [
        Component(
            name="extensions",
            bump_breaking="major",
            bump_minor="minor",
            bump_patch="patch",
            commit_prefix="Esbonio Extensions Release v",
            src="lib/esbonio-extensions",
            tag_prefix="esbonio-extensions-v",
        ),
        Component(
            name="lsp",
            # Everything is a beta version bump until we make a proper release
            bump_breaking="b",
            bump_minor="b",
            bump_patch="b",
            commit_prefix="Esbonio Language Server Release v",
            src="lib/esbonio",
            tag_prefix="esbonio-language-server-v",
        ),
        Component(
            name="vscode",
            # Everything is a beta version bump until we make a proper release
            bump_breaking="minor",
            bump_minor="minor",
            bump_patch="patch",
            commit_prefix="Esbonio VSCode Extension Release v",
            src="code",
            tag_prefix="esbonio-vscode-extension-v",
        ),
    ]
}


def main(component_name: str):
    component = COMPONENTS[component_name]

    version = set_version(component)
    generate_changelog(component, version)

    tag = commit_and_tag(component, version)
    date = datetime.now()

    with Output(ENV) as env:
        f"VERSION={version}" >> env
        f"RELEASE_DATE={date:%Y-%m-%d}" >> env
        f"RELEASE_TAG={tag}" >> env


def set_version(component: Component) -> str:
    """Set the next version of the given component."""

    changes = pathlib.Path(component["src"]) / "changes"

    if len(list(changes.glob("*.breaking.*"))) > 0:
        print("Breaking changes found, doing major release!")
        kind = component["bump_breaking"]

    elif len(list(changes.glob("*.feature.*"))) > 0:
        print("New features found, doing minor release!")
        kind = component["bump_minor"]

    else:
        print("Doing patch release!")
        kind = component["bump_patch"]

    run("hatch", "version", kind, cwd=component["src"])
    version = run("hatch", "version", cwd=component["src"], capture=True)
    if version is None or len(version) == 0:
        print("Unable to get version number!")
        sys.exit(1)

    if not IS_PR:
        print(f"Next version: {version!r}")
        return version

    # Make a dev build number based on the PR number
    ref = os.environ["GITHUB_REF"]
    print(f"Deriving build number from: {ref!r}")
    if not (match := re.match(r".*/([0-9]+)/.*", ref)):
        print(f"Unable to extract build number from {ref!r}!")
        sys.exit(1)

    sep = "-" if component["name"] == "vscode" else "."
    dev_version = f"{version}{sep}dev{match.group(1)}"
    run("hatch", "version", dev_version, cwd=component["src"])

    # Annoying, but necessary since hatch normalises `-` to `.`
    if component["name"] == "vscode":
        package_json = pathlib.Path(component["src"]) / "package.json"
        meta = json.loads(package_json.read_text())
        meta["version"] = dev_version
        package_json.write_text(json.dumps(meta, indent=2))

    print(f"Next version: {dev_version!r}")
    return dev_version


def generate_changelog(component: Component, version: str):
    """Generate the changelog for the release."""

    changes = pathlib.Path(component["src"]) / "changes"
    if IS_RELEASE and len(list(changes.glob("*.md"))) == 0:
        print("No changes detected, aborting")
        sys.exit(1)

    draft = run(
        *["towncrier", "build", "--draft", f"--version={version}"],
        cwd=component["src"],
        capture=True,
    )
    if draft is None or len(draft) == 0:
        print("Unable to get changelog!")
        sys.exit(1)

    draft_file = pathlib.Path(component["src"]) / ".changes.html"
    draft_file.write_text(draft)

    with Output(STEP_SUMMARY) as summary:
        f"{draft}\n\n" >> summary

    if not IS_RELEASE:
        return

    # Release notes for changelog
    run("towncrier", "build", "--yes", f"--version={version}", cwd=component["src"])


def commit_and_tag(component: Component, version: str) -> str:
    """Commit tag and push the new version."""

    tag = f"{component['tag_prefix']}{version}"
    commit = f"{component['commit_prefix']}{version}"

    if not IS_RELEASE:
        return tag

    run("git", "config", "user.name", "github-actions[bot]")
    run(
        "git",
        "config",
        "user.email",
        "41898282+github-actions[bot]@users.noreply.github.com",
    )
    run("git", "commit", "-am", commit, cwd=component["src"])

    # Other releases may have run before this, ensure that we're on the latest.
    run("git", "pull", "--rebase", "origin", "release", cwd=component["src"])
    run("git", "tag", "-a", tag, "-m", commit, cwd=component["src"])
    run("git", "push", "origin", "release", cwd=component["src"])
    run("git", "push", "origin", "--tags", cwd=component["src"])

    return tag


def run(*cmd, cwd: Optional[str] = None, capture: bool = False) -> Optional[str]:
    """Run a command"""

    result = subprocess.run(cmd, cwd=cwd, capture_output=capture)
    if result.returncode != 0:
        if capture:
            sys.stdout.buffer.write(result.stdout)
            sys.stdout.flush()
            sys.stderr.buffer.write(result.stderr)
            sys.stderr.flush()

        sys.exit(result.returncode)

    if capture:
        return result.stdout.decode("utf8").strip()

    return None


cli = argparse.ArgumentParser(description="Make a release")
cli.add_argument(
    "component",
    help="the component to make a release for.",
    choices=COMPONENTS.keys(),
)

if __name__ == "__main__":
    args = cli.parse_args()
    main(args.component)
