#!/usr/bin/env python3
"""Test runner script for The Floor Is a Lie."""

import os
import subprocess
import sys


def run_tests():
    """Run the test suite."""
    # Set up environment
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"

    # Run pytest
    cmd = [sys.executable, "-m", "pytest"]
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])

    result = subprocess.run(cmd, env=env)

    return result.returncode


if __name__ == "__main__":
    sys.exit(run_tests())
