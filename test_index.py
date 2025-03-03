#!/usr/bin/env python3
"""Test script for index command."""

import sys
from docindexer.cli import main
import click

if __name__ == "__main__":
    print("Testing index command...")
    sys.argv = [sys.argv[0], "index", "--help"]
    try:
        main(standalone_mode=False)
    except SystemExit as e:
        print(f"System exit: {e}")
    print("Test completed")