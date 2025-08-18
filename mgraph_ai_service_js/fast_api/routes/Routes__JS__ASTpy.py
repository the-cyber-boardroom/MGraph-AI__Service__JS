from typing                                                        import Optional
from fastapi                                                       import HTTPException
from pydantic                                                      import BaseModel, Field
from osbot_fast_api.api.routes.Fast_API__Routes                    import Fast_API__Routes
from mgraph_ai_service_js.service.js_ast.JS__AST__Roundtrip        import JS__AST__Roundtrip
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas  import JS__AST__Parser__Options, Safe_Str__Code__Formatting
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas  import JS__AST__Generator__Options
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas  import JS__AST__Parse__Request
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas  import JS__AST__Generate__Request
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas  import JS__AST__Roundtrip__Request
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas  import Safe_Str__ECMAVersion
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas  import Safe_Str__SourceType
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas  import Safe_Str__Javascript


# Pydantic models for API
class Schema__AST__Parser__Options(BaseModel):                                       # API schema for parser options
    ecma_version : str  = Field("latest", description="ECMAScript version")
    source_type  : str  = Field("module", description="Source type: script or module")
    jsx          : bool = Field(False, description="Enable JSX parsing")
    typescript   : bool = Field(False, description="Enable TypeScript parsing")
    next         : bool = Field(True, description="Enable next-gen features")
    locations    : bool = Field(True, description="Include location info")
    ranges       : bool = Field(True, description="Include range info")
    raw          : bool = Field(True, description="Include raw strings")
    tokens       : bool = Field(False, description="Include token array")
    comments     : bool = Field(True, description="Preserve comments")
    tolerant     : bool = Field(False, description="Tolerate errors")


class Schema__AST__Generator__Options(BaseModel):                                    # API schema for generator options
    indent       : str  = Field("  ", description="Indentation string")
    line_end     : str  = Field("\n", description="Line ending")
    start_indent : str  = Field("", description="Initial indentation")
    comments     : bool = Field(True, description="Include comments")
    source_map   : bool = Field(False, description="Generate source map")


class Schema__AST__Parse__Request(BaseModel):                                        # API request for parsing
    code    : str                                     = Field(..., description="JavaScript code to parse", min_length=0, max_length=1048576)
    options : Optional[Schema__AST__Parser__Options] = Field(None, description="Parser options")


class Schema__AST__Generate__Request(BaseModel):                                     # API request for generation
    ast     : dict                                       = Field(..., description="ESTree AST object")
    options : Optional[Schema__AST__Generator__Options] = Field(None, description="Generator options")


class Schema__AST__Roundtrip__Request(BaseModel):                                    # API request for roundtrip
    code              : str                                     = Field(..., description="JavaScript code to validate", min_length=0, max_length=1048576)
    parser_options    : Optional[Schema__AST__Parser__Options]   = Field(None, description="Parser options")
    generator_options : Optional[Schema__AST__Generator__Options] = Field(None, description="Generator options")


TAG__ROUTES_JS_AST   = 'js-ast'
ROUTES_PATHS__JS_AST = [f'/{TAG__ROUTES_JS_AST}/parse'    ,
                        f'/{TAG__ROUTES_JS_AST}/generate' ,
                        f'/{TAG__ROUTES_JS_AST}/roundtrip',
                        f'/{TAG__ROUTES_JS_AST}/health'   ]


