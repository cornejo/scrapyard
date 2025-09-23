#! /usr/bin/env python3

import subprocess

from pathlib import Path
from dataclasses import dataclass, field


# -----------------------------
# Data structures
# -----------------------------
@dataclass
class GitFile:
    path: str
    contents: str


@dataclass
class GitCommit:
    message: str
    files: list[GitFile] = field(default_factory=lambda: [])
    tag: str | None = None


@dataclass
class GitBranch:
    name: str
    commits: list[GitCommit] = field(default_factory=lambda: [])
    # Optional: base branch to create from
    base: str | None = None


@dataclass
class GitRepo:
    path: Path
    branches: list[GitBranch] = field(default_factory=lambda: [])


# -----------------------------
# Centralized git runner
# -----------------------------
def run_git(cwd: Path, *args: str) -> str:
    """
    Run git command in subprocess, raising an error if it fails.
    """
    print(f"Running @ {cwd}: git", " ".join(args))

    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Git command failed: git {' '.join(args)}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result.stdout.strip()


# -----------------------------
# Repo builder
# -----------------------------
def create_git_repo(repo: GitRepo) -> None:
    if (repo.path / ".git").exists():
        raise FileExistsError(f"Path {repo.path} already exists.")

    repo.path.mkdir(parents=True, exist_ok=True)

    # Initialize git repo
    run_git(repo.path, "init")

    # Create branches
    for branch in repo.branches:
        # Checkout base if specified, else first branch becomes main
        if branch.base:
            run_git(repo.path, "checkout", "-b", branch.name, branch.base)
        else:
            run_git(repo.path, "checkout", "-b", branch.name)

        # Add commits
        for commit in branch.commits:
            # Write files
            for f in commit.files:
                file_path = repo.path / f.path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(f.contents)

            # Stage files
            run_git(repo.path, "add", ".")

            # Commit
            run_git(repo.path, "commit", "-m", commit.message)

            # Tag if needed
            if commit.tag:
                run_git(repo.path, "tag", commit.tag)


# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    repo = GitRepo(
        path=Path("/tmp/my_test_repo"),
        branches=[
            GitBranch(
                name="main",
                commits=[
                    GitCommit(
                        message="Initial commit",
                        files=[
                            GitFile("README.md", "# My Project\n"),
                        ],
                    ),
                    GitCommit(
                        message="Add LICENSE",
                        files=[
                            GitFile("LICENSE", "MIT License"),
                        ],
                        tag="v1.0",
                    ),
                ],
            ),
            GitBranch(
                name="feature-branch",
                base="main",
                commits=[
                    GitCommit(
                        message="Add feature",
                        files=[
                            GitFile("feature.txt", "New feature code"),
                            GitFile("LICENSE", "Some other license"),
                        ],
                    ),
                ],
            ),
        ],
    )

    create_git_repo(repo)
    print(f"Repo created at {repo.path}")
