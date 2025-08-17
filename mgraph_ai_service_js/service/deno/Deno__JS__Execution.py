from pathlib                                                    import Path
from typing                                                     import Optional, Dict, Any, List
from osbot_utils.decorators.methods.cache_on_self               import cache_on_self
from osbot_utils.testing.Temp_File                              import Temp_File
from osbot_utils.type_safe.Type_Safe                            import Type_Safe
from osbot_utils.type_safe.type_safe_core.decorators.type_safe  import type_safe
from osbot_utils.type_safe.validators.Type_Safe__Validator      import Validate
from osbot_utils.type_safe.validators.Validator__Max            import Validator__Max
from osbot_utils.type_safe.validators.Validator__Min            import Validator__Min
from osbot_utils.utils.Files                                    import path_combine, current_temp_folder, create_folder
from osbot_utils.utils.Files                                    import file_exists, file_not_exists
from osbot_utils.utils.Http                                     import GET_bytes_to_file
from osbot_utils.utils.Process                                  import exec_process
from osbot_utils.utils.Zip                                      import unzip_file
from osbot_utils.utils.Json                                     import json_dumps
import platform
import os
from os import chmod

from mgraph_ai_service_js.schemas.Safe_Str__Javascript import Safe_Str__Javascript

# Configuration constants
DENO__VERSION__COMPATIBLE_WITH_LAMBDA = '2.3.1' #'2.0.0' #'1.46.3' #'1.40.5'
DENO__VERSION__LATEST                 = '2.4.0'
FOLDER_NAME__DENO                     = 'deno-js'
FILE__NAME__DENO                      = 'deno'
VERSION__DENO                         = os.getenv('DENO_VERSION', f'v{DENO__VERSION__COMPATIBLE_WITH_LAMBDA}')
URL__GITHUB__DENO__RELEASES_DOWNLOAD  = "https://github.com/denoland/deno/releases/download/"
MAX_EXECUTION_TIME_MS                 = 30000  # 30 seconds default
MAX_MEMORY_MB                         = 512    # 512MB default
MAX_OUTPUT_SIZE                       = 1048576 # 1MB default


# Deno binary checksums for verification (update these with actual values)
DENO_CHECKSUMS = {
    "v2.4.0": {
        "linux-x86_64" : "sha256:...",  # TODO: Add actual checksums
        "darwin-arm64" : "sha256:...",
        "darwin-x86_64": "sha256:..."
    }
}


class JS__Execution__Permissions(Type_Safe):
    """Deno permission configuration for sandboxed execution"""
    allow_read       : Optional[List[str]] = None                                 # Paths allowed for reading
    allow_write      : Optional[List[str]] = None                                 # Paths allowed for writing
    allow_net        : Optional[List[str]] = None                                 # Network hosts allowed
    allow_env        : Optional[List[str]] = None                                 # Environment variables allowed
    allow_run        : Optional[List[str]] = None                                 # Subprocesses allowed
    allow_sys        : Optional[List[str]] = None                                 # System info allowed
    allow_ffi        : bool                = False                                # Foreign Function Interface
    allow_hrtime     : bool                = False                                # High resolution time
    prompt           : bool                = False                                # Prompt for permissions


class JS__Execution__Config(Type_Safe):
    """Configuration for JavaScript execution"""
    max_execution_time_ms : Validate[int, Validator__Min(100 ), Validator__Max(60000)]  = 5000          # Max execution time (100ms - 60s)
    max_memory_mb         : Validate[int, Validator__Min(16  ), Validator__Max(2048)]    = 256           # Max memory (16MB - 2GB)
    max_output_size       : Validate[int, Validator__Min(1024), Validator__Max(10485760)] = 1048576    # Max output (1KB - 10MB)
    permissions           : JS__Execution__Permissions                            # Permission configuration
    capture_stderr        : bool                                  = False         # Include stderr in output
    json_output          : bool                                   = False         # Expect JSON output


class JS__Execution__Request(Type_Safe):
    """Request model for JavaScript execution"""
    code                : Safe_Str__Javascript                                                # JavaScript code to execute
    config              : Optional[JS__Execution__Config]        = None          # Execution configuration
    input_data          : Optional[Dict[str, Any]]              = None          # Data to pass to script


