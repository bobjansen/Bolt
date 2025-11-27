import js
import json
import asyncio
from pyodide.ffi import create_proxy, to_js
from js import console, document

class MMIXPlayground:
    """Main class for the MMIX Interactive Playground"""

    def __init__(self):
        self.mmixal_factory = None
        self.mmix_factory = None
        self.object_code = None
        self.examples = {}

        console.log("Initializing MMIX Playground...")
        self.load_examples()
        self.setup_ui()
        asyncio.ensure_future(self.load_modules_async())

    def load_examples(self):
        """Load example programs from embedded JSON"""
        try:
            examples_script = document.getElementById("example-programs")
            if examples_script:
                self.examples = json.loads(examples_script.textContent)
                console.log(f"Loaded {len(self.examples)} example programs")
        except Exception as e:
            console.error(f"Error loading examples: {e}")

    def setup_ui(self):
        """Set up UI event handlers"""
        # Assemble button
        assemble_btn = document.getElementById("assemble-btn")
        assemble_btn.onclick = create_proxy(self.on_assemble_click)

        # Run button
        run_btn = document.getElementById("run-btn")
        run_btn.onclick = create_proxy(self.on_run_click)

        # Clear button
        clear_btn = document.getElementById("clear-btn")
        clear_btn.onclick = create_proxy(self.on_clear_click)

        # Example selector
        examples_select = document.getElementById("examples")
        examples_select.onchange = create_proxy(self.on_example_change)

        # Tab switching
        tabs = document.querySelectorAll(".tab")
        for tab in tabs:
            tab.onclick = create_proxy(self.on_tab_click)

        console.log("UI event handlers set up")

    async def load_modules_async(self):
        """Load WASM module factories asynchronously"""
        try:
            self.show_status("Loading MMIX modules...")

            # Get base URL for loading modules
            base_url = js.window.location.origin

            # Load mmixal factory
            console.log("Loading mmixal factory...")
            mmixal_url = f"{base_url}/mmix/mmixal.js"
            console.log(f"Loading from: {mmixal_url}")
            mmixal_module_ns = await js.eval(f"import('{mmixal_url}')")
            self.mmixal_factory = mmixal_module_ns.default
            console.log("mmixal factory loaded")

            # Load mmix factory
            console.log("Loading mmix factory...")
            mmix_url = f"{base_url}/mmix/mmix.js"
            console.log(f"Loading from: {mmix_url}")
            mmix_module_ns = await js.eval(f"import('{mmix_url}')")
            self.mmix_factory = mmix_module_ns.default
            console.log("mmix factory loaded")

            self.show_status("Modules loaded successfully!", "success")
            self.show_error("Modules loaded and ready! Select an example or write your own MMIX code.")

            # Enable assemble button
            document.getElementById("assemble-btn").disabled = False

        except Exception as e:
            error_msg = f"Error loading modules: {e}"
            console.error(error_msg)
            self.show_error(error_msg)
            self.show_status("Failed to load modules", "error")

    async def assemble(self, source_code):
        """Assemble MMIX code and return results"""
        try:
            # Create output array for capturing print
            mmixal_output = []

            # Create a fresh module instance
            console.log("Creating fresh mmixal module instance...")
            mmixal_config = to_js({
                "print": create_proxy(lambda text: mmixal_output.append(str(text))),
                "printErr": create_proxy(lambda text: mmixal_output.append(str(text))),
                "noInitialRun": True
            })
            mmixal_module = await self.mmixal_factory(mmixal_config)
            console.log(f"mmixal module instance created, type: {type(mmixal_module)}")

            # Create virtual files in MEMFS
            console.log(f"Writing source code ({len(source_code)} bytes) to /input.mms")
            console.log(f"Source code preview: {source_code[:100] if len(source_code) > 100 else source_code}")
            mmixal_module.FS.writeFile("/input.mms", source_code)

            # Verify the file was written
            input_stat = mmixal_module.FS.stat("/input.mms")
            console.log(f"input.mms written, size: {input_stat.size}")

            # Call mmixal with arguments
            # mmixal -l /output.lst -o /output.mmo /input.mms
            console.log("Calling mmixal...")
            args = to_js([
                "-l", "/output.lst",
                "-o", "/output.mmo",
                "/input.mms"
            ])
            exit_code = mmixal_module.callMain(args)

            console.log(f"mmixal exit code: {exit_code}")
            console.log(f"mmixal output captured: {mmixal_output}")

            # Try to force close any open file descriptors
            try:
                # Get list of open streams
                console.log("Checking for open streams...")
                streams = mmixal_module.FS.streams
                console.log(f"Number of streams: {len(streams) if streams else 0}")
                if streams:
                    for stream in streams:
                        if stream and hasattr(stream, 'fd') and stream.fd > 2:  # Skip stdin/stdout/stderr
                            console.log(f"Closing stream fd={stream.fd}")
                            try:
                                mmixal_module.FS.close(stream)
                            except:
                                pass
            except Exception as e:
                console.error(f"Error closing streams: {e}")

            # List files in root directory and check their stats
            try:
                files = mmixal_module.FS.readdir("/")
                console.log(f"Files in /: {files}")

                # Check file stats for output files
                for filename in ["/output.lst", "/output.mmo"]:
                    try:
                        stat = mmixal_module.FS.stat(filename)
                        console.log(f"Stat for {filename}: size={stat.size}")
                    except Exception as e:
                        console.error(f"Error stat'ing {filename}: {e}")
            except Exception as e:
                console.error(f"Error listing files: {e}")

            # Read outputs
            listing = ""
            object_code = None

            try:
                listing_data = mmixal_module.FS.readFile("/output.lst", to_js({"encoding": "utf8"}))
                # Check if we got a string or bytes
                if hasattr(listing_data, 'length'):
                    # It's a Uint8Array, decode it
                    console.log(f"Got Uint8Array with length {listing_data.length}")
                    # Convert to Python string
                    listing = bytes(listing_data).decode('utf-8')
                else:
                    listing = str(listing_data)
                console.log(f"Read listing, length: {len(listing)} chars")
                console.log(f"Listing preview: {listing[:200] if len(listing) > 200 else listing}")
            except Exception as e:
                console.error(f"Error reading listing: {e}")

            try:
                # Read as Uint8Array - don't convert to Python bytes
                object_code = mmixal_module.FS.readFile("/output.mmo")
                console.log(f"Read object code, length: {object_code.length if hasattr(object_code, 'length') else len(object_code)} bytes")
            except Exception as e:
                console.error(f"Error reading object code: {e}")

            # Get any console output
            console_output = "\n".join(mmixal_output)

            # Check if object code is valid (not None and has length > 0)
            has_object_code = object_code is not None
            if has_object_code and hasattr(object_code, 'length'):
                has_object_code = object_code.length > 0
            elif has_object_code:
                has_object_code = len(object_code) > 0

            console.log(f"Assembly complete - exit_code: {exit_code}, has_object_code: {has_object_code}")

            return {
                "success": exit_code == 0 and has_object_code,
                "listing": listing,
                "object_code": object_code,
                "exit_code": exit_code,
                "console_output": console_output
            }
        except Exception as e:
            console.error(f"Assembly error: {e}")
            import traceback
            console.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e),
                "console_output": ""
            }

    async def run_simulation(self, object_code):
        """Run MMIX simulator on assembled code"""
        try:
            # Create output array for capturing print
            mmix_output = []

            # Create a fresh module instance
            console.log("Creating fresh mmix module instance...")

            # Create output callback using JavaScript directly to avoid conversion issues
            output_captured = []

            # Create config object using JavaScript
            console.log("Setting up output capture using JavaScript eval...")
            js.eval("""
                window.mmixOutputCapture = [];
                window.mmixOutCallback = function(text) {
                    window.mmixOutputCapture.push(text);
                };
            """)

            mmix_config = js.eval("""({
                print: function(text) { window.mmixOutCallback(text); },
                printErr: function(text) { window.mmixOutCallback(text); },
                noInitialRun: true
            })""")

            mmix_module = await self.mmix_factory(mmix_config)
            console.log(f"mmix module instance created")

            # Write object code to MEMFS
            mmix_module.FS.writeFile("/program.mmo", object_code)

            # Redirect stdout to a file instead of trying to intercept writes
            console.log("Redirecting stdout to file...")

            # Run simulator with output redirected: mmix /program.mmo > /output.txt
            # We'll use the shell-like redirection by running with -q flag and capturing
            console.log("Running mmix simulator...")
            args = to_js(["-q", "/program.mmo"])  # -q for quiet mode (suppresses extra output)
            console.log(f"Calling mmix with args: {args}")

            # Run the simulation
            exit_code = mmix_module.callMain(args)

            console.log(f"mmix exit code: {exit_code}")

            # Try to force close any open file descriptors
            try:
                console.log("Checking for open streams in mmix...")
                streams = mmix_module.FS.streams
                console.log(f"Number of streams: {len(streams) if streams else 0}")
                if streams:
                    for stream in streams:
                        if stream and hasattr(stream, 'fd') and stream.fd > 2:
                            console.log(f"Closing stream fd={stream.fd}")
                            try:
                                mmix_module.FS.close(stream)
                            except:
                                pass
            except Exception as e:
                console.error(f"Error closing streams: {e}")

            # Get captured output from JavaScript
            captured = js.window.mmixOutputCapture
            console.log(f"Captured output array length: {len(captured)}")
            console.log(f"Captured output contents: {captured}")

            # Convert to Python list and join
            output_parts = []
            for i in range(len(captured)):
                output_parts.append(str(captured[i]))
            output = "".join(output_parts)

            if not output:
                output = "(Program completed with no output)"

            console.log(f"Final output: {output}")

            # Success if exit code is reasonable (0-15 are normal MMIX halt codes)
            # Exit code > 128 typically indicates an error
            is_success = exit_code >= 0 and exit_code < 128
            console.log(f"Simulation success: {is_success} (exit_code={exit_code})")

            return {
                "success": is_success,
                "output": output,
                "exit_code": exit_code
            }
        except Exception as e:
            console.error(f"Simulation error: {e}")
            import traceback
            console.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e),
                "output": ""
            }

    def on_assemble_click(self, event):
        """Handle assemble button click"""
        if not self.mmixal_factory:
            self.show_error("MMIX modules not loaded yet. Please wait...")
            return

        code = document.getElementById("code-editor").value
        if not code.strip():
            self.show_error("Please enter some MMIX code to assemble.")
            return

        # Launch async assembly
        asyncio.ensure_future(self._do_assemble(code))

    async def _do_assemble(self, code):
        """Async assembly handler"""
        self.show_status("Assembling...")

        # Clear previous outputs
        self.clear_output()

        # Assemble
        result = await self.assemble(code)

        if result["success"]:
            self.show_listing(result["listing"])
            self.object_code = result["object_code"]
            document.getElementById("run-btn").disabled = False
            self.show_status("Assembly successful!", "success")
            if result["console_output"]:
                self.show_error(f"Assembly output:\n{result['console_output']}")
        else:
            error_msg = result.get("error", "Assembly failed")
            if result.get("console_output"):
                error_msg = f"{error_msg}\n\n{result['console_output']}"
            self.show_error(error_msg)
            self.show_status("Assembly failed", "error")
            document.getElementById("run-btn").disabled = True

    def on_run_click(self, event):
        """Handle run button click"""
        if not self.mmix_factory:
            self.show_error("MMIX modules not loaded yet.")
            return

        if not self.object_code:
            self.show_error("Please assemble code first.")
            return

        # Launch async simulation
        asyncio.ensure_future(self._do_run())

    async def _do_run(self):
        """Async simulation handler"""
        self.show_status("Running simulation...")

        # Run simulation
        result = await self.run_simulation(self.object_code)
        console.log(f"Simulation result: {result}")

        if result["success"]:
            output_text = result["output"] or "(Program completed with no output)"
            console.log(f"Displaying output: {output_text}")
            self.show_output(output_text)
            self.show_status("Simulation completed!", "success")
            self.switch_tab("output")
        else:
            error_msg = result.get("error", "Simulation failed")
            if result.get("output"):
                error_msg = f"{error_msg}\n\n{result['output']}"
            self.show_error(error_msg)
            self.show_status("Simulation failed", "error")

    def on_clear_click(self, event):
        """Handle clear button click"""
        self.clear_output()
        self.show_status("Output cleared")

    def on_example_change(self, event):
        """Handle example selection change"""
        example_key = event.target.value
        if example_key and example_key in self.examples:
            example = self.examples[example_key]
            document.getElementById("code-editor").value = example["code"]
            self.clear_output()
            self.show_status(f"Loaded example: {example['name']}")
            document.getElementById("run-btn").disabled = True

    def on_tab_click(self, event):
        """Handle tab click"""
        tab_name = event.target.getAttribute("data-tab")
        self.switch_tab(tab_name)

    def switch_tab(self, tab_name):
        """Switch to a specific output tab"""
        # Update tab buttons
        tabs = document.querySelectorAll(".tab")
        for tab in tabs:
            if tab.getAttribute("data-tab") == tab_name:
                tab.classList.add("active")
            else:
                tab.classList.remove("active")

        # Update output panes
        panes = {
            "listing": document.getElementById("listing-output"),
            "output": document.getElementById("simulation-output"),
            "errors": document.getElementById("error-output")
        }

        for name, pane in panes.items():
            if name == tab_name:
                pane.classList.add("active")
            else:
                pane.classList.remove("active")

    def show_listing(self, listing):
        """Display assembly listing"""
        document.getElementById("listing-output").textContent = listing
        self.switch_tab("listing")

    def show_output(self, output):
        """Display simulation output"""
        document.getElementById("simulation-output").textContent = output

    def show_error(self, error):
        """Display error message"""
        document.getElementById("error-output").textContent = error

    def clear_output(self):
        """Clear all output panes"""
        document.getElementById("listing-output").textContent = ""
        document.getElementById("simulation-output").textContent = ""
        document.getElementById("error-output").textContent = ""

    def show_status(self, message, status_type="info"):
        """Show a status message (could be enhanced with a status bar)"""
        console.log(f"[{status_type}] {message}")

# Initialize the playground
console.log("Creating MMIXPlayground instance...")
playground = MMIXPlayground()
console.log("MMIXPlayground initialized")
