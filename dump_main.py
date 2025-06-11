#!/usr/bin/env python3
import sys

def dump_main_section(path):
    printing = False
    try:
        with open(path, 'r') as f:
            for line in f:
                # once we hit the sentinel, start printing
                if not printing and line.strip() == 'if __name__ == "__main__":':
                    printing = True
                if printing:
                    sys.stdout.write(line)
    except FileNotFoundError:
        sys.exit(f"File not found: {path}")
    except IOError as e:
        sys.exit(f"I/O error({e.errno}): {e.strerror}")

def main():
    if len(sys.argv) != 2:
        sys.exit(f"Usage: {sys.argv[0]} <python_file>")
    dump_main_section(sys.argv[1])

if __name__ == "__main__":
    main()

