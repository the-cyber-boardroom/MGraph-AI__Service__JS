from typing                                                     import Optional, Dict, List
from osbot_utils.testing.Temp_File                              import Temp_File
from osbot_utils.utils.Process                                  import exec_process
from mgraph_ai_service_js.service.deno.Deno__JS__Execution      import Deno__JS__Execution, DENO__VERSION__COMPATIBLE_WITH_LAMBDA
from mgraph_ai_service_js.service.deno.Deno__JS__Execution      import JS__Execution__Config
from mgraph_ai_service_js.service.deno.Deno__JS__Execution      import JS__Execution__Request
from mgraph_ai_service_js.service.deno.Deno__JS__Execution      import JS__Execution__Result


# Supported CDN providers for npm packages
CDN_PROVIDERS = {
    'esm.sh'     : 'https://esm.sh',           # Recommended for Deno
    'skypack'    : 'https://cdn.skypack.dev',  # Good ESM support
    'jsdelivr'   : 'https://cdn.jsdelivr.net', # Fast and reliable
    'unpkg'      : 'https://unpkg.com',        # Popular but needs ESM packages
    'deno.land'  : 'https://deno.land'         # Deno's official modules
}

# Default allowed CDN hosts for imports
DEFAULT_ALLOWED_IMPORT_HOSTS = [
    'esm.sh',
    'cdn.skypack.dev',
    'cdn.jsdelivr.net',
    'unpkg.com',
    'deno.land'
]


class JS__Module__Execution__Config(JS__Execution__Config):
    """Extended configuration for JavaScript module execution"""
    allow_url_imports   : bool                           = True          # Allow URL imports
    allowed_import_hosts: Optional[List[str]]            = None          # Whitelist of import hosts
    cache_imports       : bool                           = True          # Use Deno's cache for imports


class JS__Module__Execution__Request(JS__Execution__Request):             # Extended request model for JavaScript module execution"""
    config       : Optional[JS__Module__Execution__Config] = None         # Module execution configuration


class Deno__JS__Module__Execution(Deno__JS__Execution):
    """Extended JavaScript execution service with module/import support"""

    def build_module_permission_flags(self, config: JS__Module__Execution__Config,
                                        imports: Optional[Dict[str, str]] = None
                                 ) -> List[str]:
        # Start with parent's permission flags
        flags = self.build_permission_flags(config.permissions)

        # Add import permissions for remote modules if needed
        if config.allow_url_imports:
            allowed_hosts = config.allowed_import_hosts or DEFAULT_ALLOWED_IMPORT_HOSTS

            # Add --allow-import flag for remote module imports
            if allowed_hosts:
                # For Deno 2.x, we need --allow-import flag
                import_hosts = ','.join(allowed_hosts)
                flags.append(f"--allow-import={import_hosts}")

            # Also keep --allow-net for any network requests the code might make
            net_permissions = []

            # Add hosts from existing permissions
            if config.permissions and config.permissions.allow_net:
                net_permissions.extend(config.permissions.allow_net)

            # Add import hosts to net permissions too
            net_permissions.extend(allowed_hosts)

            # Remove duplicates and rebuild flag
            if net_permissions:
                unique_hosts = list(set(net_permissions))
                # Remove any existing --allow-net flags
                flags = [f for f in flags if not f.startswith('--allow-net')]
                flags.append(f"--allow-net={','.join(unique_hosts)}")

        # Add cache control flags
        if not config.cache_imports:
            flags.append('--reload')  # Force reload of remote modules

        return flags


    def execute_module_js(self, request: JS__Module__Execution__Request) -> JS__Execution__Result:
        config = request.config or JS__Module__Execution__Config()

        # Just use the code as provided
        code_to_execute = request.code

        # Write code to temp file and execute directly
        with Temp_File(contents=code_to_execute, extension='.ts', return_file_path=True) as script_file:
            params = ["run", "--quiet"]
            params.extend(self.build_module_permission_flags(config))
            params.append(f"--v8-flags=--max-old-space-size={config.max_memory_mb}")
            params.append(script_file)

            import time
            import os
            start_time = time.time()

            # Set Deno cache directory to /tmp for Lambda compatibility
            env = os.environ.copy()
            env['DENO_DIR'] = '/tmp/deno_cache'

            result = exec_process(
                self.file_path__deno(),
                params,
                timeout=config.max_execution_time_ms / 1000.0,
                env=env  # Pass the environment with DENO_DIR set
            )

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Process results
            stdout = result.get('stdout', '').strip()
            stderr = result.get('stderr', '').strip()

            success = result.get('status') == 'ok' and not stderr

            return JS__Execution__Result(
                success           = success,
                output            = stdout,
                error             = stderr if stderr else None,
                execution_time_ms = execution_time_ms,
                truncated         = len(stdout) > config.max_output_size,
                deno_version      = f'v{DENO__VERSION__COMPATIBLE_WITH_LAMBDA}'
        )