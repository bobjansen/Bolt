#!/bin/bash
# Wrapper script to run MMIXware JavaScript versions with Node.js
# Usage: ./run-wrapper.sh <tool> [arguments]
# Example: ./run-wrapper.sh mmixal -l copy.lst copy.mms

set -e

TOOL="$1"
shift

if [ -z "$TOOL" ]; then
    echo "Usage: $0 <tool> [arguments]"
    echo ""
    echo "Available tools:"
    echo "  mmixal   - MMIX assembler"
    echo "  mmix     - MMIX simulator"
    echo "  mmotype  - MMIX object file type utility"
    echo "  mmmix    - MMIX pipelined meta-simulator"
    echo ""
    echo "Example: $0 mmixal -l copy.lst copy.mms"
    exit 1
fi

cd "$(dirname "$0")"

if [ ! -f "${TOOL}.js" ]; then
    echo "Error: ${TOOL}.js not found"
    echo "Please run ./build-emscripten.sh first"
    exit 1
fi

# Run the tool with Node.js
node "${TOOL}.js" "$@"
