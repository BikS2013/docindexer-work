#!/usr/bin/env python3
"""Test script for config command."""

import sys
import os
from docindexer.cli import main
import click

if __name__ == "__main__":
    print("Testing config command with file filtering options...")
    test_dir = os.path.abspath(os.path.dirname(__file__))
    sys.argv = [sys.argv[0], "config", "--create-local", "-s", test_dir, 
                "-p", "*.md", "-l", "5", "--omit-properties", "items,vectorize", "--debug"]
    try:
        main(standalone_mode=False)
    except SystemExit as e:
        print(f"System exit: {e}")
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()
    print("Test completed")