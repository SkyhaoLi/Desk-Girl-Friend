# -*- coding: utf-8 -*-
"""单独重生成 work 状态，复用统一边缘清理逻辑"""
from fix_edges import process_state


if __name__ == "__main__":
    print("Rebuilding work state...")
    process_state("work")
    print("Done!")
