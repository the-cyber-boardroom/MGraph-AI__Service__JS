from typing                                                          import Optional, Dict, List
from fastapi                                                         import HTTPException
from pydantic                                                        import BaseModel, Field
from osbot_fast_api.api.routes.Fast_API__Routes                      import Fast_API__Routes
from osbot_utils.decorators.methods.cache_on_self                    import cache_on_self
from mgraph_ai_service_js.service.deno.Deno__JS__Execution           import DENO__VERSION__COMPATIBLE_WITH_LAMBDA
from mgraph_ai_service_js.service.deno.Deno__JS__Module__Execution   import Deno__JS__Module__Execution
from mgraph_ai_service_js.service.deno.Deno__JS__Module__Execution   import JS__Module__Execution__Config
from mgraph_ai_service_js.service.deno.Deno__JS__Module__Execution   import JS__Module__Execution__Request
from mgraph_ai_service_js.service.deno.Deno__JS__Module__Execution   import DEFAULT_ALLOWED_IMPORT_HOSTS


# API Schema Models (simplified to match the new model)
class Schema__Module__Config(BaseModel):
    """API schema for module execution configuration"""
    max_execution_time_ms : int                      = Field(5000, ge=100, le=60000, description="Max execution time in milliseconds")
    max_memory_mb        : int                      = Field(256, ge=16, le=2048, description="Max memory in MB")
    max_output_size      : int                      = Field(1048576, ge=1024, le=10485760, description="Max output size in bytes")
    capture_stderr       : bool                     = Field(False, description="Include stderr in output")
    allow_url_imports    : bool                     = Field(True, description="Allow URL imports")
    allowed_import_hosts : Optional[List[str]]      = Field(None, description="Whitelist of import hosts")
    cache_imports        : bool                     = Field(True, description="Use Deno's cache for imports")
    # File system permissions (optional)
    allow_read           : Optional[List[str]]      = Field(None, description="Paths allowed for reading")
    allow_write          : Optional[List[str]]      = Field(None, description="Paths allowed for writing")


class Schema__Module__Execute__Request(BaseModel):
    """API request schema for module-enabled JavaScript execution"""
    code       : str                                = Field(..., description="JavaScript/TypeScript code to execute", min_length=1, max_length=1048576)
    config     : Optional[Schema__Module__Config]   = Field(None, description="Execution configuration")


class Schema__Module__Execute__Response(BaseModel):
    """API response schema for module execution"""
    success            : bool                      = Field(..., description="Execution succeeded")
    output             : Optional[str]             = Field(None, description="Standard output")
    error              : Optional[str]             = Field(None, description="Error output")
    execution_time_ms  : int                       = Field(..., description="Execution duration in milliseconds")
    truncated          : bool                      = Field(False, description="Output was truncated")
    deno_version       : str                       = Field(..., description="Deno runtime version")


class Schema__Module__Info__Response(BaseModel):
    """API response schema for module execution info"""
    default_allowed_hosts: List[str]               = Field(..., description="Default allowed import hosts")
    features            : Dict[str, bool]          = Field(..., description="Feature availability")
    examples            : Dict[str, str]           = Field(..., description="Example code snippets")


TAG__ROUTES_JS_MODULE = 'js-module'
ROUTES_PATHS__JS_MODULE = [f'/{TAG__ROUTES_JS_MODULE}/execute',
                           f'/{TAG__ROUTES_JS_MODULE}/info'   ,
                           f'/{TAG__ROUTES_JS_MODULE}/health' ]


