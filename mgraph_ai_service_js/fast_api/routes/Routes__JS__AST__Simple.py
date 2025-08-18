import json
from typing                                                        import Dict, Any
from fastapi                                                       import HTTPException
from pydantic                                                      import BaseModel, Field
from osbot_fast_api.api.routes.Fast_API__Routes                    import Fast_API__Routes
from osbot_utils.utils.Http                                        import GET
from mgraph_ai_service_js.service.js_ast.JS__AST__Roundtrip        import JS__AST__Roundtrip
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas  import JS__AST__Parser__Options
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas  import JS__AST__Generator__Options
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas  import JS__AST__Parse__Request
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas  import JS__AST__Generate__Request
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas  import Safe_Str__Javascript


# Simple request/response models for easy Swagger UI usage
class Schema__Simple__JS_to_AST__Request(BaseModel):
    """Simple request with just JavaScript code as a string"""
    code: str = Field(
        ...,
        description="JavaScript code to parse into AST",
        example="const greeting = 'Hello, World!';\nconsole.log(greeting);"
    )


class Schema__Simple__JS_to_AST__Response(BaseModel):
    """Simple response with the AST as a dictionary"""
    ast: Dict[str, Any] = Field(
        ...,
        description="ESTree AST representation"
    )


class Schema__Simple__AST_to_JS__Request(BaseModel):
    """Simple request with AST as a dictionary"""
    ast: Dict[str, Any] = Field(
        ...,
        description="ESTree AST to generate JavaScript from",
        example={
            "type": "Program",
            "body": [{
                "type": "VariableDeclaration",
                "declarations": [{
                    "type": "VariableDeclarator",
                    "id": {"type": "Identifier", "name": "greeting"},
                    "init": {"type": "Literal", "value": "Hello, World!"}
                }],
                "kind": "const"
            }],
            "sourceType": "module"
        }
    )


class Schema__Simple__AST_to_JS__Response(BaseModel):
    """Simple response with generated JavaScript code"""
    code: str = Field(
        ...,
        description="Generated JavaScript code"
    )


# class Schema__Simple__URL_to_AST__Request(BaseModel):
#     """Simple request with URL to fetch JavaScript from"""
#     url: str = Field(
#         ...,
#         description="URL of JavaScript file to parse into AST",
#         example="https://cdnjs.cloudflare.com/ajax/libs/lodash.js/4.17.21/lodash.min.js"
#     )

class Schema__Simple__JSON_to_AST__Request(BaseModel):
    """Simple request with raw JSON to convert to AST"""
    json_data: str = Field(
        ...,
        description="Raw JSON data to convert to JavaScript AST (paste directly, no escaping needed)",
        example='{"name": "John", "age": 30, "items": [1, 2, 3], "active": true}'
    )


class Schema__Simple__JSON_to_AST__Response(BaseModel):
    """Response with AST representation of the JSON data"""
    ast: Dict[str, Any] = Field(
        ...,
        description="ESTree AST representation of the JSON as JavaScript"
    )
    original_json: Dict[str, Any] = Field(
        ...,
        description="The parsed JSON data for reference"
    )


class Schema__Simple__URL_to_AST__Response(BaseModel):
    """Response with AST and metadata from URL"""
    ast: Dict[str, Any] = Field(
        ...,
        description="ESTree AST representation"
    )
    url: str = Field(
        ...,
        description="Original URL"
    )
    size: int = Field(
        ...,
        description="Size of fetched JavaScript in bytes"
    )


TAG__ROUTES_JS_AST_SIMPLE   = 'js-ast-simple'
ROUTES_PATHS__JS_AST_SIMPLE = [f'/{TAG__ROUTES_JS_AST_SIMPLE}/js-to-ast',
                               f'/{TAG__ROUTES_JS_AST_SIMPLE}/ast-to-js',
                               f'/{TAG__ROUTES_JS_AST_SIMPLE}/url-to-ast',
                               f'/{TAG__ROUTES_JS_AST_SIMPLE}/json-to-ast']


