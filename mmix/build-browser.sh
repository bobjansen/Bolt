#!/bin/bash
# Build script for MMIXware browser version with Emscripten
# This script creates browser-compatible WASM modules for the web playground

set -e

echo "Building MMIXware for browser with Emscripten..."
echo ""

# Check if emcc is available
if ! command -v emcc &> /dev/null; then
    echo "Error: emcc (Emscripten compiler) not found in PATH"
    echo "Please install Emscripten first: https://emscripten.org/docs/getting_started/downloads.html"
    exit 1
fi

# Check if CWEB is available
if ! command -v ctangle &> /dev/null; then
    echo "Error: ctangle (CWEB) not found in PATH"
    echo "Please install CWEB first"
    exit 1
fi

cd "$(dirname "$0")"

# Generate C files from CWEB sources with change files
echo "Generating C files from CWEB sources..."

# Generate abstime.c with change file
if [ -f abstime.ch ]; then
    ctangle abstime.w abstime.ch
else
    ctangle abstime.w
fi

# Generate other C files (with change files where available)
# Only generate files needed for MVP (mmixal and mmix)
for webfile in mmix-arith mmix-io mmix-sim mmixal; do
    if [ -f "${webfile}.ch" ]; then
        echo "  Processing ${webfile}.w with change file..."
        ctangle "${webfile}.w" "${webfile}.ch"
    elif [ -f "${webfile}.w" ]; then
        ctangle "${webfile}.w"
    fi
done

echo ""
echo "Compiling with Emscripten for browser..."

# Compile abstime to JavaScript (simple build for Node.js use during build)
echo "  Building abstime.js..."
emcc -O2 -s ALLOW_MEMORY_GROWTH=1 \
    -s EXPORTED_FUNCTIONS='["_main"]' -s EXPORTED_RUNTIME_METHODS='["callMain"]' \
    abstime.c -o abstime.js

# Generate abstime.h
echo "  Generating abstime.h..."
node abstime.js > abstime.h

# Compile object files
echo "  Building mmix-arith.o..."
emcc -O2 -c mmix-arith.c -o mmix-arith.o

echo "  Building mmix-io.o..."
emcc -O2 -c mmix-io.c -o mmix-io.o

rm abstime.h

echo ""
echo "Building browser-compatible modules (with MEMFS, ES6)..."

# Build mmixal for browser
echo "  Building mmixal.js (browser version)..."
emcc -O2 -s ALLOW_MEMORY_GROWTH=1 \
    -s FORCE_FILESYSTEM=1 \
    -s EXPORTED_FUNCTIONS='["_main"]' \
    -s EXPORTED_RUNTIME_METHODS='["FS","callMain","cwrap"]' \
    -s EXIT_RUNTIME=1 \
    -s INVOKE_RUN=0 \
    -s MODULARIZE=1 \
    -s EXPORT_ES6=1 \
    -s EXPORT_NAME='createMMIXALModule' \
    -s ENVIRONMENT='web' \
    mmixal.c mmix-arith.o -o mmixal.js

# Build mmix simulator for browser
echo "  Building mmix.js (browser version)..."
node abstime.js > abstime.h
emcc -O2 -s ALLOW_MEMORY_GROWTH=1 \
    -s FORCE_FILESYSTEM=1 \
    -s EXPORTED_FUNCTIONS='["_main"]' \
    -s EXPORTED_RUNTIME_METHODS='["FS","callMain","cwrap"]' \
    -s EXIT_RUNTIME=1 \
    -s INVOKE_RUN=0 \
    -s MODULARIZE=1 \
    -s EXPORT_ES6=1 \
    -s EXPORT_NAME='createMMIXModule' \
    -s ENVIRONMENT='web' \
    mmix-sim.c mmix-arith.o mmix-io.o -o mmix.js
rm abstime.h

echo ""
echo "Build complete! Generated browser-compatible files:"
echo "  - mmixal.js / mmixal.wasm - MMIX assembler (ES6 module)"
echo "  - mmix.js / mmix.wasm - MMIX simulator (ES6 module)"
echo ""
echo "These modules are configured for browser use with:"
echo "  - MEMFS (in-memory filesystem)"
echo "  - EXIT_RUNTIME=0 (reusable modules)"
echo "  - ES6 module exports"
echo "  - Exposed FS API for virtual filesystem"
echo ""
echo "Copy these files to your web server and load them from PyScript."
echo "See ../web/ directory for the playground implementation."
