from unittest                                 import TestCase
from tests.unit.Service__Fast_API__Test_Objs  import setup__service_fast_api_test_objs
from tests.unit.Service__Fast_API__Test_Objs  import TEST_API_KEY__NAME, TEST_API_KEY__VALUE


class test_Routes__JS__AST__Simple__client(TestCase):

    @classmethod
    def setUpClass(cls):
        with setup__service_fast_api_test_objs() as _:
            cls.client = _.fast_api__client
            cls.client.headers[TEST_API_KEY__NAME] = TEST_API_KEY__VALUE

    def test_js_to_ast_simple(self):
        """Test simple JS to AST conversion"""
        request_data = {
            "code": "const greeting = 'Hello, World!';"
        }

        response = self.client.post('/js-ast-simple/js-to-ast', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert 'ast' in result
        assert result['ast']['type'] == 'Program'
        assert len(result['ast']['body']) == 1
        assert result['ast']['body'][0]['type'] == 'VariableDeclaration'

    def test_ast_to_js_simple(self):
        """Test simple AST to JS conversion"""
        request_data = {
            "ast": {
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
        }

        response = self.client.post('/js-ast-simple/ast-to-js', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert 'code' in result
        assert result['code'] == "const greeting = \"Hello, World!\";\n"

    def test_roundtrip_via_simple_endpoints(self):
        """Test that code survives a roundtrip through both endpoints"""

        # Step 1: Convert JS to AST
        original_code = "function add(a, b) {\n  return a + b;\n}"
        js_to_ast_response = self.client.post('/js-ast-simple/js-to-ast', json={"code": original_code})

        assert js_to_ast_response.status_code == 200
        ast = js_to_ast_response.json()['ast']

        # Step 2: Convert AST back to JS
        ast_to_js_response = self.client.post( '/js-ast-simple/ast-to-js', json={"ast": ast} )

        assert ast_to_js_response.status_code == 200
        generated_code = ast_to_js_response.json()['code']

        # The generated code should be functionally equivalent
        assert "function add" in generated_code
        assert "return a + b" in generated_code

    def test_js_to_ast_complex_code(self):
        """Test JS to AST with more complex code"""
        complex_code = """
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
        }
        
        const calc = new Calculator();
        calc.add(5).multiply(2);
        console.log(calc.result);
        """

        response = self.client.post(
            '/js-ast-simple/js-to-ast',
            json={"code": complex_code}
        )

        assert response.status_code == 200
        result = response.json()
        ast = result['ast']

        # Check that the AST contains the expected structures
        assert ast['type'] == 'Program'
        # Should have class declaration and const declaration
        body_types = [node['type'] for node in ast['body']]
        assert 'ClassDeclaration' in body_types
        assert 'VariableDeclaration' in body_types

    def test_ast_to_js_with_console_log(self):
        """Test AST to JS with console.log statement"""
        ast = {
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
                    "arguments": [
                        {"type": "Literal", "value": "Hello from AST!"}
                    ]
                }
            }],
            "sourceType": "module"
        }

        response = self.client.post(
            '/js-ast-simple/ast-to-js',
            json={"ast": ast}
        )

        assert response.status_code == 200
        result = response.json()
        assert result['code'] == 'console.log("Hello from AST!");\n'

    def test_js_to_ast_error_handling(self):
        """Test error handling for invalid JavaScript"""
        response = self.client.post(
            '/js-ast-simple/js-to-ast',
            json={"code": "const x = ;"}  # Invalid syntax
        )

        assert response.status_code == 500
        error = response.json()
        assert 'detail' in error
        assert 'Parse error' in error['detail']

    def test_ast_to_js_error_handling(self):
        """Test error handling for invalid AST"""
        response = self.client.post(
            '/js-ast-simple/ast-to-js',
            json={"ast": {"type": "InvalidNodeType"}}
        )

        assert response.status_code == 500
        error = response.json()
        assert 'detail' in error

    def test_copy_paste_workflow(self):
        """
        Test the intended copy-paste workflow:
        1. Paste JS code into js-to-ast
        2. Copy the AST
        3. Modify it if needed
        4. Paste into ast-to-js
        5. Get modified JS code
        """

        # Original code
        original = "const x = 10;"

        # Get AST
        ast_response            = self.client.post('/js-ast-simple/js-to-ast',json={"code": original} )
        ast                     = ast_response.json()['ast']
        response__original_ast = self.client.post('/js-ast-simple/ast-to-js', json={"ast": ast})
        code__original_ast     = response__original_ast.json()['code']
        # Modify the AST (change variable name and value)

        ast['body'][0]['declarations'][0]['id']['name'   ] = 'y'
        ast['body'][0]['declarations'][0]['init']['value'] = 20                 # this one doesn't seem to impact the creation
        ast['body'][0]['declarations'][0]['init']['raw'  ] = 20                 # ths is value that has impact
        print(ast)
        # Generate new code
        response__modified_ast = self.client.post( '/js-ast-simple/ast-to-js',json={"ast": ast})
        code__modified_ast = response__modified_ast.json()['code']

        assert code__original_ast == "const x = 10;\n"                               # has the original value of 10 and original variable x
        assert code__modified_ast == "const y = 20;\n"                               # has the modified value of 10 and modified variable y

    def test_js_to_ast_with_arrow_function(self):
        """Test JS to AST with arrow function"""
        code = "const multiply = (a, b) => a * b;"

        response = self.client.post(
            '/js-ast-simple/js-to-ast',
            json={"code": code}
        )

        assert response.status_code == 200
        ast = response.json()['ast']

        # Check for arrow function in AST
        declaration = ast['body'][0]['declarations'][0]
        assert declaration['init']['type'] == 'ArrowFunctionExpression'
        assert len(declaration['init']['params']) == 2

    def test_ast_to_js_with_template_literal(self):
        """Test generating code with template literals"""
        ast = {
            "type": "Program",
            "body": [{
                "type": "VariableDeclaration",
                "declarations": [{
                    "type": "VariableDeclarator",
                    "id": {"type": "Identifier", "name": "message"},
                    "init": {
                        "type": "TemplateLiteral",
                        "quasis": [
                            {"type": "TemplateElement", "value": {"raw": "Hello, ", "cooked": "Hello, "}},
                            {"type": "TemplateElement", "value": {"raw": "!", "cooked": "!"}}
                        ],
                        "expressions": [
                            {"type": "Identifier", "name": "name"}
                        ]
                    }
                }],
                "kind": "const"
            }],
            "sourceType": "module"
        }

        response = self.client.post(
            '/js-ast-simple/ast-to-js',
            json={"ast": ast}
        )

        assert response.status_code == 200
        code = response.json()['code']
        assert "`Hello, ${name}!`" in code


    def test_url_to_ast_simple(self):
        """Test URL to AST conversion with a simple JavaScript file"""
        # Using a small, reliable CDN-hosted file for testing
        request_data = { "url": "https://cdnjs.cloudflare.com/ajax/libs/js-cookie/3.0.1/js.cookie.min.js" }

        response = self.client.get('/js-ast-simple/url-to-ast', params=request_data)

        # If external request fails (CI/CD environments), skip
        if response.status_code == 404:
            self.skipTest("External URL not accessible in test environment")

        assert response.status_code == 200
        result = response.json()
        assert 'ast' in result
        assert 'url' in result
        assert 'size' in result
        assert result['ast']['type'] == 'Program'
        assert result['url'] == request_data['url']
        assert result['size'] > 0

    def test_url_to_ast_invalid_url(self):
        """Test URL to AST with invalid URL format"""
        request_data = { "url": "not-a-valid-url" }

        response = self.client.get('/js-ast-simple/url-to-ast', params=request_data)

        assert response.status_code == 400
        error = response.json()
        assert 'detail' in error
        assert 'must start with http://' in error['detail']

    def test_url_to_ast_html_content(self):
        """Test URL to AST with HTML page instead of JS"""
        request_data = { "url": "https://www.google.com" }

        response = self.client.get('/js-ast-simple/url-to-ast', params=request_data)

        assert response.status_code == 400
        error = response.json()

        assert 'HTML content' in error.get('detail', '')

    def test_url_to_ast_nonexistent(self):
        """Test URL to AST with non-existent URL"""
        request_data = {
            "url": "https://this-domain-definitely-does-not-exist-12345.com/script.js"
        }

        response = self.client.get('/js-ast-simple/url-to-ast', params=request_data)

        assert response.status_code in [404, 500]
        error = response.json()
        assert 'detail' in error
