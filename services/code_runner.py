from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Tuple


class CodeRunner:
    """Executes generated Python code in a safe subprocess."""

    def run(self, code: str) -> Tuple[str, str]:
        """Execute Python code and return stdout/stderr."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "generated_code.py"
            path.write_text(code, encoding="utf-8")
            result = subprocess.run(
                ["python", str(path)],
                capture_output=True,
                text=True,
                timeout=20,
                cwd=tmp_dir,
            )
            if result.returncode == 0:
                return "Execution succeeded", result.stdout.strip()
            return "Execution failed", result.stderr.strip() or result.stdout.strip()
