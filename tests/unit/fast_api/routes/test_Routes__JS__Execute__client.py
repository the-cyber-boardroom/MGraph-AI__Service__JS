from unittest                                 import TestCase
from osbot_utils.utils.Objects                import obj
from tests.unit.Service__Fast_API__Test_Objs  import setup__service_fast_api_test_objs
from tests.unit.Service__Fast_API__Test_Objs  import TEST_API_KEY__NAME, TEST_API_KEY__VALUE
import json


class test_Routes__JS__Execute__client(TestCase):

    @classmethod
    def setUpClass(cls):
        with setup__service_fast_api_test_objs() as _:
            cls.client = _.fast_api__client
            cls.client.headers[TEST_API_KEY__NAME] = TEST_API_KEY__VALUE

    def test__js_execute__health(self):                                          # Test health endpoint
        response = self.client.get('/js-execute/health')

        assert response.status_code == 200
        result = response.json()
        assert result['service'] == 'js-execution'
        assert result['runtime'] == 'deno'
        assert result['status'] in ['healthy', 'degraded', 'unhealthy']

    def test__js_execute__simple(self):                                          # Test simple execution
        request_data = {
            "code": "console.log(40 + 2);"
        }

        response = self.client.post('/js-execute/execute', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert result['output'] == "42"
        assert result['error'] is None
        assert result['execution_time_ms'] > 0

    def test__js_execute__with_input_data(self):                                # Test with input data
        request_data = {
            "code": """
                const numbers = INPUT.numbers;
                const sum = numbers.reduce((a, b) => a + b, 0);
                console.log(sum);
            """,
            "input_data": {
                "numbers": [10, 20, 30, 40]
            }
        }

        response = self.client.post('/js-execute/execute', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert "100" in result['output']

    def test__js_execute__with_json_output(self):                               # Test JSON output mode
        request_data = {
            "code": """
                const result = {
                    status: 'success',
                    value: 123,
                    items: ['a', 'b', 'c']
                };
                return result;
            """,
            "config": {
                "json_output": True
            }
        }

        response = self.client.post('/js-execute/execute', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True

        # Parse the JSON output
        output_data = json.loads(result['output'])
        assert output_data['status'] == 'success'
        assert output_data['value'] == 123
        assert output_data['items'] == ['a', 'b', 'c']

    def test__js_execute__with_permissions(self):                               # Test permission configuration
        request_data = {
            "code": """
                console.log('Execution with limited permissions');
            """,
            "config": {
                "permissions": {
                    "allow_read": ["/tmp"],
                    "allow_write": [],
                    "allow_net": []
                }
            }
        }

        response = self.client.post('/js-execute/execute', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert "Execution with limited permissions" in result['output']

    def test__js_execute__with_timeout(self):                                   # Test timeout handling
        request_data = {
            "code": """
                // Long running code
                const start = Date.now();
                while (Date.now() - start < 10000) {
                    // Loop for 10 seconds
                }
            """,
            "config": {
                "max_execution_time_ms": 100  # 100ms timeout
            }
        }

        response = self.client.post('/js-execute/execute', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['success'] is False
        assert result['execution_time_ms'] >= 100

    def test__js_execute__with_error(self):                                     # Test error handling
        request_data = {
            "code": """
                throw new Error('Intentional error for testing');
            """,
            "config": {
                "capture_stderr": True
            }
        }

        response = self.client.post('/js-execute/execute', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['success'] is False
        assert "Intentional error" in (result['error'] or result['output'])

    def test__js_execute__validate_valid(self):                                 # Test validation - valid code
        request_data = {
            "code": """
                const x = 42;
                function test() {
                    return x * 2;
                }
            """
        }

        response = self.client.post('/js-execute/validate', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['valid'] is True
        assert result['error'] is None

    def test__js_execute__validate_invalid(self):                               # Test validation - invalid code
        request_data = {
            "code": """
                const x = ;  // Invalid syntax
            """
        }

        response = self.client.post('/js-execute/validate', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['valid'] is False
        assert result['error'] is not None

    def test__js_execute__with_resource_limits(self):                           # Test resource limits
        request_data = {
            "code": """
                // Generate output within limits
                for (let i = 0; i < 10; i++) {
                    console.log(`Line ${i}`);
                }
            """,
            "config": {
                "max_execution_time_ms": 5000,
                "max_memory_mb": 128,
                "max_output_size": 1024
            }
        }

        response = self.client.post('/js-execute/execute', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert len(result['output']) <= 1024

    def test__js_execute__async_code(self):                                     # Test async JavaScript
        request_data = {
            "code": """
                async function delay(ms) {
                    return new Promise(resolve => setTimeout(resolve, ms));
                }
                
                await delay(10);
                console.log('Async complete');
            """
        }

        response = self.client.post('/js-execute/execute', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert "Async complete" in result['output']

    def test__js_execute__complex_computation(self):                            # Test complex computation
        request_data = {
            "code": """
                // Fibonacci calculation
                function fibonacci(n) {
                    if (n <= 1) return n;
                    return fibonacci(n - 1) + fibonacci(n - 2);
                }
                
                const result = fibonacci(10);
                console.log(`Fibonacci(10) = ${result}`);
                return result;
            """,
            "config": {
                "json_output": True
            }
        }

        response = self.client.post('/js-execute/execute', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert "55" in result['output']  # Fibonacci(10) = 55

    def test__js_execute__input_validation(self):                               # Test input validation
        # Test with empty code
        request_data = {"code": ""}
        response = self.client.post('/js-execute/execute', json=request_data)
        assert response.status_code == 400  # Validation error
        assert response.text == ('{"detail":[{"type":"string_too_short","loc":["body","code"],"msg":"String '
                                   'should have at least 1 character","input":"","ctx":{"min_length":1}}]}') != ()

        # Test with code too long
        request_data = {"code": "x" * 2000000}  # Over 1MB limit
        response = self.client.post('/js-execute/execute', json=request_data)
        assert response.status_code == 400  # Validation error
        assert obj(response.json()).detail[0].msg == 'String should have at most 1048576 characters'

        # Test with invalid config values
        request_data = {
            "code": "console.log('test');",
            "config": {
                "max_execution_time_ms": 50  # Below minimum (100)
            }
        }
        response = self.client.post('/js-execute/execute', json=request_data)
        assert response.status_code == 400  # Validation error

        assert response.text == ('{"detail":[{"type":"greater_than_equal","loc":["body","config","max_execution_time_ms"],"msg":"Input '
                                 'should be greater than or equal to 100","input":50,"ctx":{"ge":100}}]}')
