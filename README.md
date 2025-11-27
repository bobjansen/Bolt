# MMIX Interactive Playground

A browser-based interactive environment for writing, assembling, and running
[MMIX](https://mmix.cs.hm.edu/) assembly code, powered by Donald E. Knuth's
MMIXware compiled to WebAssembly.

## What is MMIX?

MMIX is a 64-bit RISC architecture designed by Donald E. Knuth for his seminal
work *The Art of Computer Programming* (TAOCP). It serves as the successor to
the MIX architecture and provides a modern, clean instruction set for teaching
computer science fundamentals.

This project brings MMIX to your browser - no installation required!

## Web Interface

Try it live at: **[https://bolt.bobjansen.net](https://bolt.bobjansen.net)**

### Features

- **Interactive Code Editor**: Write MMIX assembly code directly in your browser
- **One-Click Execution**: Assemble and run with a single button (or press `Ctrl+Enter`)
- **Real-time Output**: See your program's output immediately
- **Assembly Listing**: View the assembled machine code and symbol tables
- **Example Programs**: Learn from working examples including:
  - Hello World
  - Fibonacci sequence generator
  - File copy utility

### How to Use

1. **Write Code**: Enter MMIX assembly code in the left panel, or select an example from the dropdown
2. **Run**: Click "Assemble & Run" or press `Ctrl+Enter` (or `Cmd+Enter` on Mac)
3. **View Output**: The simulation output appears in the right panel
4. **Explore Tabs**:
   - **Simulation Output**: Your program's output
   - **Assembly Listing**: Detailed assembly listing with addresses and machine code
   - **Messages**: Assembly and simulation messages

### Quick Example

```mmix
        LOC  #100
Main    GETA $255,String
        TRAP 0,Fputs,StdOut
        TRAP 0,Halt,0
String  BYTE "Hello, MMIX!",#a,0
```

Press `Ctrl+Enter` and watch it run!

## Architecture

This project consists of:

- **MMIXware Tools**: Knuth's original CWEB sources compiled to:
  - Native binaries (mmixal, mmix, mmotype, mmmix)
  - WebAssembly modules (for browser use)
- **Web Playground**: PyScript-based interface using:
  - PyScript/Pyodide (Python in the browser via WebAssembly)
  - Emscripten-compiled MMIX tools
  - Clean, TAOCP-inspired design

## Project Structure

```
.
├── web/                      # Web playground
│   ├── index.html           # Main HTML interface
│   ├── style.css            # TAOCP-inspired styling
│   ├── mmix-playground.py   # PyScript application
│   └── pyscript.toml        # PyScript configuration
├── mmix/                     # MMIX tools
│   ├── *.w                  # Original CWEB source files
│   ├── *.ch                 # Change files (C99, Emscripten compatibility)
│   ├── build-native.sh      # Build native binaries
│   ├── build-browser.sh     # Build WebAssembly modules
│   ├── build-doc.sh         # Build PDF documentation
│   ├── mmixal, mmix, ...    # Native executables
│   └── *.js, *.wasm         # WebAssembly modules
└── README.md
```

## Building from Source

### Prerequisites

- **CWEB**: Knuth's literate programming system
  ```bash
  sudo apt install texlive-binaries  # Debian/Ubuntu
  ```
- **Emscripten**: For WebAssembly builds
  ```bash
  # Follow installation instructions at:
  # https://emscripten.org/docs/getting_started/downloads.html
  ```
- **Clang**: For native builds (optional)
  ```bash
  sudo apt install clang
  ```

### Build Native Tools

```bash
cd mmix
./build-native.sh
```

This generates:
- `mmixal` - MMIX assembler
- `mmix` - MMIX simulator
- `mmotype` - Object file inspector
- `mmmix` - Meta-simulator

### Build WebAssembly Modules

```bash
cd mmix
./build-browser.sh
```

This generates:
- `mmixal.js` / `mmixal.wasm` - Assembler for browser
- `mmix.js` / `mmix.wasm` - Simulator for browser

### Build Documentation

```bash
cd mmix
./build-doc.sh
```

Generates PDF documentation from CWEB sources in `doc/`.

## Deployment

### Self-Hosting with Nginx

1. Copy files to your web server:
   ```bash
   rsync -avz . your-server:/var/www/mmix/
   ```

2. Configure nginx to serve the files:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       root /var/www/mmix;

       location /web/ {
           try_files $uri $uri/ =404;
       }

       location ~* \.(wasm)$ {
           types { application/wasm wasm; }
       }
   }
   ```

3. Access at `http://your-domain.com/web/`

### Static Hosting (GitHub Pages, Netlify, etc.)

Simply upload the entire directory - no server-side processing required!

## License & Attribution

This project uses Donald E. Knuth's MMIXware from *The Art of Computer Programming*.

Per Knuth's license, the source code cannot be modified directly. All
modifications are made through CWEB change files (`.ch` files), which patch the
original sources during compilation.

- **Original CWEB sources**: Copyright © Donald E. Knuth
- **Change files and web interface**: See LICENSE

## Resources

- [MMIX Home Page](https://mmix.cs.hm.edu/)
- [The Art of Computer Programming](https://www-cs-faculty.stanford.edu/~knuth/taocp.html)
- [MMIX Documentation](https://mmix.cs.hm.edu/doc/fasc1.pdf)
- [PyScript](https://pyscript.net/)
- [Emscripten](https://emscripten.org/)

## Contributing

Contributions welcome! Please remember:
- Use CWEB change files (`.ch`) for source modifications of the CWEB code
- Test both native and WebAssembly builds
- Follow the TAOCP aesthetic for web interface changes

---

*"The best programs are written so that computing machines can perform them quickly and so that human beings can understand them clearly." — Donald E. Knuth*