class Routes__JS__AST__Simple(Fast_API__Routes):
    """Simple JavaScript AST conversion endpoints for easy copy-paste usage"""
    tag         : str                = TAG__ROUTES_JS_AST_SIMPLE
    ast_service : JS__AST__Roundtrip

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ast_service = JS__AST__Roundtrip()

    def js_to_ast(self, request: Schema__Simple__JS_to_AST__Request
                 ) -> Schema__Simple__JS_to_AST__Response:
        """
        Convert JavaScript code to AST

        Simple endpoint that takes JavaScript code as a string and returns the ESTree AST.
        Perfect for copy-paste usage in Swagger UI.

        Example JavaScript inputs:
        - `const x = 42;`
        - `function greet(name) { return 'Hello ' + name; }`
        - `const sum = (a, b) => a + b;`
        - `class Example { constructor() { this.value = 1; } }`

        The response will be an ESTree-compliant AST that can be copied and used
        in the ast-to-js endpoint or for AST analysis.
        """
        try:
            # Create the parse request with default options
            parse_request = JS__AST__Parse__Request(
                code    = Safe_Str__Javascript(request.code),
                options = JS__AST__Parser__Options()  # Use defaults
            )

            # Parse the code
            response = self.ast_service.parse_to_ast(parse_request)

            if not response.success:
                raise HTTPException(
                    status_code=400,
                    detail=f"Parse error: {response.error}"
                )

            return Schema__Simple__JS_to_AST__Response(ast=response.ast)

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    def ast_to_js(self, request: Schema__Simple__AST_to_JS__Request
                 ) -> Schema__Simple__AST_to_JS__Response:
        """
        Convert AST to JavaScript code

        Simple endpoint that takes an ESTree AST and returns formatted JavaScript code.
        Perfect for copy-paste usage in Swagger UI.

        Example AST input:
        ```json
        {
          "type": "Program",
          "body": [{
            "type": "ExpressionStatement",
            "expression": {
              "type": "CallExpression",
              "callee": {
                "type": "MemberExpression",
                "object": {"type": "Identifier", "name": "console"},
                "property": {"type": "Identifier", "name": "log"}
              },
              "arguments": [{"type": "Literal", "value": "Hello!"}]
            }
          }],
          "sourceType": "module"
        }
        ```

        The response will be formatted JavaScript code that can be copied and executed.
        """
        try:
            # Create the generate request with default options
            generate_request = JS__AST__Generate__Request(
                ast     = request.ast,
                options = JS__AST__Generator__Options()  # Use defaults
            )

            # Generate the code
            response = self.ast_service.generate_from_ast(generate_request)

            if not response.success:
                raise HTTPException(
                    status_code=400,
                    detail=f"Generation error: {response.error}"
                )

            return Schema__Simple__AST_to_JS__Response(code=str(response.code))

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    def url_to_ast(self, url: str = "https://cdnjs.cloudflare.com/ajax/libs/js-cookie/3.0.1/js.cookie.min.js") -> Schema__Simple__URL_to_AST__Response:
        """
        Fetch JavaScript from URL and convert to AST

        Simple endpoint that fetches JavaScript code from a URL and returns the ESTree AST.
        Perfect for analyzing external scripts, CDN libraries, or any publicly accessible JavaScript.

        Example URLs to try:
        - Small library: `https://cdnjs.cloudflare.com/ajax/libs/uuid/8.3.2/uuid.min.js`
        - jQuery: `https://code.jquery.com/jquery-3.6.0.min.js`
        - React: `https://unpkg.com/react@18/umd/react.production.min.js`
        - Lodash: `https://cdnjs.cloudflare.com/ajax/libs/lodash.js/4.17.21/lodash.min.js`

        Note: The URL must be publicly accessible (no authentication required).
        Large files may take longer to process.
        """
        try:
            # Validate URL format
            if not url.startswith(('http://', 'https://')):
                raise HTTPException(
                    status_code=400,
                    detail="URL must start with http:// or https://"
                )

            # Fetch the JavaScript content
            try:
                response = GET(url)
                if response is None or response == '':
                    raise HTTPException(
                        status_code=404,
                        detail=f"Could not fetch content from URL: {url}"
                    )

                # Check if content looks like JavaScript (basic validation)
                content_lower = response[:1000].lower()  # Check first 1KB
                if 'html' in content_lower and '<html' in content_lower:
                    raise HTTPException(
                        status_code=400,
                        detail="URL returned HTML content, not JavaScript"
                    )

            except Exception as e:
                if isinstance(e, HTTPException):
                    raise
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to fetch URL: {str(e)}"
                )

            # Get size before processing
            content_size = len(response.encode('utf-8'))

            # Check size limit (10MB)
            if content_size > 10 * 1024 * 1024:
                raise HTTPException(
                    status_code=413,
                    detail=f"JavaScript file too large: {content_size} bytes (max 10MB)"
                )

            # Parse the JavaScript code
            parse_request = JS__AST__Parse__Request(
                code    = Safe_Str__Javascript(response),
                options = JS__AST__Parser__Options()
            )

            parse_response = self.ast_service.parse_to_ast(parse_request)

            if not parse_response.success:
                raise HTTPException(
                    status_code=400,
                    detail=f"Parse error: {parse_response.error}"
                )

            return Schema__Simple__URL_to_AST__Response(
                ast  = parse_response.ast,
                url  = url,
                size = content_size
            )

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    def json_to_ast(self, json_data: dict
               ) -> dict:
        """
        Convert JSON data to JavaScript AST

        Takes raw JSON data and converts it to an AST representation of JavaScript code
        that would create that data structure.

        The JSON is converted to: `const data = <your_json>;`

        Example JSON inputs:
        - Simple object: `{"key": "value"}`
        - Array: `[1, 2, 3, 4, 5]`
        - Complex nested: `{"users": [{"name": "Alice", "age": 30}]}`
        - Mixed types: `{"string": "text", "number": 42, "boolean": true, "null": null}`

        Perfect for:
        - Analyzing data structure as code
        - Converting JSON configs to JavaScript
        - Understanding how data maps to AST
        """
        try:
            # Parse the JSON string
            # try:
            #     json_obj = json.loads(request.json_data)
            # except json.JSONDecodeError as e:
            #     raise HTTPException(
            #         status_code=400,
            #         detail=f"Invalid JSON: {str(e)}"
            #     )

            # Convert JSON to JavaScript code
            # Using json.dumps with ensure_ascii=False for better readability
            json_as_js_literal = json.dumps(json_data, ensure_ascii=False, indent=2)

            # Create JavaScript code that assigns this to a variable
            js_code = f"const data = {json_as_js_literal};"

            # Parse to AST
            parse_request = JS__AST__Parse__Request(
                code    = Safe_Str__Javascript(js_code),
                options = JS__AST__Parser__Options()
            )

            response = self.ast_service.parse_to_ast(parse_request)

            if not response.success:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to parse generated JavaScript: {response.error}"
                )
            return response.ast
            # return Schema__Simple__JSON_to_AST__Response(
            #     ast           = response.ast,
            #     original_json = json_data
            # )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error: {str(e)}"
            )

    def setup_routes(self):
        """Configure the FastAPI routes"""
        self.add_route_post(self.js_to_ast  )
        self.add_route_post(self.ast_to_js  )
        self.add_route_get (self.url_to_ast )
        self.add_route_post(self.json_to_ast)