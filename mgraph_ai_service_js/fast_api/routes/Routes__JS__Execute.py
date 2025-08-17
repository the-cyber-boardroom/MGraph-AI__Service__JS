from typing                                                 import Optional, Dict, Any
from fastapi import HTTPException, FastAPI
from pydantic                                               import BaseModel, Field
from osbot_fast_api.api.routes.Fast_API__Routes             import Fast_API__Routes
from osbot_utils.decorators.methods.cache_on_self           import cache_on_self
from mgraph_ai_service_js.service.deno.Deno__JS__Execution  import Deno__JS__Execution
from mgraph_ai_service_js.service.deno.Deno__JS__Execution  import JS__Execution__Config
from mgraph_ai_service_js.service.deno.Deno__JS__Execution  import JS__Execution__Permissions
from mgraph_ai_service_js.service.deno.Deno__JS__Execution  import JS__Execution__Request
from mgraph_ai_service_js.service.deno.Deno__JS__Execution  import JS__Execution__Result

# API Schema Models (for FastAPI/Pydantic compatibility)
class Schema__JS__Permissions(BaseModel):
    """API schema for JavaScript execution permissions"""
    allow_read  : Optional[list[str]] = Field(None, description="Paths allowed for reading")
    allow_write : Optional[list[str]] = Field(None, description="Paths allowed for writing")
    allow_net   : Optional[list[str]] = Field(None, description="Network hosts allowed")
    allow_env   : Optional[list[str]] = Field(None, description="Environment variables allowed")
    allow_run   : Optional[list[str]] = Field(None, description="Subprocesses allowed")
    allow_sys   : Optional[list[str]] = Field(None, description="System info allowed")
    allow_ffi   : bool                = Field(False, description="Allow Foreign Function Interface")
    allow_hrtime: bool                = Field(False, description="Allow high resolution time")
    prompt      : bool                = Field(False, description="Prompt for permissions")


class Schema__JS__Config(BaseModel):
    """API schema for JavaScript execution configuration"""
    max_execution_time_ms : int                             = Field(5000, ge=100, le=60000, description="Max execution time in milliseconds")
    max_memory_mb        : int                             = Field(256, ge=16, le=2048, description="Max memory in MB")
    max_output_size      : int                             = Field(1048576, ge=1024, le=10485760, description="Max output size in bytes")
    permissions          : Optional[Schema__JS__Permissions] = Field(None, description="Permission configuration")
    capture_stderr       : bool                             = Field(False, description="Include stderr in output")
    json_output         : bool                             = Field(False, description="Expect JSON output")


class Schema__JS__Execute__Request(BaseModel):
    """API request schema for JavaScript execution"""
    code       : str                                = Field(..., description="JavaScript code to execute", min_length=1, max_length=1048576)
    config     : Optional[Schema__JS__Config]       = Field(None, description="Execution configuration")
    input_data : Optional[Dict[str, Any]]          = Field(None, description="Data to pass to script")


class Schema__JS__Execute__Response(BaseModel):
    """API response schema for JavaScript execution"""
    success           : bool           = Field(..., description="Execution succeeded")
    output            : Optional[str]  = Field(None, description="Standard output")
    error             : Optional[str]  = Field(None, description="Error output")
    execution_time_ms : int           = Field(..., description="Execution duration in milliseconds")
    memory_used_mb    : Optional[float] = Field(None, description="Memory usage in MB")
    truncated         : bool           = Field(False, description="Output was truncated")


class Schema__JS__Validate__Request(BaseModel):
    """API request schema for JavaScript validation"""
    code : str = Field(..., description="JavaScript code to validate", min_length=1, max_length=1048576)


class Schema__JS__Validate__Response(BaseModel):
    """API response schema for JavaScript validation"""
    valid : bool           = Field(..., description="Code is syntactically valid")
    error : Optional[str]  = Field(None, description="Validation error message")


TAG__ROUTES_JS_EXECUTE = 'js-execute'
ROUTES_PATHS__JS_EXECUTE = [f'/{TAG__ROUTES_JS_EXECUTE}/execute'  ,
                            f'/{TAG__ROUTES_JS_EXECUTE}/validate' ,
                            f'/{TAG__ROUTES_JS_EXECUTE}/health'   ]


