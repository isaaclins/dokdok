"""Audience targets: same sources, different reports (pentest-report doctype)."""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(not shutil.which("pandoc"), reason="pandoc not installed")

FINDING = """---
section: findings
---

## High – Session cookie without Secure flag

**Impact.** A user on public Wi-Fi can have their session stolen.

::: {.only-for="blue-team"}
**Evidence.** `Set-Cookie: session=…; HttpOnly` without `Secure`.

**Remediation.** Add `Secure` in `config/session.php`, line 14.
:::
"""


def test_exec_and_blue_team_differ(tmp_path):
    run = lambda *a, cwd: subprocess.run([sys.executable, "-m", "dokdok.cli", *a], cwd=cwd, text=True, capture_output=True)
    assert run("new", "pt", "--type", str(REPO / "doctypes" / "pentest-report"), cwd=tmp_path).returncode == 0
    p = tmp_path / "pt"
    (p / "doc" / "03-findings.md").write_text(FINDING)
    for t in ("exec", "blue-team"):
        assert run("render", t, cwd=p).returncode == 0
    exec_md = (p / "out" / "pt-exec.md").read_text()
    blue_md = (p / "out" / "pt-blue-team.md").read_text()
    assert "Impact." in exec_md and "Remediation." not in exec_md and "# Remediation plan" not in exec_md
    assert "Remediation." in blue_md and "# Remediation plan" in blue_md and "# Appendix" in blue_md
