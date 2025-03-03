#!/usr/bin/env python3
"""Test script for structure command."""

import sys
from docindexer.cli import main
import click

if __name__ == "__main__":
    print("Testing structure command with source folder...")
    test_dir = "/Users/giorgosmarinos/aiwork/rag-work/docindexer-work"
    sys.argv = [sys.argv[0], "structure", "-s", test_dir, "-l", "2", "--debug"]
    try:
        main(standalone_mode=False)
    except SystemExit as e:
        print(f"System exit: {e}")
    except Exception as e:
        print(f"Exception: {e}")
    print("Test completed")