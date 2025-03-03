#!/usr/bin/env python3
"""Test script for default help."""

import sys
from docindexer.cli import main
import click

if __name__ == "__main__":
    print("Testing default help...")
    sys.argv = [sys.argv[0]]
    try:
        main(standalone_mode=False)
    except SystemExit as e:
        print(f"System exit: {e}")
    print("Test completed")