class Routes__JS__AST(Fast_API__Routes):                                             # FastAPI routes for JavaScript AST operations
    tag         : str                = TAG__ROUTES_JS_AST
    ast_service : JS__AST__Roundtrip

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ast_service = JS__AST__Roundtrip()

    def parse(self, request: Schema__AST__Parse__Request                             # Parse JavaScript code to ESTree AST
              ):
        """
        Parse JavaScript code to ESTree AST

        Example request:
        ```json
        {
          "code": "const x = 42; console.log(x);",
          "options": {
            "ecma_version": "latest",
            "source_type": "module",
            "locations": true,
            "ranges": true
          }
        }
        ```
        """
        try:
            options = None
            if request.options:
                options = JS__AST__Parser__Options(
                    ecma_version = Safe_Str__ECMAVersion(request.options.ecma_version),
                    source_type  = Safe_Str__SourceType(request.options.source_type)  ,
                    jsx          = request.options.jsx                                ,
                    typescript   = request.options.typescript                         ,
                    next         = request.options.next                               ,
                    locations    = request.options.locations                          ,
                    ranges       = request.options.ranges                             ,
                    raw          = request.options.raw                                ,
                    tokens       = request.options.tokens                             ,
                    comments     = request.options.comments                           ,
                    tolerant     = request.options.tolerant
                )

            service_request = JS__AST__Parse__Request(
                code    = Safe_Str__Javascript(request.code),
                options = options
            )

            response = self.ast_service.parse_to_ast(service_request)

            if not response.success:
                raise HTTPException(status_code=400, detail=str(response.error))

            return {
                "success"       : response.success      ,
                "ast"           : response.ast          ,
                "parse_time_ms" : response.parse_time_ms
            }

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Parse failed: {str(e)}")

    def generate(self, request: Schema__AST__Generate__Request                       # Generate JavaScript from ESTree AST
                 ):
        """
        Generate JavaScript code from ESTree AST

        Example request:
        ```json
        {
          "ast": {
            "type": "Program",
            "body": [{
              "type": "VariableDeclaration",
              "declarations": [{
                "type": "VariableDeclarator",
                "id": {"type": "Identifier", "name": "x"},
                "init": {"type": "Literal", "value": 42}
              }],
              "kind": "const"
            }]
          },
          "options": {
            "indent": "  ",
            "comments": true
          }
        }
        ```
        """
        try:
            options = None
            if request.options:
                options = JS__AST__Generator__Options(indent       = Safe_Str__Code__Formatting(request.options.indent      ),
                                                      line_end     = Safe_Str__Code__Formatting(request.options.line_end    ),
                                                      start_indent = Safe_Str__Code__Formatting(request.options.start_indent),
                                                      comments     = request.options.comments,
                                                      source_map   = request.options.source_map)

            service_request = JS__AST__Generate__Request(
                ast     = request.ast,
                options = options
            )

            response = self.ast_service.generate_from_ast(service_request)

            if not response.success:
                raise HTTPException(status_code=400, detail=str(response.error))

            return {
                "success"            : response.success           ,
                "code"               : str(response.code)         ,
                "generation_time_ms" : response.generation_time_ms
            }

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

    def roundtrip(self, request: Schema__AST__Roundtrip__Request                     # Validate roundtrip: parse -> generate -> parse
                  ):
        """
        Validate roundtrip: parse -> generate -> parse

        Ensures that code maintains semantic equivalence through the transformation.

        Example request:
        ```json
        {
          "code": "function hello(name) { return `Hello, ${name}!`; }",
          "parser_options": {
            "ecma_version": "latest",
            "source_type": "module"
          },
          "generator_options": {
            "indent": "  "
          }
        }
        ```
        """
        try:
            parser_options = None
            if request.parser_options:
                parser_options = JS__AST__Parser__Options(
                    ecma_version = Safe_Str__ECMAVersion(request.parser_options.ecma_version),
                    source_type  = Safe_Str__SourceType(request.parser_options.source_type)  ,
                    jsx          = request.parser_options.jsx                                ,
                    typescript   = request.parser_options.typescript                         ,
                    next         = request.parser_options.next                               ,
                    locations    = request.parser_options.locations                          ,
                    ranges       = request.parser_options.ranges                             ,
                    raw          = request.parser_options.raw                                ,
                    tokens       = request.parser_options.tokens                             ,
                    comments     = request.parser_options.comments                           ,
                    tolerant     = request.parser_options.tolerant
                )

            generator_options = None
            if request.generator_options:
                generator_options = JS__AST__Generator__Options(
                    indent       = Safe_Str__Code__Formatting(request.generator_options.indent)      ,
                    line_end     = Safe_Str__Code__Formatting(request.generator_options.line_end)    ,
                    start_indent = Safe_Str__Code__Formatting(request.generator_options.start_indent),
                    comments     = request.generator_options.comments              ,
                    source_map   = request.generator_options.source_map
                )

            service_request = JS__AST__Roundtrip__Request(
                code              = Safe_Str__Javascript(request.code),
                parser_options    = parser_options                    ,
                generator_options = generator_options
            )

            response = self.ast_service.validate_roundtrip(service_request)

            if not response.success:
                raise HTTPException(status_code=400, detail=str(response.error))

            return {
                "success"          : response.success                     ,
                "is_valid"         : response.is_valid                    ,
                "original_ast"     : response.original_ast                ,
                "generated_code"   : str(response.generated_code) if response.generated_code else None,
                "regenerated_ast"  : response.regenerated_ast             ,
                "parse_time_ms"    : response.parse_time_ms               ,
                "generate_time_ms" : response.generate_time_ms            ,
                "total_time_ms"    : response.total_time_ms
            }

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Roundtrip validation failed: {str(e)}")

    def health(self) -> dict:                                                        # Check if the AST service is healthy

        try:
            test_request = JS__AST__Parse__Request(
                code    = Safe_Str__Javascript("const x = 42;"),
                options = JS__AST__Parser__Options()
            )

            result = self.ast_service.parse_to_ast(test_request)

            if result.success and result.ast:
                return {
                    "status"    : "healthy"  ,
                    "service"   : "js-ast"   ,
                    "parser"    : "meriyah"  ,
                    "generator" : "astring"
                }
            else:
                return {
                    "status"  : "degraded"                     ,
                    "service" : "js-ast"                       ,
                    "message" : "AST operations check failed"
                }

        except Exception as e:
            return {
                "status"  : "unhealthy",
                "service" : "js-ast"   ,
                "error"   : str(e)
            }

    def setup_routes(self):                                                          # Configure FastAPI routes
        self.add_route_post(self.parse    )
        self.add_route_post(self.generate )
        self.add_route_post(self.roundtrip)
        self.add_route_get (self.health   )