class Routes__JS__Execute(Fast_API__Routes):        # FastAPI routes for JavaScript execution service
    tag              : str                   = TAG__ROUTES_JS_EXECUTE
    deno_js_executor : Deno__JS__Execution

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.deno_js_executor as _:
            _.setup()
            _.install()

    @cache_on_self
    def setup_executor(self) -> Deno__JS__Execution:                             # Initialize Deno executor
        """Initialize and cache the Deno executor"""
        executor = Deno__JS__Execution()
        executor.setup()
        return executor

    def execute(self, request: Schema__JS__Execute__Request                      # Execute JavaScript code
               ) -> Schema__JS__Execute__Response:
        """Execute JavaScript code in a secure sandboxed environment"""

        try:
            # Get or create executor
            if not self.deno_js_executor:
                self.deno_js_executor = self.setup_executor()

            # Convert API schema to Type_Safe models
            permissions = None
            if request.config and request.config.permissions:
                permissions = JS__Execution__Permissions(
                    allow_read   = request.config.permissions.allow_read  ,
                    allow_write  = request.config.permissions.allow_write ,
                    allow_net    = request.config.permissions.allow_net   ,
                    allow_env    = request.config.permissions.allow_env   ,
                    allow_run    = request.config.permissions.allow_run   ,
                    allow_sys    = request.config.permissions.allow_sys   ,
                    allow_ffi    = request.config.permissions.allow_ffi   ,
                    allow_hrtime = request.config.permissions.allow_hrtime,
                    prompt       = request.config.permissions.prompt
                )

            config = None
            if request.config:
                config = JS__Execution__Config(
                    max_execution_time_ms = request.config.max_execution_time_ms,
                    max_memory_mb        = request.config.max_memory_mb        ,
                    max_output_size      = request.config.max_output_size      ,
                    permissions          = permissions                         ,
                    capture_stderr       = request.config.capture_stderr       ,
                    json_output         = request.config.json_output
                )

            # Create execution request
            exec_request = JS__Execution__Request(
                code       = request.code      ,
                config     = config            ,
                input_data = request.input_data
            )

            # Execute the code
            result = self.deno_js_executor.execute_js(exec_request)

            # Convert result to API response
            return Schema__JS__Execute__Response(
                success           = result.success          ,
                output            = result.output           ,
                error             = result.error            ,
                execution_time_ms = result.execution_time_ms,
                memory_used_mb    = result.memory_used_mb   ,
                truncated         = result.truncated
            )

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")

    def validate(self, request: Schema__JS__Validate__Request                    # Validate JavaScript syntax
                ) -> Schema__JS__Validate__Response:
        """Validate JavaScript code syntax without executing it"""

        try:
            # Get or create executor
            if not self.deno_js_executor:
                self.deno_js_executor = self.setup_executor()

            # Validate the code
            is_valid, error_message = self.deno_js_executor.validate_js_syntax(request.code)

            return Schema__JS__Validate__Response(
                valid = is_valid     ,
                error = error_message
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

    def health(self) -> dict:                                                    # Health check endpoint
        """Check if the JavaScript execution service is healthy"""

        try:
            # Get or create executor
            if not self.deno_js_executor:
                self.deno_js_executor = self.setup_executor()

            # Try a simple execution to verify Deno is working
            test_request = JS__Execution__Request(
                code   = "40 + 2",
                config = JS__Execution__Config(max_execution_time_ms=1000)
            )

            result = self.deno_js_executor.execute_js(test_request)

            if result.success and result.output and "42" in result.output:
                return {
                    "status"  : "healthy"       ,
                    "service" : "js-execution"  ,
                    "runtime" : "deno"          ,
                    "version" : "v2.4.0"
                }
            else:
                return {
                    "status"  : "degraded"      ,
                    "service" : "js-execution"  ,
                    "runtime" : "deno"          ,
                    "message" : "Runtime check failed"
                }

        except Exception as e:
            return {
                "status"  : "unhealthy"     ,
                "service" : "js-execution"  ,
                "error"   : str(e)
            }

    def setup_routes(self):                                                       # Configure FastAPI routes
        self.add_route_post(self.execute )
        self.add_route_post(self.validate)
        self.add_route_get (self.health  )