"""Derived sections: staleness from files and git log, `dokdok inputs`."""
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(not shutil.which("pandoc"), reason="pandoc not installed")


def run(*a, cwd):
    return subprocess.run([sys.executable, "-m", "dokdok.cli", *a], cwd=cwd, text=True, encoding="utf-8", capture_output=True)


@pytest.fixture
def project(tmp_path):
    assert run("new", "t", "--type", str(REPO / "doctypes" / "school-thesis"), cwd=tmp_path).returncode == 0
    p = tmp_path / "t"
    (p / "dokdok.yaml").write_text((p / "dokdok.yaml").read_text(encoding="utf-8")
                                   + "derive:\n  main-part: [results/*.txt, git-log]\n", encoding="utf-8")
    return p


def test_file_input_marks_section_stale(project):
    assert "stale" not in run("check", cwd=project).stdout
    (project / "results").mkdir(); time.sleep(0.05)
    (project / "results" / "tests.txt").write_text("42 passed\n", encoding="utf-8")
    future = time.time() + 5
    os.utime(project / "results" / "tests.txt", (future, future))
    out = run("check", cwd=project).stdout
    assert "stale: results/*.txt" in out and "dokdok inputs main-part" in out
    assert "42 passed" in run("inputs", "main-part", cwd=project).stdout


def test_git_log_is_optional(project):
    out = run("inputs", "main-part", cwd=project).stdout
    assert "no git repository" in out                       # no repo: skipped, no error
    if not shutil.which("git"):
        return
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "first commit"], cwd=project, check=True)
    assert "first commit" in run("inputs", "main-part", "--all", cwd=project).stdout
