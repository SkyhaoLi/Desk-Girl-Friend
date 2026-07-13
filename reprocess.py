# -*- coding: utf-8 -*-
"""兼容入口：重新生成素材时请走统一处理链路"""
import os
import subprocess
import sys

STATE_ARGS = sys.argv[1:]
BASE_STATES = STATE_ARGS or ["work", "idle"]


def run_step(script, *args):
    cmd = [sys.executable, script, *args]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    states = [state for state in BASE_STATES if state]
    if not states:
        raise SystemExit("No states selected")

    run_step("extract_all.py", *states)
    run_step("rembg_proper.py", *states)
    run_step("fix_edges.py", *states)
    print("\nDone!")