class JS__Execution__Result(Type_Safe):
    """Result model for JavaScript execution"""
    success             : bool                                                    # Execution succeeded
    output              : Optional[str]         = None          # Standard output
    error               : Optional[str]         = None          # Error output
    execution_time_ms   : int                   = 0              # Execution duration
    memory_used_mb      : Optional[float]       = None          # Memory usage (if available)
    truncated           : bool                  = False         # Output was truncated
    deno_version        : str                   = DENO__VERSION__COMPATIBLE_WITH_LAMBDA


class Deno__JS__Execution(Type_Safe):                           # Secure JavaScript execution service using Deno runtime

    def setup(self) -> 'Deno__JS__Execution':                                     # Initialize Deno runtime
        self.folder_path__deno_js()                                               # Ensure folder exists
        self.install()                                                            # Install Deno if needed
        return self

    @cache_on_self
    def folder_path__deno_js(self) -> Path:                                       # Get Deno installation folder
        deno_folder = path_combine(current_temp_folder(), FOLDER_NAME__DENO)
        create_folder(deno_folder)
        return Path(deno_folder)

    @cache_on_self
    def file_path__deno(self) -> Path:                                           # Get Deno executable path
        return Path(path_combine(str(self.folder_path__deno_js()), FILE__NAME__DENO))

    def file_path__deno_zip(self) -> Path:                                       # Get Deno zip path
        return Path(str(self.file_path__deno()) + '.zip')

    @type_safe
    def install(self) -> bool:                                                    # Download and install Deno
        deno_path = self.file_path__deno()

        if file_exists(str(deno_path)):
            return True

        system  = platform.system().lower()
        machine = platform.machine().lower()

        # DeterValidator__Mine download URL based on platform
        if system == "linux":
            platform_key = "linux-x86_64"
            url = f"{URL__GITHUB__DENO__RELEASES_DOWNLOAD}{VERSION__DENO}/deno-x86_64-unknown-linux-gnu.zip"
        elif system == "darwin":
            if "arm" in machine:
                platform_key = "darwin-arm64"
                url = f"{URL__GITHUB__DENO__RELEASES_DOWNLOAD}{VERSION__DENO}/deno-aarch64-apple-darwin.zip"
            else:
                platform_key = "darwin-x86_64"
                url = f"{URL__GITHUB__DENO__RELEASES_DOWNLOAD}{VERSION__DENO}/deno-x86_64-apple-darwin.zip"
        else:
            raise RuntimeError(f"Unsupported platform: {system}")

        zip_path = self.file_path__deno_zip()

        if file_not_exists(str(zip_path)):
            # Download zip file
            GET_bytes_to_file(url, str(zip_path))

            # TODO: Verify checksum when actual checksums are available
            # expected_checksum = DENO_CHECKSUMS.get(VERSION__DENO, {}).get(platform_key)
            # if expected_checksum:
            #     actual_checksum = file_sha256(str(zip_path))
            #     if actual_checksum != expected_checksum:
            #         file_delete(str(zip_path))
            #         raise SecurityError(f"Checksum mismatch for Deno binary")

            # Extract and set permissions
            unzip_file(str(zip_path), str(self.folder_path__deno_js()))
            chmod(str(deno_path), 0o755)

        return file_exists(str(deno_path))

    @type_safe
    def build_permission_flags(self, permissions: JS__Execution__Permissions      # Build Deno permission flags
                               ) -> List[str]:
        flags = []

        if permissions.allow_read:
            flags.append(f"--allow-read={','.join(permissions.allow_read)}")
        if permissions.allow_write:
            flags.append(f"--allow-write={','.join(permissions.allow_write)}")
        if permissions.allow_net:
            flags.append(f"--allow-net={','.join(permissions.allow_net)}")
        if permissions.allow_env:
            flags.append(f"--allow-env={','.join(permissions.allow_env)}")
        if permissions.allow_run:
            flags.append(f"--allow-run={','.join(permissions.allow_run)}")
        if permissions.allow_sys:
            flags.append(f"--allow-sys={','.join(permissions.allow_sys)}")
        if permissions.allow_ffi:
            flags.append("--allow-ffi")
        if permissions.allow_hrtime:
            flags.append("--allow-hrtime")
        if permissions.prompt:
            flags.append("--prompt")

        # If no permissions specified, run with no permissions (most secure)
        if not flags:
            flags.append("--no-prompt")

        return flags

    @type_safe
    def execute_js(self, request: JS__Execution__Request                          # Execute JavaScript code securely
                    ) -> JS__Execution__Result:

        # Use provided config or create default secure config
        config = request.config or JS__Execution__Config()

        # Create wrapper script that enforces limits and handles I/O
        wrapper_script = self._create_wrapper_script(request.code                ,
                                                     request.input_data          ,
                                                     config.max_execution_time_ms,
                                                     config.json_output          )

        # Write script to temporary file
        with Temp_File(contents=wrapper_script, extension='.js', return_file_path=True) as script_file:
            # Build command with security flags
            params = []
            params.extend(["run", "--quiet"])
            params.extend(self.build_permission_flags(config.permissions))
            params.append(f"--v8-flags=--max-old-space-size={config.max_memory_mb}")
            params.append(script_file)

            # Execute with timeout
            import time
            start_time = time.time()

            result = exec_process(str(self.file_path__deno())                    ,
                                 params                                          ,
                                 timeout=config.max_execution_time_ms / 1000.0  )

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Process results
            stdout = result.get('stdout', '').strip()
            stderr = result.get('stderr', '').strip()

            # Truncate output if needed
            truncated = False
            if len(stdout) > config.max_output_size:
                stdout = stdout[:config.max_output_size]
                truncated = True

            # DeterValidator__Mine success
            success = result.get('status') == 'ok' and not stderr

            # Build response
            output = stdout
            if config.capture_stderr and stderr:
                output = f"{output}\n--- STDERR ---\n{stderr}"

            return JS__Execution__Result(success           = success          ,
                                         output            = output           ,
                                         error             = stderr if stderr else None,
                                         execution_time_ms = execution_time_ms,
                                         truncated         = truncated        ,
                                         deno_version      = DENO__VERSION__COMPATIBLE_WITH_LAMBDA)

    def _create_wrapper_script(self, user_code          : str  ,                  # Create sandboxed wrapper script
                                     input_data         : Optional[Dict[str, Any]],
                                     max_execution_time : int  ,
                                     json_output        : bool
                               ) -> str:

        # Prepare input data
        input_json = json_dumps(input_data) if input_data else '{}'

    def _create_wrapper_script(self, user_code          : str  ,                  # Create sandboxed wrapper script
                                     input_data         : Optional[Dict[str, Any]],
                                     max_execution_time : int  ,
                                     json_output        : bool
                               ) -> str:

        # Prepare input data
        input_json = json_dumps(input_data) if input_data else '{}'

        # todo: move this JS code into a separate JS file and write tests for it
        wrapper = f"""\
// Execution wrapper with timeout and resource limits
const maxExecutionTime = {max_execution_time};
const inputData = {input_json};
const jsonOutput = {str(json_output).lower()};

// Set execution timeout
const timeoutId = setTimeout(() => {{
    console.error("Execution timeout exceeded");
    Deno.exit(1);
}}, maxExecutionTime);

// User code execution
(async () => {{
    try {{
        // Make input data available
        globalThis.INPUT = inputData;
        
        // Execute user code (wrapped in async context)
        const result = await (async function() {{
            {user_code}
        }})();
        
        // Output result
        if (jsonOutput && result !== undefined) {{
            console.log(JSON.stringify(result));
        }} else if (result !== undefined) {{
            console.log(result);
        }}
        
        clearTimeout(timeoutId);
    }} catch (error) {{
        clearTimeout(timeoutId);
        console.error(`Execution error: ${{error.message}}`);
        Deno.exit(1);
    }}
}})();
    """
        return wrapper

    @type_safe
    def validate_js_syntax(self, code: str                                        # Validate JavaScript syntax
                           ) -> tuple[bool, Optional[str]]:
        """Validate JavaScript syntax without executing"""

        # Use Deno's check functionality
        with Temp_File(contents=code, extension='.js', return_file_path=True) as script_file:
            result = exec_process(str(self.file_path__deno())     ,
                                 ["check", "--quiet", script_file])
            stderr = result.get('stderr', '').strip()

            if result.get('status') == 'ok' and not stderr:
                return True, None
            else:
                return False, stderr

    # def cleanup(self) -> bool:                                                    # Clean up Deno installation
    #     """Remove Deno binary and temporary files"""
    #     import shutil
    #     deno_folder = self.folder_path__deno_js()
    #     if file_exists(str(deno_folder)):
    #         shutil.rmtree(str(deno_folder))
    #         return True
    #     return False