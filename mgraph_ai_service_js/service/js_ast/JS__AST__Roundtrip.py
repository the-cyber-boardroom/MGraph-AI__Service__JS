import json
import time
from typing                                                                 import Optional, Dict, Any
from osbot_utils.type_safe.Type_Safe                                        import Type_Safe
from osbot_utils.type_safe.primitives.safe_uint.Safe_UInt                   import Safe_UInt
from mgraph_ai_service_js.service.deno.Deno__JS__Module__Execution          import Deno__JS__Module__Execution
from mgraph_ai_service_js.service.deno.Deno__JS__Module__Execution          import JS__Module__Execution__Config
from mgraph_ai_service_js.service.deno.Deno__JS__Module__Execution          import JS__Module__Execution__Request
from mgraph_ai_service_js.service.deno.Deno__JS__Execution                  import JS__Execution__Permissions
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas           import JS__AST__Parser__Options
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas           import JS__AST__Generator__Options
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas           import JS__AST__Parse__Request
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas           import JS__AST__Parse__Response
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas           import JS__AST__Generate__Request
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas           import JS__AST__Generate__Response
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas           import JS__AST__Roundtrip__Request
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas           import JS__AST__Roundtrip__Response
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas           import JS__AST__Location
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas           import Safe_Str__Javascript
from osbot_utils.type_safe.primitives.safe_str.Safe_Str                     import Safe_Str
from osbot_utils.type_safe.primitives.safe_int.Safe_Int                     import Safe_Int


MERIYAH_VERSION = '4.3.9'
ASTRING_VERSION = '1.8.6'


