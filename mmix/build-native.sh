#!/bin/bash
# Build script for MMIXware with native compiler (clang)
# Uses change files to fix C99 compatibility warnings

set -e

echo "Building MMIXware with native compiler (clang)..."
echo ""

# Check if clang is available
if ! command -v clang &> /dev/null; then
    echo "Warning: clang not found, using default CC"
    CC=${CC:-gcc}
else
    CC=clang
fi

# Check if CWEB is available
if ! command -v ctangle &> /dev/null; then
    echo "Error: ctangle (CWEB) not found in PATH"
    echo "Please install CWEB first"
    exit 1
fi

cd "$(dirname "$0")"

echo "Using compiler: $CC"
echo ""

# Build using make
CC=$CC make all

echo ""
echo "Build complete! Generated executables:"
echo "  - mmixal - MMIX assembler"
echo "  - mmix   - MMIX simulator"
echo "  - mmotype - MMIX object file utility"
echo "  - mmmix  - MMIX pipelined meta-simulator"
echo ""
echo "Example usage:"
echo "  ./mmixal copy.mms"
echo "  ./mmix copy copy.mms"
