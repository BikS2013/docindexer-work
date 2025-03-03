#!/usr/bin/env python3
"""Test script for --readme option."""

import sys
from docindexer.cli import main
import click

if __name__ == "__main__":
    print("Testing --readme option...")
    sys.argv = [sys.argv[0], "--readme"]
    try:
        main(standalone_mode=False)
    except click.exceptions.MissingParameter as e:
        print(f"Error: {e}")
    except click.exceptions.UsageError as e:
        print(f"Usage error: {e}")
    except SystemExit as e:
        print(f"System exit: {e}")
    print("Test completed")