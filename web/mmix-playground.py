import js
import json
import asyncio
from pyodide.ffi import create_proxy, to_js
from js import console, document, localStorage, Blob, URL

class StorageManager:
    """Manages localStorage for persistent code and file storage"""

    def __init__(self):
        self.CURRENT_CODE_KEY = "mmix.currentCode"
        self.CURRENT_ARGS_KEY = "mmix.currentArgs"
        self.PROGRAMS_KEY = "mmix.programs"
        self.FILES_KEY = "mmix.uploadedFiles"

    def save_current_code(self, code):
        """Auto-save current code"""
        try:
            localStorage.setItem(self.CURRENT_CODE_KEY, code)
        except Exception as e:
            console.error(f"Error saving current code: {e}")

    def load_current_code(self):
        """Load auto-saved code"""
        try:
            code = localStorage.getItem(self.CURRENT_CODE_KEY)
            return code if code else ""
        except Exception as e:
            console.error(f"Error loading current code: {e}")
            return ""

    def save_current_args(self, args):
        """Auto-save current arguments"""
        try:
            localStorage.setItem(self.CURRENT_ARGS_KEY, args)
        except Exception as e:
            console.error(f"Error saving current args: {e}")

    def load_current_args(self):
        """Load auto-saved arguments"""
        try:
            args = localStorage.getItem(self.CURRENT_ARGS_KEY)
            return args if args else ""
        except Exception as e:
            console.error(f"Error loading current args: {e}")
            return ""

    def save_program(self, name, code):
        """Save a named program"""
        try:
            programs = self.get_programs()
            # Update if exists, otherwise add
            found = False
            for prog in programs:
                if prog["name"] == name:
                    prog["code"] = code
                    prog["timestamp"] = js.Date.now()
                    found = True
                    break
            if not found:
                programs.append({
                    "name": name,
                    "code": code,
                    "timestamp": js.Date.now()
                })
            localStorage.setItem(self.PROGRAMS_KEY, json.dumps(programs))
            return True
        except Exception as e:
            console.error(f"Error saving program: {e}")
            return False

    def get_programs(self):
        """Get all saved programs"""
        try:
            programs_json = localStorage.getItem(self.PROGRAMS_KEY)
            if programs_json:
                return json.loads(programs_json)
            return []
        except Exception as e:
            console.error(f"Error getting programs: {e}")
            return []

    def delete_program(self, name):
        """Delete a saved program"""
        try:
            programs = self.get_programs()
            programs = [p for p in programs if p["name"] != name]
            localStorage.setItem(self.PROGRAMS_KEY, json.dumps(programs))
            return True
        except Exception as e:
            console.error(f"Error deleting program: {e}")
            return False

    def save_uploaded_file(self, filename, content):
        """Save an uploaded file"""
        try:
            files = self.get_uploaded_files()
            # Update if exists, otherwise add
            found = False
            for f in files:
                if f["name"] == filename:
                    f["content"] = content
                    found = True
                    break
            if not found:
                files.append({"name": filename, "content": content})
            localStorage.setItem(self.FILES_KEY, json.dumps(files))
            return True
        except Exception as e:
            console.error(f"Error saving uploaded file: {e}")
            return False

    def get_uploaded_files(self):
        """Get all uploaded files"""
        try:
            files_json = localStorage.getItem(self.FILES_KEY)
            if files_json:
                return json.loads(files_json)
            return []
        except Exception as e:
            console.error(f"Error getting uploaded files: {e}")
            return []

    def delete_uploaded_file(self, filename):
        """Delete an uploaded file"""
        try:
            files = self.get_uploaded_files()
            files = [f for f in files if f["name"] != filename]
            localStorage.setItem(self.FILES_KEY, json.dumps(files))
            return True
        except Exception as e:
            console.error(f"Error deleting uploaded file: {e}")
            return False

