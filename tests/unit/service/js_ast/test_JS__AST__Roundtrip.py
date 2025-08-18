import re
import pytest
from unittest                                                      import TestCase
from mgraph_ai_service_js.service.js_ast.JS__AST__Roundtrip        import JS__AST__Roundtrip
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas  import JS__AST__Parser__Options, Safe_Str__Code__Formatting
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas  import JS__AST__Generator__Options
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas  import JS__AST__Parse__Request
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas  import JS__AST__Generate__Request
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas  import JS__AST__Roundtrip__Request
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas  import Safe_Str__Javascript
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas  import Safe_Str__ECMAVersion
from mgraph_ai_service_js.service.js_ast.schemas.JS__AST__Schemas  import Safe_Str__SourceType


class test_JS__AST__Roundtrip(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ast_service = JS__AST__Roundtrip()

    def test_01_parse_simple_code(self):                                             # Test parsing simple JavaScript
        request = JS__AST__Parse__Request(
            code    = Safe_Str__Javascript("const x = 42;"),
            options = JS__AST__Parser__Options()
        )

        response = self.ast_service.parse_to_ast(request)

        assert response.success                          is True
        assert response.ast                              is not None
        assert response.ast['type']                      == 'Program'
        assert len(response.ast['body'])                 == 1
        assert response.ast['body'][0]['type']           == 'VariableDeclaration'

    def test_02_parse_complex_code(self):                                            # Test parsing modern JavaScript
        code = Safe_Str__Javascript("""
        async function fetchData(url) {
            const response = await fetch(url);
            const { data, ...rest } = await response.json();
            return data?.items ?? [];
        }
        
        class DataProcessor {
            #privateField = 'secret';
            
            process(items) {
                return items.map(item => ({
                    ...item,
                    processed: true
                }));
            }
        }
        """)

        request = JS__AST__Parse__Request(
            code    = code,
            options = JS__AST__Parser__Options(
                ecma_version = Safe_Str__ECMAVersion("latest"),
                next         = True
            )
        )

        response = self.ast_service.parse_to_ast(request)

        assert response.success                is True
        assert response.ast                    is not None
        assert response.ast['type']            == 'Program'
        assert len(response.ast['body'])       == 2

    def test_03_generate_from_ast(self):                                             # Test generating code from AST
        ast = {
            "type"      : "Program"            ,
            "body"      : [{
                "type"        : "VariableDeclaration",
                "declarations": [{
                    "type" : "VariableDeclarator"        ,
                    "id"   : {"type": "Identifier", "name": "x"},
                    "init" : {"type": "Literal"   , "value": 42}
                }],
                "kind": "const"
            }],
            "sourceType": "module"
        }

        request = JS__AST__Generate__Request(ast     = ast,
                                             options = JS__AST__Generator__Options(indent=Safe_Str__Code__Formatting("  ")))

        response = self.ast_service.generate_from_ast(request)

        assert response.success  is True
        assert response.code     is not None
        assert response.code     == "const x = 42;\n"

    def test_04_roundtrip_simple(self):                                              # Test simple roundtrip validation
        js_code = """\
function add(a, b) {
  return a + b;
}
"""
        request = JS__AST__Roundtrip__Request(code              = Safe_Str__Javascript       (js_code),
                                              parser_options    = JS__AST__Parser__Options   (),
                                              generator_options = JS__AST__Generator__Options())

        response = self.ast_service.validate_roundtrip(request)

        assert response.success            is True
        assert response.is_valid           is True
        assert response.generated_code     is not None
        assert response.generated_code     == js_code                           # note: for this to work the code formatting of js_code must match the one created by the ast parser
        assert "function add"              in str(response.generated_code)

    def test_05_roundtrip_complex(self):                                             # Test complex roundtrip
        code = Safe_Str__Javascript("""
        const obj = {
            method: async () => {
                const [first, ...rest] = await getData();
                return { first, rest };
            }
        };
        """)

        request = JS__AST__Roundtrip__Request(
            code              = code                                             ,
            parser_options    = JS__AST__Parser__Options(
                ecma_version = Safe_Str__ECMAVersion("latest")
            ),
            generator_options = JS__AST__Generator__Options(
                indent = Safe_Str__Code__Formatting("    ")
            )
        )

        response = self.ast_service.validate_roundtrip(request)

        assert response.success  is True
        assert response.is_valid is True

    def test_06_parse_with_jsx(self):                                                # Test parsing JSX code
        code = Safe_Str__Javascript("""
        const element = <div className="container">
            <h1>Hello, {name}!</h1>
        </div>;
        """)

        request = JS__AST__Parse__Request(
            code    = code,
            options = JS__AST__Parser__Options(jsx=True)
        )

        response = self.ast_service.parse_to_ast(request)

        assert response.success is True
        assert response.ast     is not None

    def test_07_parse_error_handling(self):                                          # Test parsing invalid code
        request = JS__AST__Parse__Request(
            code    = Safe_Str__Javascript("const x = ;"),
            options = JS__AST__Parser__Options()
        )

        response = self.ast_service.parse_to_ast(request)

        assert response.success is False
        assert response.error   is not None
        assert response.error   == '_1_11___Unexpected_token_____'

    def test_08_generate_complex_ast(self):                                          # Test generating from complex AST
        js_code ="""\
class Example {
  constructor(name) {
    this.name = name;
  }
  greet() {
    return `Hello, ${this.name}!`;
  }
}
"""
        parse_request = JS__AST__Parse__Request(code    = js_code                   ,
                                                options = JS__AST__Parser__Options())

        parse_response = self.ast_service.parse_to_ast(parse_request)
        assert parse_response.success is True

        generate_request = JS__AST__Generate__Request(
            ast     = parse_response.ast,
            options = JS__AST__Generator__Options()
        )

        generate_response = self.ast_service.generate_from_ast(generate_request)


        assert generate_response.success is True
        assert generate_response.code == js_code

    def test_09_ast_normalization(self):                                             # Test AST comparison normalization
        code1 = Safe_Str__Javascript("const x=42;const y=100;")
        code2 = Safe_Str__Javascript("""
        const x = 42;
        const y = 100;
        """)

        request1 = JS__AST__Parse__Request(code=code1)
        request2 = JS__AST__Parse__Request(code=code2)

        response1 = self.ast_service.parse_to_ast(request1)
        response2 = self.ast_service.parse_to_ast(request2)

        assert response1.success is True
        assert response2.success is True

        assert self.ast_service._compare_asts(response1.ast,response2.ast) is True

    def test_10_performance(self):                                                   # Test performance with larger code
        lines = [f"const var_{i} = {i};" for i in range(100)]
        code  = Safe_Str__Javascript("// Large code sample\n" + "\n".join(lines))

        request = JS__AST__Parse__Request(
            code    = code,
            options = JS__AST__Parser__Options()
        )

        response = self.ast_service.parse_to_ast(request)

        assert response.success              is True
        assert response.parse_time_ms        < 150
        assert len(response.ast['body'])     >= 100

    def test_11_safe_str_types(self):                                                # Test Safe_Str type validation
        options = JS__AST__Parser__Options(
            ecma_version = Safe_Str__ECMAVersion("es2023"),
            source_type  = Safe_Str__SourceType ("script")
        )

        assert options.ecma_version == "es2023"
        assert options.source_type  == "script"

        # Test invalid values get sanitized
        error_message_1 = 'Value does not match required pattern: ^(latest|es\\d{4}|\\d{4})$'
        with pytest.raises(ValueError, match=re.escape(error_message_1)):
            Safe_Str__ECMAVersion("invalid!")

        error_message_1 = 'Value does not match required pattern: ^(module|script|unambiguous)$'
        with pytest.raises(ValueError, match=re.escape(error_message_1)):
            Safe_Str__SourceType("invalid!")


        # Test generator options
        gen_options = JS__AST__Generator__Options(indent   = Safe_Str__Code__Formatting("\t"),
                                                  line_end = Safe_Str__Code__Formatting("\r\n"))

        assert str(gen_options.indent)   == "\t"
        assert str(gen_options.line_end) == "\r\n"