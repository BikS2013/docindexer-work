#!/usr/bin/env python3
"""Test script for structure command."""

import sys
from docindexer.cli import main
import click

if __name__ == "__main__":
    print("Testing structure command help...")
    sys.argv = [sys.argv[0], "structure", "--help"]
    try:
        main(standalone_mode=False)
    except SystemExit as e:
        print(f"System exit: {e}")
    print("Test completed")