class Routes__JS__Module__Execute(Fast_API__Routes):
    """FastAPI routes for JavaScript module execution service"""
    tag                    : str                        = TAG__ROUTES_JS_MODULE
    deno_module_executor   : Deno__JS__Module__Execution

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.deno_module_executor as _:
            _.setup()
            _.install()

    @cache_on_self
    def setup_executor(self) -> Deno__JS__Module__Execution:                      # Initialize module executor
        """Initialize and cache the Deno module executor"""
        executor = Deno__JS__Module__Execution()
        executor.setup()
        return executor

    def execute(self, request: Schema__Module__Execute__Request                   # Execute JavaScript with modules
               ) -> Schema__Module__Execute__Response:
        """
Execute JavaScript/TypeScript code with ES module support

Features:
- Direct ES module imports from any HTTPS source
- NPM packages via CDN (esm.sh, Skypack, jsDelivr, unpkg)
- TypeScript support (automatic)
- Top-level await
- Deno standard library access

Example with URL import:
```javascript
{
  "code": "import _ from 'https://esm.sh/lodash@4.17.21'; const result = _.chunk([1,2,3,4], 2);console.log(JSON.stringify(result));",
  "config": {
    "max_execution_time_ms": 5000,
    "max_memory_mb": 256,
    "max_output_size": 1048576,
    "capture_stderr": true,
    "allow_url_imports": false,
    "allowed_import_hosts": [
      "esm.sh"
    ],
    "cache_imports": true,
    "allow_read": [],
    "allow_write": []
  }
}
```

Example with Deno std library:
```javascript
import { assertEquals } from 'https://deno.land/std@0.208.0/testing/asserts.ts';
assertEquals(1 + 1, 2);
console.log('Test passed!');
```

Example with TypeScript:
```typescript
interface User {
    name: string;
    age: number;
}
const users: User[] = [{name: 'Alice', age: 30}];
console.log(users[0].name);
```
        """
        try:
            # Get or create executor
            if not self.deno_module_executor:
                self.deno_module_executor = self.setup_executor()

            # Convert API schema to Type_Safe models
            config = None
            if request.config:
                # Create permissions for file system if specified
                from mgraph_ai_service_js.service.deno.Deno__JS__Execution import JS__Execution__Permissions

                permissions = JS__Execution__Permissions()

                # Add file system permissions if specified
                if request.config.allow_read:
                    permissions.allow_read = request.config.allow_read
                if request.config.allow_write:
                    permissions.allow_write = request.config.allow_write

                config = JS__Module__Execution__Config(
                    max_execution_time_ms = request.config.max_execution_time_ms,
                    max_memory_mb        = request.config.max_memory_mb,
                    max_output_size      = request.config.max_output_size,
                    permissions          = permissions,
                    capture_stderr       = request.config.capture_stderr,
                    allow_url_imports    = request.config.allow_url_imports,
                    allowed_import_hosts = request.config.allowed_import_hosts,
                    cache_imports        = request.config.cache_imports
                )

            # Create execution request
            exec_request = JS__Module__Execution__Request(
                code   = request.code,
                config = config
            )

            # Execute the code with module support
            result = self.deno_module_executor.execute_module_js(exec_request)

            # Convert result to API response
            return Schema__Module__Execute__Response(
                success           = result.success,
                output            = result.output,
                error             = result.error,
                execution_time_ms = result.execution_time_ms,
                truncated         = result.truncated,
                deno_version      = result.deno_version
            )

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Module execution failed: {str(e)}")

    def info(self) -> Schema__Module__Info__Response:                             # Get module system info
        """
        Get information about the module execution system

        Returns details about allowed import hosts, available features,
        and example code snippets.
        """
        return Schema__Module__Info__Response(
            default_allowed_hosts = DEFAULT_ALLOWED_IMPORT_HOSTS,
            features            = {
                "url_imports"     : True,   # Direct HTTPS imports
                "npm_packages"    : True,   # Via CDN URLs
                "typescript"      : True,   # Native TypeScript support
                "top_level_await" : True,   # Async at module level
                "deno_std"        : True,   # Access to Deno standard library
                "file_system"     : True,   # With proper permissions
                "jsx"             : False,  # Requires .jsx/.tsx extension (not implemented)
            },
            examples = {
                "lodash_import": """import _ from 'https://esm.sh/lodash@4.17.21';
const result = _.chunk([1, 2, 3, 4], 2);
console.log(JSON.stringify(result));""",

                "deno_std": """import { delay } from 'https://deno.land/std@0.208.0/async/delay.ts';
console.log('Starting...');
await delay(100);
console.log('Done after 100ms');""",

                "typescript": """interface Point {
    x: number;
    y: number;
}
const point: Point = { x: 10, y: 20 };
console.log(`Point: (${point.x}, ${point.y})`);""",

                "multiple_imports": """import _ from 'https://esm.sh/lodash@4.17.21';
import { format } from 'https://deno.land/std@0.208.0/datetime/format.ts';

const numbers = _.sum([1, 2, 3, 4, 5]);
const date = format(new Date(), 'yyyy-MM-dd');
console.log(`Sum: ${numbers}, Date: ${date}`);""",

                "file_output": """// Requires allow_write permission for /tmp
const data = { result: 'success', timestamp: Date.now() };
await Deno.writeTextFile('/tmp/output.json', JSON.stringify(data));
console.log('Data written to /tmp/output.json');"""
            }
        )

    def health(self) -> dict:                                                     # Health check with module test
        """Check if the module execution service is healthy"""
        try:
            # Get or create executor
            if not self.deno_module_executor:
                self.deno_module_executor = self.setup_executor()

            # Try a simple module import execution
            test_request = JS__Module__Execution__Request(
                code = """
                    import { chunk } from 'https://cdn.skypack.dev/lodash@4';
                    const result = chunk([1, 2, 3, 4], 2);
                    console.log(JSON.stringify(result));
                """,
                config = JS__Module__Execution__Config(
                    max_execution_time_ms = 5000,
                    allow_url_imports    = True
                )
            )

            result = self.deno_module_executor.execute_module_js(test_request)

            if result.success and "[[1,2],[3,4]]" in result.output:
                return {
                    "status"          : "healthy",
                    "service"         : "js-module-execution",
                    "runtime"         : "deno",
                    "version"         : f"v{DENO__VERSION__COMPATIBLE_WITH_LAMBDA}",
                    "module_support"  : True
                }
            else:
                return {
                    "status"          : "degraded",
                    "service"         : "js-module-execution",
                    "runtime"         : "deno",
                    "message"         : "Module import check failed",
                    "module_support"  : False
                }

        except Exception as e:
            return {
                "status"          : "unhealthy",
                "service"         : "js-module-execution",
                "error"           : str(e),
                "module_support"  : False
            }

    def setup_routes(self):                                                       # Configure FastAPI routes
        self.add_route_post(self.execute)
        self.add_route_get (self.info)
        self.add_route_get (self.health)