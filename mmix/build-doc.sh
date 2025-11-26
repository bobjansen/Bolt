#!/bin/bash
# Build script for MMIXware documentation
# Checks dependencies and builds PostScript documentation

set -e

echo "Building MMIXware documentation..."
echo ""

cd "$(dirname "$0")"

# Check for CWEB
if ! command -v cweave &> /dev/null; then
    echo "Error: cweave (CWEB) not found in PATH"
    echo "Please install CWEB: sudo apt-get install cweb"
    exit 1
fi

# Check for TeX
if ! command -v tex &> /dev/null; then
    echo "Error: tex not found in PATH"
    echo "Please install TeX Live: sudo apt-get install texlive-base"
    exit 1
fi

# Check for cwebmac.tex by trying to compile a minimal file
echo "Checking for cwebmac.tex..."
cat > /tmp/test-cwebmac.tex <<'EOF'
\input cwebmac
\bye
EOF

if ! tex -interaction=nonstopmode /tmp/test-cwebmac.tex &>/dev/null; then
    echo "Error: cwebmac.tex not found"
    echo "This file is provided by the texlive-plain-generic package"
    echo ""
    echo "To install on Debian/Ubuntu:"
    echo "  sudo apt-get install texlive-plain-generic"
    echo ""
    echo "To install on other systems, you may need to install:"
    echo "  - texlive-plain-generic (Debian/Ubuntu)"
    echo "  - texlive-plain-extra (older Debian/Ubuntu)"
    echo "  - texlive-collection-plaingeneric (Arch Linux)"
    echo "  - The full TeX Live distribution from https://www.tug.org/texlive/"
    rm -f /tmp/test-cwebmac.*
    exit 1
fi
rm -f /tmp/test-cwebmac.*
echo "✓ cwebmac.tex found"

# Check for dvips
if ! command -v dvips &> /dev/null; then
    echo "Error: dvips not found in PATH"
    echo "Please install: sudo apt-get install texlive-binaries"
    exit 1
fi

echo "✓ All dependencies found"
echo ""

# Build documentation
echo "Building documentation with make doc..."
make doc

echo ""
echo "Converting PostScript to PDF..."

# Check if ps2pdf is available
if command -v ps2pdf &> /dev/null; then
    for psfile in mmix-doc.ps mmixal-intro.ps mmix-sim-intro.ps; do
        if [ -f "$psfile" ]; then
            pdffile="${psfile%.ps}.pdf"
            echo "  Converting $psfile -> $pdffile"
            ps2pdf "$psfile" "$pdffile"
        fi
    done
    echo ""
    echo "Build complete! Generated documentation:"
    echo "  PDF files:"
    echo "    - mmix-doc.pdf - Complete MMIX architecture documentation"
    echo "    - mmixal-intro.pdf - MMIXAL assembler introduction"
    echo "    - mmix-sim-intro.pdf - MMIX simulator introduction"
    echo "  PostScript files:"
    echo "    - mmix-doc.ps"
    echo "    - mmixal-intro.ps"
    echo "    - mmix-sim-intro.ps"
    echo ""
    echo "You can view the PDFs with:"
    echo "  evince mmix-doc.pdf"
else
    echo "Warning: ps2pdf not found, skipping PDF conversion"
    echo ""
    echo "Build complete! Generated documentation:"
    echo "  - mmix-doc.ps - Complete MMIX architecture documentation"
    echo "  - mmixal-intro.ps - MMIXAL assembler introduction"
    echo "  - mmix-sim-intro.ps - MMIX simulator introduction"
    echo ""
    echo "To convert to PDF manually:"
    echo "  ps2pdf mmix-doc.ps mmix-doc.pdf"
fi