class MMIXPlayground:
    """Main class for the MMIX Interactive Playground"""

    def __init__(self):
        self.mmixal_factory = None
        self.mmix_factory = None
        self.object_code = None
        self.examples = {}
        self.storage = StorageManager()

        console.log("Initializing MMIX Playground...")
        self.load_examples()
        self.setup_ui()
        self.restore_code()
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
        # Assemble & Run button
        assemble_run_btn = document.getElementById("assemble-run-btn")
        assemble_run_btn.onclick = create_proxy(self.on_assemble_run_click)

        # Assemble button
        assemble_btn = document.getElementById("assemble-btn")
        assemble_btn.onclick = create_proxy(self.on_assemble_click)

        # Run button
        run_btn = document.getElementById("run-btn")
        run_btn.onclick = create_proxy(self.on_run_click)

        # Tab switching
        tabs = document.querySelectorAll(".tab")
        for tab in tabs:
            tab.onclick = create_proxy(self.on_tab_click)

        # Keyboard shortcut: Ctrl-Enter to assemble & run
        code_editor = document.getElementById("code-editor")
        code_editor.onkeydown = create_proxy(self.on_editor_keydown)

        # Auto-save on code changes
        code_editor.oninput = create_proxy(self.on_code_change)

        # Files button
        document.getElementById("files-btn").onclick = create_proxy(self.on_files_click)
        document.getElementById("files-close-btn").onclick = create_proxy(self.on_modal_cancel)

        # Args modal
        document.getElementById("args-btn").onclick = create_proxy(self.on_edit_args_click)
        document.getElementById("edit-args-btn").onclick = create_proxy(self.on_edit_args_click)
        document.getElementById("args-done-btn").onclick = create_proxy(self.on_args_done)
        document.getElementById("args-clear-btn").onclick = create_proxy(self.on_args_clear)
        document.getElementById("args-assemble-run-btn").onclick = create_proxy(self.on_args_assemble_run)
        args_input = document.getElementById("args-input")
        args_input.oninput = create_proxy(self.on_args_change)

        # File tabs
        file_tabs = document.querySelectorAll(".file-tab")
        for tab in file_tabs:
            tab.onclick = create_proxy(self.on_file_tab_click)

        # Save/Import/Export buttons
        document.getElementById("save-confirm-btn").onclick = create_proxy(self.on_save_confirm)
        document.getElementById("import-btn").onclick = create_proxy(self.on_import_click)
        document.getElementById("export-btn").onclick = create_proxy(self.on_export_click)
        document.getElementById("import-file-input").onchange = create_proxy(self.on_import_file_selected)

        # Data file upload
        document.getElementById("upload-file-btn").onclick = create_proxy(self.on_upload_file_click)
        document.getElementById("upload-data-file-input").onchange = create_proxy(self.on_data_file_selected)

        console.log("UI event handlers set up")

    def restore_code(self):
        """Restore saved code from localStorage or load default example"""
        saved_code = self.storage.load_current_code()
        if saved_code:
            document.getElementById("code-editor").value = saved_code
            console.log("Restored code from localStorage")
        elif "hello" in self.examples:
            # Load hello example by default
            document.getElementById("code-editor").value = self.examples["hello"]["code"]
            console.log("Loaded default hello example")

        # Restore args
        saved_args = self.storage.load_current_args()
        if saved_args:
            document.getElementById("args-input").value = saved_args
            self.update_args_display()
            console.log("Restored args from localStorage")

    def on_code_change(self, event):
        """Handle code editor changes - auto-save"""
        code = document.getElementById("code-editor").value
        self.storage.save_current_code(code)

    def on_args_change(self, event):
        """Handle args input changes - auto-save and update display"""
        args = document.getElementById("args-input").value
        self.storage.save_current_args(args)
        self.update_args_display()

    def update_args_display(self):
        """Update the args display row visibility and content"""
        args = document.getElementById("args-input").value.strip()
        args_display = document.getElementById("args-display")
        args_display_value = document.getElementById("args-display-value")

        if args:
            args_display_value.value = args
            args_display.style.display = "flex"
        else:
            args_display.style.display = "none"

    def on_edit_args_click(self, event):
        """Show args modal"""
        self.show_modal("args-modal")

    def on_args_done(self, event):
        """Close args modal"""
        self.hide_modal("args-modal")

    def on_args_clear(self, event):
        """Clear the args input"""
        args_input = document.getElementById("args-input")
        args_input.value = ""
        self.storage.save_current_args("")
        self.update_args_display()

    def on_args_assemble_run(self, event):
        """Close args modal and trigger assemble & run"""
        self.hide_modal("args-modal")
        self.on_assemble_run_click(event)

    def on_files_click(self, event):
        """Show files modal with all tabs"""
        self.populate_programs_list()
        self.populate_examples_list()
        self.populate_data_files_list()
        self.show_modal("files-modal")

    def on_file_tab_click(self, event):
        """Handle file tab switching"""
        tab_name = event.target.getAttribute("data-tab")

        # Update tabs
        tabs = document.querySelectorAll(".file-tab")
        for tab in tabs:
            if tab.getAttribute("data-tab") == tab_name:
                tab.classList.add("active")
            else:
                tab.classList.remove("active")

        # Update panes
        panes = {
            "programs": document.getElementById("programs-pane"),
            "examples": document.getElementById("examples-pane"),
            "data": document.getElementById("data-pane")
        }

        for name, pane in panes.items():
            if name == tab_name:
                pane.classList.add("active")
            else:
                pane.classList.remove("active")

    def on_save_confirm(self, event):
        """Save current code with specified name"""
        name = document.getElementById("save-name-input").value.strip()
        if not name:
            self.show_error("Please enter a program name")
            return

        code = document.getElementById("code-editor").value
        if self.storage.save_program(name, code):
            self.show_status(f"Saved program '{name}'", "success")
            document.getElementById("save-name-input").value = ""
            self.populate_programs_list()
        else:
            self.show_error("Failed to save program")

    def on_import_click(self, event):
        """Trigger file import"""
        document.getElementById("import-file-input").click()

    def on_export_click(self, event):
        """Export current code as .mms file"""
        code = document.getElementById("code-editor").value
        if not code.strip():
            self.show_error("No code to export")
            return

        # Create blob and download
        blob = Blob.new([code], to_js({"type": "text/plain"}))
        url = URL.createObjectURL(blob)

        # Create temporary download link
        link = document.createElement("a")
        link.href = url
        link.download = "program.mms"
        link.click()

        URL.revokeObjectURL(url)
        self.show_status("Exported program.mms", "success")

    def on_import_file_selected(self, event):
        """Handle imported file"""
        files = event.target.files
        if files.length == 0:
            return

        file = files.item(0)  # Use .item() for JsProxy arrays
        reader = js.FileReader.new()

        def on_load(e):
            code = e.target.result
            document.getElementById("code-editor").value = code
            self.storage.save_current_code(code)
            self.show_status(f"Imported {file.name}", "success")

        reader.onload = create_proxy(on_load)
        reader.readAsText(file)

    def on_upload_file_click(self, event):
        """Trigger data file upload"""
        document.getElementById("upload-data-file-input").click()

    def on_data_file_selected(self, event):
        """Handle uploaded data file"""
        files = event.target.files
        if files.length == 0:
            return

        file = files.item(0)  # Use .item() for JsProxy arrays
        reader = js.FileReader.new()

        def on_load(e):
            content = e.target.result
            if self.storage.save_uploaded_file(file.name, content):
                self.show_status(f"Uploaded {file.name}", "success")
                self.populate_data_files_list()
            else:
                self.show_error(f"Failed to upload {file.name}")

        reader.onload = create_proxy(on_load)
        reader.readAsText(file)


    def populate_programs_list(self):
        """Populate the programs list in load modal"""
        programs = self.storage.get_programs()
        list_div = document.getElementById("programs-list")

        if len(programs) == 0:
            list_div.innerHTML = "<p>No saved programs yet.</p>"
            return

        html_parts = []
        for prog in programs:
            name = prog["name"]
            display_name = f"{name}.mms"  # Show with extension
            html_parts.append(f'''
                <div class="program-item">
                    <span class="program-name">{display_name}</span>
                    <div class="program-actions">
                        <button class="btn btn-small" onclick="playground.load_program('{name}')">Load</button>
                        <button class="btn btn-small" onclick="playground.delete_program('{name}')">Delete</button>
                    </div>
                </div>
            ''')

        list_div.innerHTML = "".join(html_parts)

    def populate_examples_list(self):
        """Populate the examples list"""
        list_div = document.getElementById("examples-list")

        if len(self.examples) == 0:
            list_div.innerHTML = "<p>No examples available.</p>"
            return

        html_parts = []
        for key, example in self.examples.items():
            name = example["name"]
            html_parts.append(f'''
                <div class="program-item">
                    <span class="program-name">{name}</span>
                    <div class="program-actions">
                        <button class="btn btn-small" onclick="playground.load_example('{key}')">Load</button>
                    </div>
                </div>
            ''')

        list_div.innerHTML = "".join(html_parts)

    def populate_data_files_list(self):
        """Populate the uploaded data files list"""
        files = self.storage.get_uploaded_files()
        list_div = document.getElementById("data-files-list")

        if len(files) == 0:
            list_div.innerHTML = "<p>No uploaded files yet.</p>"
            return

        html_parts = []
        for f in files:
            name = f["name"]
            html_parts.append(f'''
                <div class="file-item">
                    <span class="file-name">{name}</span>
                    <div class="file-actions">
                        <button class="btn btn-small" onclick="playground.delete_file('{name}')">Delete</button>
                    </div>
                </div>
            ''')

        list_div.innerHTML = "".join(html_parts)

    def load_program(self, name):
        """Load a saved program (called from JavaScript)"""
        programs = self.storage.get_programs()
        for prog in programs:
            if prog["name"] == name:
                document.getElementById("code-editor").value = prog["code"]
                self.storage.save_current_code(prog["code"])
                self.hide_modal("files-modal")
                self.show_status(f"Loaded program '{name}'", "success")
                return

        self.show_error(f"Program '{name}' not found")

    def load_example(self, key):
        """Load an example program (called from JavaScript)"""
        if key in self.examples:
            document.getElementById("code-editor").value = self.examples[key]["code"]
            self.storage.save_current_code(self.examples[key]["code"])
            self.hide_modal("files-modal")
            self.show_status(f"Loaded example: {self.examples[key]['name']}", "success")
        else:
            self.show_error(f"Example '{key}' not found")

    def delete_program(self, name):
        """Delete a saved program (called from JavaScript)"""
        if self.storage.delete_program(name):
            self.populate_programs_list()
            self.show_status(f"Deleted program '{name}'", "success")
        else:
            self.show_error(f"Failed to delete program '{name}'")

    def delete_file(self, name):
        """Delete an uploaded file (called from JavaScript)"""
        if self.storage.delete_uploaded_file(name):
            self.populate_data_files_list()
            self.show_status(f"Deleted file '{name}'", "success")
        else:
            self.show_error(f"Failed to delete file '{name}'")

    def show_modal(self, modal_id):
        """Show a modal dialog"""
        modal = document.getElementById(modal_id)
        modal.classList.add("show")

    def hide_modal(self, modal_id):
        """Hide a modal dialog"""
        modal = document.getElementById(modal_id)
        modal.classList.remove("show")

    def on_modal_cancel(self, event):
        """Handle modal cancel - close all modals"""
        modals = document.querySelectorAll(".modal")
        for modal in modals:
            modal.classList.remove("show")

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
                    console.log('[mmixOutCallback] called with:', JSON.stringify(text), 'charCode:', text.charCodeAt(0));
                    // Since newlines aren't being passed through, add them after each call
                    window.mmixOutputCapture.push(text + '\\n');
                };
            """)

            mmix_config = js.eval("""({
                print: function(text) { window.mmixOutCallback(text); },
                printErr: function(text) { window.mmixOutCallback(text); },
                noInitialRun: true
            })""")

            mmix_module = await self.mmix_factory(mmix_config)
            console.log(f"mmix module instance created")

            # Write uploaded files to MEMFS so programs can access them
            uploaded_files = self.storage.get_uploaded_files()
            if len(uploaded_files) > 0:
                console.log(f"Writing {len(uploaded_files)} uploaded files to MEMFS...")
                for file_info in uploaded_files:
                    filename = file_info["name"]
                    content = file_info["content"]
                    mmix_module.FS.writeFile(f"/{filename}", content)
                    console.log(f"Wrote uploaded file: /{filename}")

            # Also write saved programs to MEMFS so they can be used as input
            saved_programs = self.storage.get_programs()
            if len(saved_programs) > 0:
                console.log(f"Writing {len(saved_programs)} saved programs to MEMFS...")
                for prog in saved_programs:
                    # Save with .mms extension
                    filename = f"{prog['name']}.mms"
                    content = prog["code"]
                    mmix_module.FS.writeFile(f"/{filename}", content)
                    console.log(f"Wrote program file: /{filename}")

            # Write object code to MEMFS
            mmix_module.FS.writeFile("/program.mmo", object_code)

            # Redirect stdout to a file instead of trying to intercept writes
            console.log("Redirecting stdout to file...")

            # Get user-provided arguments
            args_input = document.getElementById("args-input").value.strip()
            user_args = []
            if args_input:
                # Simple split on spaces - could be enhanced to handle quoted strings
                user_args = [arg for arg in args_input.split() if arg]
                console.log(f"User provided args: {user_args}")

            # Run simulator with output redirected: mmix /program.mmo > /output.txt
            # We'll use the shell-like redirection by running with -q flag and capturing
            console.log("Running mmix simulator...")
            # Build args: mmix -q /program.mmo [user_args]
            # Args must come AFTER the object file
            args_list = ["-q", "/program.mmo"] + user_args
            args = to_js(args_list)
            console.log(f"Calling mmix with args: {args_list}")

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
                part = str(captured[i])
                console.log(f"Output part {i}: {repr(part)}")
                output_parts.append(part)
            output = "".join(output_parts)
            console.log(f"Joined output: {repr(output)}")

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

    def on_assemble_run_click(self, event):
        """Handle assemble & run button click"""
        if not self.mmixal_factory or not self.mmix_factory:
            self.show_error("MMIX modules not loaded yet. Please wait...")
            return

        code = document.getElementById("code-editor").value
        if not code.strip():
            self.show_error("Please enter some MMIX code to assemble.")
            return

        # Launch async assemble & run
        asyncio.ensure_future(self._do_assemble_and_run(code))

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

    def on_editor_keydown(self, event):
        """Handle keydown events in code editor"""
        # Check for Ctrl-Enter (or Cmd-Enter on Mac)
        if (event.ctrlKey or event.metaKey) and event.key == "Enter":
            event.preventDefault()
            self.on_assemble_run_click(event)

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

    async def _do_assemble_and_run(self, code):
        """Async assemble and run handler"""
        self.show_status("Assembling...")

        # Switch to output tab immediately to prevent flash
        self.switch_tab("output")

        # Clear previous outputs
        self.clear_output()

        # Assemble
        result = await self.assemble(code)

        if not result["success"]:
            error_msg = result.get("error", "Assembly failed")
            if result.get("console_output"):
                error_msg = f"{error_msg}\n\n{result['console_output']}"
            self.show_error(error_msg)
            self.show_status("Assembly failed", "error")
            document.getElementById("run-btn").disabled = True
            self.switch_tab("errors")
            return

        # Assembly successful, populate listing but don't switch to it
        document.getElementById("listing-output").textContent = result["listing"]
        self.object_code = result["object_code"]
        document.getElementById("run-btn").disabled = False
        if result["console_output"]:
            self.show_error(f"Assembly output:\n{result['console_output']}")

        # Now run simulation
        self.show_status("Running simulation...")
        sim_result = await self.run_simulation(self.object_code)
        console.log(f"Simulation result: {sim_result}")

        if sim_result["success"]:
            output_text = sim_result["output"] or "(Program completed with no output)"
            console.log(f"Displaying output: {output_text}")
            self.show_output(output_text)
            self.show_status("Completed successfully!", "success")
            self.switch_tab("output")
        else:
            error_msg = sim_result.get("error", "Simulation failed")
            if sim_result.get("output"):
                error_msg = f"{error_msg}\n\n{sim_result['output']}"
            self.show_error(error_msg)
            self.show_status("Simulation failed", "error")
            self.switch_tab("errors")

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

# Expose to JavaScript for onclick handlers
js.window.playground = playground