class JS__AST__Roundtrip(Type_Safe):                                                 # JavaScript AST parsing and generation service
    module_executor: Deno__JS__Module__Execution

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.module_executor as _:
            _.setup()
            _.install()

    def parse_to_ast(self, request: JS__AST__Parse__Request                          # Parse JavaScript to ESTree AST
                     ) -> JS__AST__Parse__Response:

        start_time = time.time()
        options    = request.options or JS__AST__Parser__Options()

        parse_script = self._create_parse_script(request.code, options)

        exec_request = JS__Module__Execution__Request(
            code   = parse_script,
            config = self._create_execution_config()
        )

        result        = self.module_executor.execute_module_js(exec_request)
        parse_time_ms = Safe_Int(int((time.time() - start_time) * 1000))

        if result.success:
            try:
                parsed_result = json.loads(result.output)
                if parsed_result.get('success'):
                    return JS__AST__Parse__Response(
                        success       = True                         ,
                        ast           = parsed_result.get('ast')     ,
                        parse_time_ms = parse_time_ms
                    )
                else:
                    return JS__AST__Parse__Response(
                        success        = False                             ,
                        error          = Safe_Str(parsed_result.get('error')),
                        error_location = self._parse_error_location(parsed_result.get('location')),
                        parse_time_ms  = parse_time_ms
                    )
            except json.JSONDecodeError as e:
                return JS__AST__Parse__Response(
                    success       = False                                           ,
                    error         = Safe_Str(f"Failed to decode parser output: {e}"),
                    parse_time_ms = parse_time_ms
                )
        else:
            return JS__AST__Parse__Response(
                success       = False                                        ,
                error         = Safe_Str(result.error or "Parser execution failed"),
                parse_time_ms = parse_time_ms
            )

    def generate_from_ast(self, request: JS__AST__Generate__Request                  # Generate JavaScript from AST
                          ) -> JS__AST__Generate__Response:

        start_time = time.time()
        options    = request.options or JS__AST__Generator__Options()

        generate_script = self._create_generate_script(request.ast, options)

        exec_request = JS__Module__Execution__Request(
            code   = generate_script,
            config = self._create_execution_config()
        )

        result             = self.module_executor.execute_module_js(exec_request)
        generation_time_ms = Safe_Int(int((time.time() - start_time) * 1000))

        if result.success:
            try:
                generated_result = json.loads(result.output)
                if generated_result.get('success'):
                    return JS__AST__Generate__Response(
                        success            = True                                             ,
                        code               = Safe_Str__Javascript(generated_result.get('code')),
                        generation_time_ms = generation_time_ms
                    )
                else:
                    return JS__AST__Generate__Response(
                        success            = False                               ,
                        error              = Safe_Str(generated_result.get('error')),
                        generation_time_ms = generation_time_ms
                    )
            except json.JSONDecodeError as e:
                return JS__AST__Generate__Response(
                    success            = False                                            ,
                    error              = Safe_Str(f"Failed to decode generator output: {e}"),
                    generation_time_ms = generation_time_ms
                )
        else:
            return JS__AST__Generate__Response(
                success            = False                                          ,
                error              = Safe_Str(result.error or "Generator execution failed"),
                generation_time_ms = generation_time_ms
            )

    def validate_roundtrip(self, request: JS__AST__Roundtrip__Request                # Validate parse -> generate -> parse
                           ) -> JS__AST__Roundtrip__Response:

        total_start = time.time()

        # Step 1: Parse original code
        parse_request = JS__AST__Parse__Request(
            code    = request.code           ,
            options = request.parser_options
        )
        parse_response = self.parse_to_ast(parse_request)

        if not parse_response.success:
            return JS__AST__Roundtrip__Response(
                success       = False                                              ,
                is_valid      = False                                              ,
                error         = Safe_Str(f"Initial parse failed: {parse_response.error}"),
                parse_time_ms = parse_response.parse_time_ms                       ,
                total_time_ms = Safe_Int(int((time.time() - total_start) * 1000))
            )

        original_ast = parse_response.ast

        # Step 2: Generate code from AST
        generate_request = JS__AST__Generate__Request(
            ast     = original_ast               ,
            options = request.generator_options
        )
        generate_response = self.generate_from_ast(generate_request)

        if not generate_response.success:
            return JS__AST__Roundtrip__Response(
                success          = False                                                ,
                is_valid         = False                                                ,
                original_ast     = original_ast                                         ,
                error            = Safe_Str(f"Generation failed: {generate_response.error}"),
                parse_time_ms    = parse_response.parse_time_ms                         ,
                generate_time_ms = generate_response.generation_time_ms                 ,
                total_time_ms    = Safe_Int(int((time.time() - total_start) * 1000))
            )

        generated_code = generate_response.code

        # Step 3: Re-parse generated code
        reparse_request = JS__AST__Parse__Request(
            code    = generated_code         ,
            options = request.parser_options
        )
        reparse_response = self.parse_to_ast(reparse_request)

        if not reparse_response.success:
            return JS__AST__Roundtrip__Response(
                success          = False                                                  ,
                is_valid         = False                                                  ,
                original_ast     = original_ast                                           ,
                generated_code   = generated_code                                         ,
                error            = Safe_Str(f"Re-parse failed: {reparse_response.error}") ,
                parse_time_ms    = Safe_Int(parse_response.parse_time_ms + reparse_response.parse_time_ms),
                generate_time_ms = generate_response.generation_time_ms                   ,
                total_time_ms    = Safe_Int(int((time.time() - total_start) * 1000))
            )

        regenerated_ast = reparse_response.ast
        is_valid        = self._compare_asts(original_ast, regenerated_ast)

        return JS__AST__Roundtrip__Response(
            success          = True                                                           ,
            is_valid         = is_valid                                                       ,
            original_ast     = original_ast                                                   ,
            generated_code   = generated_code                                                 ,
            regenerated_ast  = regenerated_ast                                                ,
            parse_time_ms    = Safe_Int(parse_response.parse_time_ms + reparse_response.parse_time_ms),
            generate_time_ms = generate_response.generation_time_ms                           ,
            total_time_ms    = Safe_Int(int((time.time() - total_start) * 1000))
        )

    def _create_execution_config(self) -> JS__Module__Execution__Config:             # Create standard execution config
        return JS__Module__Execution__Config(
            max_execution_time_ms = 10000                                  ,
            max_memory_mb         = 512                                    ,
            allow_url_imports     = True                                   ,
            allowed_import_hosts  = ["esm.sh"]                             ,
            cache_imports         = True                                   ,
            permissions           = JS__Execution__Permissions()
        )

    def _create_parse_script(self, code    : Safe_Str__Javascript,                   # Create Meriyah parser script
                                   options : JS__AST__Parser__Options
                             ) -> str:

        escaped_code   = json.dumps(str(code))
        parser_options = {
            "module"        : str(options.source_type) == "module",
            "next"          : options.next                        ,
            "loc"           : options.locations                   ,
            "ranges"        : options.ranges                      ,
            "raw"           : options.raw                         ,
            "globalReturn"  : str(options.source_type) == "script",
            "preserveParens": False                               ,
            "lexical"       : True
        }

        if options.jsx:
            parser_options["jsx"] = True

        return f"""
import {{ parse }} from 'https://esm.sh/meriyah@{MERIYAH_VERSION}';

const code = {escaped_code};
const options = {json.dumps(parser_options)};

try {{
    const ast = parse(code, options);
    const cleanAst = JSON.parse(JSON.stringify(ast));
    
    console.log(JSON.stringify({{
        success: true,
        ast: cleanAst
    }}));
}} catch (error) {{
    console.log(JSON.stringify({{
        success: false,
        error: error.message,
        location: error.loc || null
    }}));
}}
"""

    def _create_generate_script(self, ast     : Dict[str, Any],                      # Create Astring generator script
                                      options : JS__AST__Generator__Options
                                ) -> str:

        escaped_ast        = json.dumps(ast)
        generator_options  = {
            "indent"              : str(options.indent)     ,
            "lineEnd"             : str(options.line_end)   ,
            "startingIndentLevel" : 0
        }

        if options.comments:
            generator_options["comments"] = True

        return f"""
import {{ generate }} from 'https://esm.sh/astring@{ASTRING_VERSION}';

const ast = {escaped_ast};
const options = {json.dumps(generator_options)};

try {{
    const code = generate(ast, options);
    
    console.log(JSON.stringify({{
        success: true,
        code: code
    }}));
}} catch (error) {{
    console.log(JSON.stringify({{
        success: false,
        error: error.message
    }}));
}}
"""

    def _compare_asts(self, ast1: Dict[str, Any],                                    # Compare ASTs for semantic equivalence
                           ast2: Dict[str, Any]
                      ) -> bool:

        def normalize_ast(node):
            if isinstance(node, dict):
                normalized = {}
                for key, value in node.items():
                    if key not in ['loc', 'range', 'start', 'end', 'raw', 'leadingComments', 'trailingComments']:
                        normalized[key] = normalize_ast(value)
                return normalized
            elif isinstance(node, list):
                return [normalize_ast(item) for item in node]
            else:
                return node

        normalized_ast1 = normalize_ast(ast1)
        normalized_ast2 = normalize_ast(ast2)

        return json.dumps(normalized_ast1, sort_keys=True) == json.dumps(normalized_ast2, sort_keys=True)

    def _parse_error_location(self, location: Optional[Dict]                         # Parse error location from response
                          ) -> Optional[JS__AST__Location]:
        if not location:
            return None

        return JS__AST__Location(
            start_line   = Safe_UInt(location.get('start', {}).get('line', 0))  ,
            start_column = Safe_UInt(location.get('start', {}).get('column', 0)),
            end_line     = Safe_UInt(location.get('end', {}).get('line', 0))    ,
            end_column   = Safe_UInt(location.get('end', {}).get('column', 0))
        )