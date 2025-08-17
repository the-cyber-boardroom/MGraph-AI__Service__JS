import json
from unittest                                                import TestCase
from osbot_utils.utils.Files                                 import file_exists, folder_exists
from mgraph_ai_service_js.service.deno.Deno__JS__Execution   import Deno__JS__Execution
from mgraph_ai_service_js.service.deno.Deno__JS__Execution   import JS__Execution__Config
from mgraph_ai_service_js.service.deno.Deno__JS__Execution   import JS__Execution__Permissions
from mgraph_ai_service_js.service.deno.Deno__JS__Execution   import JS__Execution__Request
from mgraph_ai_service_js.service.deno.Deno__JS__Execution   import JS__Execution__Result


class test_Deno__JS__Execution(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.deno_executor = Deno__JS__Execution()

    def test__init__(self):                                                       # Test initialization
        with self.deno_executor as _:
            assert type(_) is Deno__JS__Execution

    def test_01__setup(self):                                                     # Test setup process
        with self.deno_executor as _:
            assert _.setup() == _
            assert folder_exists(str(_.folder_path__deno_js()))

    def test_02__install(self):                                                   # Test Deno installation
        with self.deno_executor as _:
            assert _.install() is True
            assert file_exists(str(_.file_path__deno()))

    def test_03__execute_simple(self):                                           # Test simple execution
        request = JS__Execution__Request(code   = "console.log(40 + 2);",
                                         config = JS__Execution__Config())

        result = self.deno_executor.execute_js(request)

        assert type(result)       is JS__Execution__Result
        assert result.success     is True
        assert result.output      == "42"
        assert result.error       is None
        assert result.truncated   is False
        assert result.execution_time_ms > 0

    def test_04__execute_with_input_data(self):                                  # Test execution with input data
        request = JS__Execution__Request(
            code       = """
                const numbers = INPUT.numbers;
                const sum = numbers.reduce((a, b) => a + b, 0);
                console.log(`Sum: ${sum}`);
                return sum;
            """,
            config     = JS__Execution__Config(json_output=True),
            input_data = {"numbers": [1, 2, 3, 4, 5]}
        )

        result = self.deno_executor.execute_js(request)

        assert result.success is True
        assert "15" in result.output

    def test_05__execute_with_permissions(self):                                 # Test permission restrictions
        request_no_perms = JS__Execution__Request(                              # Test with no permissions (should fail to access file system)
            code   = """
                try {
                    await Deno.readTextFile('/etc/passwd');
                    console.log('READ SUCCESS');
                } catch (e) {
                    console.log('READ DENIED');
                }
            """,
            config = JS__Execution__Config(
                permissions = JS__Execution__Permissions()  # No permissions
            )
        )

        result = self.deno_executor.execute_js(request_no_perms)

        assert "READ DENIED" in result.output or "PermissionDenied" in str(result.error)

        # Test with read permission to /tmp
        request_with_perms = JS__Execution__Request(
            code   = """
                try {
                    await Deno.writeTextFile('/tmp/test.txt', 'test');
                    console.log('WRITE SUCCESS');
                } catch (e) {
                    console.log('WRITE DENIED');
                }
            """,
            config = JS__Execution__Config(
                permissions = JS__Execution__Permissions(
                    allow_write = ["/tmp"]
                )
            )
        )

        result = self.deno_executor.execute_js(request_with_perms)
        assert "WRITE SUCCESS" in result.output

    def test_06__execute_with_timeout(self):                                     # Test execution timeout
        request = JS__Execution__Request(
            code   = """
                // Infinite loop
                while (true) {
                    // This should timeout
                }
            """,
            config = JS__Execution__Config(max_execution_time_ms=100)
        )

        result = self.deno_executor.execute_js(request)

        assert result.success is False
        assert result.execution_time_ms >= 100
        assert result.execution_time_ms < 500  # Should timeout quickly

    def test_07__execute_with_error(self):                                       # Test error handling
        request = JS__Execution__Request(
            code   = """
                throw new Error('Test error');
            """,
            config = JS__Execution__Config(capture_stderr=True)
        )

        result = self.deno_executor.execute_js(request)

        assert result.success is False
        assert result.error is not None
        assert "Test error" in result.error or "Test error" in result.output

    def test_08__validate_syntax(self):                                          # Test syntax validation

        valid, error = self.deno_executor.validate_js_syntax("const x = 42;")   # Valid syntax
        assert valid is True
        assert error is None

        valid, error = self.deno_executor.validate_js_syntax("const x = ;")     # Invalid syntax

        assert valid is False
        assert error is not None

    def test_09__execute_with_json_output(self):                                 # Test JSON output mode
        request = JS__Execution__Request(
            code   = """
                const result = {
                    name: 'test',
                    value: 42,
                    items: [1, 2, 3]
                };
                return result;
            """,
            config = JS__Execution__Config(json_output=True)
        )

        result      = self.deno_executor.execute_js(request)
        output_data = json.loads(result.output)

        assert result.success       is True
        assert output_data['name']  == 'test'
        assert output_data['value'] == 42
        assert output_data['items'] == [1, 2, 3]

    def test_10__execute_with_output_truncation(self):                          # Test output truncation
        request = JS__Execution__Request(
            code   = """
                // Generate large output
                for (let i = 0; i < 1000; i++) {
                    console.log('A'.repeat(1000));
                }
            """,
            config = JS__Execution__Config(max_output_size=1024)
        )

        result = self.deno_executor.execute_js(request)

        assert result.truncated is True
        assert len(result.output) <= 1024

    def test_11__build_permission_flags(self):                                  # Test permission flag building
        permissions = JS__Execution__Permissions(
            allow_read   = ["/tmp", "/home"],
            allow_write  = ["/tmp"],
            allow_net    = ["api.example.com", "localhost:8080"],
            allow_env    = ["PATH", "HOME"],
            allow_run    = ["ls", "cat"],
            allow_sys    = ["osRelease"],
            allow_ffi    = True,
            allow_hrtime = True,
            prompt       = False
        )

        flags = self.deno_executor.build_permission_flags(permissions)

        assert "--allow-read=/tmp,/home"              in flags
        assert "--allow-write=/tmp"                   in flags
        assert "--allow-net=api.example.com,localhost:8080" in flags
        assert "--allow-env=PATH,HOME"                in flags
        assert "--allow-run=ls,cat"                   in flags
        assert "--allow-sys=osRelease"                in flags
        assert "--allow-ffi"                          in flags
        assert "--allow-hrtime"                       in flags

    def test_12__execute_async_code(self):                                      # Test async JavaScript execution
        request = JS__Execution__Request(
            code   = """
                async function fetchData() {
                    await new Promise(resolve => setTimeout(resolve, 100));
                    return 'async result';
                }
                
                const result = await fetchData();
                console.log(result);
            """,
            config = JS__Execution__Config()
        )

        result = self.deno_executor.execute_js(request)

        assert result.success is True
        assert "async result" in result.output

    def test_13__execute_with_modules(self):                                    # Test module imports (if allowed)
        request = JS__Execution__Request(
            code   = """
                // Test basic JavaScript features
                const arr = [1, 2, 3, 4, 5];
                const doubled = arr.map(x => x * 2);
                const sum = doubled.reduce((a, b) => a + b, 0);
                console.log(sum);
            """,
            config = JS__Execution__Config()
        )

        result = self.deno_executor.execute_js(request)

        assert result.success is True
        assert "30" in result.output  # 2+4+6+8+10 = 30

    # def test_14__cleanup(self):                                                 # Test cleanup (run last)
    #     # Note: Comment out this test during development to avoid re-downloading Deno
    #     # assert self.deno_executor.cleanup() is True
    #     # assert not folder_exists(str(self.deno_executor.folder_path__deno_js()))
    #     pass