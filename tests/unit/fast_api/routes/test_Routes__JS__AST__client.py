from unittest                                 import TestCase
from tests.unit.Service__Fast_API__Test_Objs  import setup__service_fast_api_test_objs
from tests.unit.Service__Fast_API__Test_Objs  import TEST_API_KEY__NAME, TEST_API_KEY__VALUE



class test_Routes__JS__AST__client(TestCase):

    @classmethod
    def setUpClass(cls):
        with setup__service_fast_api_test_objs() as _:
            cls.client = _.fast_api__client
            cls.client.headers[TEST_API_KEY__NAME] = TEST_API_KEY__VALUE


    def test__ast_health(self):                                                      # Test health endpoint
        response = self.client.get('/js-ast/health')
        result   = response.json()
        assert response.status_code       == 200

        assert result == { 'generator': 'astring' ,
                           'parser'   : 'meriyah' ,
                           'service'  : 'js-ast'  ,
                           'status'   : 'healthy' }

    def test__ast_parse_simple(self):                                                # Test parsing simple code
        request_data = {
            "code": "const x = 42;"
        }

        response = self.client.post('/js-ast/parse', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['success']    is True
        assert result['ast']        is not None
        assert result['ast']['type'] == 'Program'
        assert len(result['ast']['body']) == 1

    def test__ast_parse_with_options(self):                                          # Test parsing with options
        request_data = {
            "code": "import { test } from './module';",
            "options": {
                "ecma_version" : "latest",
                "source_type"  : "module",
                "locations"    : True,
                "ranges"       : True
            }
        }

        response = self.client.post('/js-ast/parse', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['success']    is True
        assert result['ast']['sourceType'] == 'module'

    def test__ast_parse_complex_modern_js(self):                                     # Test parsing modern JavaScript
        request_data = {
            "code": """
            async function fetchUser(id) {
                const response = await fetch(`/api/users/${id}`);
                const { data, ...meta } = await response.json();
                return data?.profile ?? null;
            }
            
            class UserManager {
                #privateKey = 'secret';
                
                async getUser(id) {
                    return await fetchUser(id);
                }
            }
            """,
            "options": {
                "ecma_version": "latest",
                "next": True
            }
        }

        response = self.client.post('/js-ast/parse', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['success']          is True
        assert len(result['ast']['body']) == 2

    def test__ast_generate_from_ast(self):                                           # Test generating code from AST
        request_data = {
            "ast": {
                "type": "Program",
                "body": [{
                    "type": "FunctionDeclaration",
                    "id": {"type": "Identifier", "name": "hello"},
                    "params": [],
                    "body": {
                        "type": "BlockStatement",
                        "body": [{
                            "type": "ReturnStatement",
                            "argument": {"type": "Literal", "value": "Hello, World!"}
                        }]
                    }
                }],
                "sourceType": "module"
            },
            "options": {
                "indent": "  "
            }
        }

        response = self.client.post('/js-ast/generate', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result == { 'code'              : 'function hello() {\n  return "Hello, World!";\n}\n',
                           'generation_time_ms': result.get('generation_time_ms')                    ,
                           'success'           : True                                                }

    def test__ast_roundtrip_simple(self):                                            # Test simple roundtrip
        js_code      = "const add = (a, b) => a + b;\n"
        request_data = { "code": js_code}

        response = self.client.post('/js-ast/roundtrip', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['generated_code'] == js_code
        assert result['success'       ]    is True
        assert result['is_valid'      ]    is True

    def test__ast_roundtrip_complex(self):                                           # Test complex roundtrip
        request_data = {
            "code": """
            class Calculator {
                constructor() {
                    this.result = 0;
                }
                
                add(value) {
                    this.result += value;
                    return this;
                }
                
                multiply(value) {
                    this.result *= value;
                    return this;
                }
                
                get() {
                    return this.result;
                }
            }
            """,
            "parser_options": {
                "ecma_version": "latest"
            },
            "generator_options": {
                "indent": "    "
            }
        }

        response = self.client.post('/js-ast/roundtrip', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert "class Calculator"         in result['generated_code']
        assert result['success'         ] is True
        assert result['is_valid'        ] is True
        assert result['parse_time_ms'   ] > 0
        assert result['generate_time_ms'] > 0
        assert result['total_time_ms'   ] > 0

    def test__ast_parse_jsx(self):                                                   # Test parsing JSX
        request_data = {
            "code": """
            const App = () => {
                return (
                    <div className="app">
                        <h1>Hello {userName}</h1>
                        <Button onClick={handleClick}>Click me</Button>
                    </div>
                );
            };
            """,
            "options": {
                "jsx": True
            }
        }

        response = self.client.post('/js-ast/parse', json=request_data)

        assert response.status_code == 200
        result                = response.json()
        ast_first_declaration = result.get('ast').get('body')[0].get('declarations')[0].get('id')
        assert ast_first_declaration == { 'end' : 22           ,
                                          'loc' : {'end': {'column': 21, 'line': 2}, 'start': {'column': 18, 'line': 2}},
                                          'name': 'App'        ,
                                          'range': [19, 22]    ,
                                          'start': 19          ,
                                          'type' : 'Identifier'}
        assert result['success']    is True
        assert result['ast']        is not None

    def test__ast_parse_error(self):                                                 # Test parsing invalid code
        request_data = { "code": "const x = ;"  } # Invalid syntax
        response     = self.client.post('/js-ast/parse', json=request_data)

        assert response.status_code == 500
        assert response.json() == {'detail': 'Parse failed: 400: _1_11___Unexpected_token_____'}


    def test__ast_generate_invalid_ast(self):                                        # Test generating from invalid AST
        request_data = {
            "ast": {
                "type": "InvalidNodeType",
                "invalid": "structure"
            }
        }

        response = self.client.post('/js-ast/generate', json=request_data)

        assert response.status_code == 500

    def test__ast_roundtrip_with_all_options(self):                                  # Test roundtrip with all options
        request_data = {
            "code": "export default function main() { return 42; }",
            "parser_options": {
                "ecma_version" : "latest",
                "source_type"  : "module",
                "jsx"          : False,
                "typescript"   : False,
                "next"         : True,
                "locations"    : True,
                "ranges"       : True,
                "raw"          : True,
                "tokens"       : False,
                "comments"     : True,
                "tolerant"     : False
            },
            "generator_options": {
                "indent"       : "  ",
                "line_end"     : "\n",
                "start_indent" : "",
                "comments"     : True,
                "source_map"   : False
            }
        }

        response = self.client.post('/js-ast/roundtrip', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['success']      is True
        assert result['is_valid']     is True

    def test__ast_parse_large_code(self):                                            # Test parsing large code
        # Generate large code sample
        lines = [f"const var_{i} = {i};" for i in range(50)]
        large_code = "\n".join(lines)

        request_data = {
            "code": large_code,
            "options": {
                "ecma_version": "latest"
            }
        }

        response = self.client.post('/js-ast/parse', json=request_data)

        assert response.status_code             == 200
        result = response.json()
        assert result['success']                is True
        assert len(result['ast']['body'])       >= 50
        assert result['parse_time_ms']          < 5000

    def test__ast_input_validation(self):                                            # Test input validation
        # Test with empty code
        response = self.client.post('/js-ast/parse', json={"code": ""})
        assert response.status_code == 200  # Empty code is valid JavaScript

        # Test with code too large
        huge_code = "x" * 2000000  # Over 1MB limit
        response = self.client.post('/js-ast/parse', json={"code": huge_code})
        assert response.status_code == 400  # Validation error

        # Test with missing code field
        response = self.client.post('/js-ast/parse', json={})
        assert response.status_code == 400  # Missing required field

    def test__ast_roundtrip_typescript_features(self):                               # Test TypeScript-like features
        request_data = {
            "code": """
            interface User {
                name: string;
                age: number;
            }
            
            const user: User = {
                name: "Alice",
                age: 30
            };
            """,
            "options": {
                "typescript": True  # Note: Meriyah doesn't support TS, will fail
            }
        }

        response = self.client.post('/js-ast/parse', json=request_data)

        # Should fail since Meriyah doesn't support TypeScript
        assert response.status_code == 500

    def test__ast_generate_with_custom_formatting(self):                             # Test custom formatting options
        # First parse some code
        parse_response = self.client.post('/js-ast/parse', json={
            "code": "function test(){return 42;}"
        })

        assert parse_response.status_code == 200
        ast = parse_response.json()['ast']

        # Generate with custom formatting
        request_data = {
            "ast": ast,
            "options": {
                "indent"   : "\t",      # Tab indentation
                "line_end" : "\r\n",    # Windows line endings
                "comments" : False
            }
        }

        response = self.client.post('/js-ast/generate', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['success']    is True
        assert "function test"      in result['code']