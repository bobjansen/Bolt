#!/bin/bash
# Build script for MMIXware with Emscripten
# This script applies change files and builds with emcc

set -e

echo "Building MMIXware with Emscripten..."
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
for webfile in mmix-arith mmix-io mmix-sim mmixal mmotype mmmix mmix-pipe mmix-config mmix-mem; do
    if [ -f "${webfile}.ch" ]; then
        echo "  Processing ${webfile}.w with change file..."
        ctangle "${webfile}.w" "${webfile}.ch"
    elif [ -f "${webfile}.w" ]; then
        ctangle "${webfile}.w"
    fi
done

echo ""
echo "Compiling with Emscripten..."

# Compile abstime to JavaScript (without ES6 export for command-line use)
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

echo "  Building mmix-pipe.o..."
emcc -O2 -c mmix-pipe.c -o mmix-pipe.o

echo "  Building mmix-config.o..."
emcc -O2 -c mmix-config.c -o mmix-config.o

echo "  Building mmix-mem.o..."
emcc -O2 -c mmix-mem.c -o mmix-mem.o

rm abstime.h

# Build executables
echo "  Building mmixal.js..."
emcc -O2 -s ALLOW_MEMORY_GROWTH=1 -s NODERAWFS=1 -s FORCE_FILESYSTEM=1 \
    -s EXPORTED_FUNCTIONS='["_main"]' -s EXPORTED_RUNTIME_METHODS='["callMain"]' \
    -s EXIT_RUNTIME=1 \
    mmixal.c mmix-arith.o -o mmixal.js

echo "  Building mmix.js..."
node abstime.js > abstime.h
emcc -O2 -s ALLOW_MEMORY_GROWTH=1 -s NODERAWFS=1 -s FORCE_FILESYSTEM=1 \
    -s EXPORTED_FUNCTIONS='["_main"]' -s EXPORTED_RUNTIME_METHODS='["callMain"]' \
    -s EXIT_RUNTIME=1 \
    mmix-sim.c mmix-arith.o mmix-io.o -o mmix.js
rm abstime.h

echo "  Building mmotype.js..."
emcc -O2 -s ALLOW_MEMORY_GROWTH=1 -s NODERAWFS=1 -s FORCE_FILESYSTEM=1 \
    -s EXPORTED_FUNCTIONS='["_main"]' -s EXPORTED_RUNTIME_METHODS='["callMain"]' \
    -s EXIT_RUNTIME=1 \
    mmotype.c -o mmotype.js

echo "  Building mmmix.js..."
node abstime.js > abstime.h
emcc -O2 -s ALLOW_MEMORY_GROWTH=1 -s NODERAWFS=1 -s FORCE_FILESYSTEM=1 \
    -s EXPORTED_FUNCTIONS='["_main"]' -s EXPORTED_RUNTIME_METHODS='["callMain"]' \
    -s EXIT_RUNTIME=1 \
    mmmix.c mmix-arith.o mmix-pipe.o mmix-config.o mmix-mem.o mmix-io.o -o mmmix.js
rm abstime.h

echo ""
echo "Build complete! Generated files:"
echo "  - abstime.js/abstime.wasm"
echo "  - mmixal.js/mmixal.wasm"
echo "  - mmix.js/mmix.wasm"
echo "  - mmotype.js/mmotype.wasm"
echo "  - mmmix.js/mmmix.wasm"
echo ""
echo "You can run these with Node.js, e.g.:"
echo "  node mmixal.js <arguments>"
