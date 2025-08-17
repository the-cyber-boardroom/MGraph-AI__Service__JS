import json
from unittest                                                        import TestCase
from osbot_utils.utils.Files                                         import file_exists, folder_exists, current_temp_folder
from osbot_utils.utils.Objects                                       import __
from mgraph_ai_service_js.service.deno.Deno__JS__Execution           import DENO__VERSION__COMPATIBLE_WITH_LAMBDA, JS__Execution__Permissions
from mgraph_ai_service_js.service.deno.Deno__JS__Module__Execution   import Deno__JS__Module__Execution
from mgraph_ai_service_js.service.deno.Deno__JS__Module__Execution   import JS__Module__Execution__Config
from mgraph_ai_service_js.service.deno.Deno__JS__Module__Execution   import JS__Module__Execution__Request


class test_Deno__JS__Module__Execution(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.module_executor = Deno__JS__Module__Execution()
        cls.module_executor.setup()

    def test__init__(self):                                                       # Test initialization
        with self.module_executor as _:
            assert type(_) is Deno__JS__Module__Execution

    def test_01__setup_and_install(self):                                        # Test setup and installation
        with self.module_executor as _:
            assert _.setup() == _
            assert folder_exists(str(_.folder_path__deno_js()))
            assert _.install() is True
            assert file_exists(str(_.file_path__deno()))

    def test_02__execute_with_url_import(self):                                  # Test direct URL import
        request = JS__Module__Execution__Request(
            code = """
                import { chunk } from 'https://cdn.skypack.dev/lodash@4';
                const result = chunk([1, 2, 3, 4, 5, 6], 2);
                console.log(JSON.stringify(result));
            """,
            config = JS__Module__Execution__Config(
                allow_url_imports = True
            )
        )

        result = self.module_executor.execute_module_js(request)

        assert result.obj() == __( success              = True                                        ,
                                   output               = '[[1,2],[3,4],[5,6]]'                       ,
                                   error                = None                                        ,
                                   execution_time_ms    = result.execution_time_ms                    ,
                                   memory_used_mb       = None                                        ,
                                   truncated            = False                                       ,
                                   deno_version         = f'v{DENO__VERSION__COMPATIBLE_WITH_LAMBDA}' )
        assert result.execution_time_ms < 3000  # First import might be slower

    def test_03__execute_with_lodash_import(self):                               # Test lodash from CDN
        request = JS__Module__Execution__Request(
            code = """
                import _ from 'https://esm.sh/lodash@4.17.21';
                const result = _.chunk(['a', 'b', 'c', 'd'], 2);
                console.log(JSON.stringify(result));
            """,
            config = JS__Module__Execution__Config(
                allow_url_imports = True
            )
        )

        result = self.module_executor.execute_module_js(request)

        assert result.success is True
        assert '[["a","b"],["c","d"]]' in result.output

    def test_04__execute_with_multiple_imports(self):                            # Test multiple imports in same file
        request = JS__Module__Execution__Request(
            code = """
                import _ from 'https://cdn.skypack.dev/lodash@4';
                import { delay } from 'https://deno.land/std@0.208.0/async/delay.ts';
                
                const arr = [1, 2, 3, 4, 5];
                const sum = _.sum(arr);
                const mean = _.mean(arr);
                
                console.log(`Sum: ${sum}, Mean: ${mean}`);
                await delay(1);  // Small delay to test async
                console.log('After delay');
            """,
            config = JS__Module__Execution__Config(
                allow_url_imports = True
            )
        )

        result = self.module_executor.execute_module_js(request)
        assert result.success is True
        assert result.output == 'Sum: 15, Mean: 3\nAfter delay'

    def test_05__execute_with_deno_std_library(self):                            # Test Deno standard library
        request = JS__Module__Execution__Request(
            code = """
                import { assertEquals } from 'https://deno.land/std@0.208.0/testing/asserts.ts';
                
                try {
                    assertEquals(1 + 1, 2);
                    assertEquals('hello', 'hello');
                    console.log('All assertions passed!');
                } catch (e) {
                    console.error('Assertion failed:', e.message);
                }
            """,
            config = JS__Module__Execution__Config(
                allow_url_imports = True
            )
        )

        result = self.module_executor.execute_module_js(request)

        assert result.success is True
        assert "All assertions passed!" in result.output

    def test_06__execute_with_manual_input_data(self):                           # Test with manual input data setup
        request = JS__Module__Execution__Request(
            code = """
                import _ from 'https://esm.sh/lodash@4.17.21';
                
                // Define input data manually
                const INPUT = {
                    numbers: [1, 2, 3, 4, 5],
                    multiplier: 3
                };
                
                const doubled = _.map(INPUT.numbers, n => n * INPUT.multiplier);
                const sum = _.sum(doubled);
                
                console.log(JSON.stringify({
                    original: INPUT.numbers,
                    doubled: doubled,
                    sum: sum
                }));
            """,
            config = JS__Module__Execution__Config(
                allow_url_imports = True
            )
        )

        result = self.module_executor.execute_module_js(request)

        assert result.success is True
        assert result.output == '{"original":[1,2,3,4,5],"doubled":[3,6,9,12,15],"sum":45}'

    def test_07__execute_with_typescript(self):                                  # Test TypeScript support
        request = JS__Module__Execution__Request(
            code = """
                // TypeScript code
                interface User {
                    name: string;
                    age: number;
                }
                
                const users: User[] = [
                    { name: 'Alice', age: 30 },
                    { name: 'Bob', age: 25 }
                ];
                
                const names: string[] = users.map((u: User) => u.name);
                console.log(names.join(', '));
            """,
            config = JS__Module__Execution__Config()
        )

        result = self.module_executor.execute_module_js(request)

        assert result.success is True
        assert "Alice, Bob" in result.output

    def test_08__execute_with_async_and_top_level_await(self):                   # Test async/await
        request = JS__Module__Execution__Request(
            code = """
                import { delay } from 'https://deno.land/std@0.208.0/async/delay.ts';
                
                console.log('Starting...');
                await delay(1);  // Wait 1ms
                console.log('Finished after delay');
                
                // Can't use return at top level, just log result
                const result = 'completed';
                console.log(result);
            """,
            config = JS__Module__Execution__Config(
                allow_url_imports = True
            )
        )

        result = self.module_executor.execute_module_js(request)

        assert result.success is True
        assert "Starting..." in result.output
        assert "Finished after delay" in result.output
        assert "completed" in result.output

    def test_09__execute_with_function_wrapper_for_return(self):                 # Test using function to return value
        request = JS__Module__Execution__Request(
            code = """
                import _ from 'https://esm.sh/lodash@4.17.21';
                
                function process() {
                    const numbers = [1, 2, 3, 4, 5];
                    const doubled = _.map(numbers, n => n * 2);
                    return doubled;
                }
                
                const result = process();
                console.log(JSON.stringify(result));
            """,
            config = JS__Module__Execution__Config(
                allow_url_imports = True
            )
        )

        result = self.module_executor.execute_module_js(request)

        assert result.success is True
        assert "[2,4,6,8,10]" in result.output

    def test_10__execute_without_network_permissions(self):                      # Test network permission restrictions
        request = JS__Module__Execution__Request(
            code = """
                import _ from 'https://cdn.skypack.dev/lodash@4';
                console.log('Should not reach here');
            """,
            config = JS__Module__Execution__Config(
                allow_url_imports = False  # Disable URL imports
            )
        )

        result = self.module_executor.execute_module_js(request)

        # Should fail because imports are not allowed
        assert result.error.index('Requires import access to "cdn.skypack.dev:443", run again with the --allow-import flag') == 24
        assert result.success is False
        assert result.error is not None

    def test_11__execute_with_cache_control(self):                               # Test import caching
        # First execution - might download
        request_cached = JS__Module__Execution__Request(
            code = """
                import _ from 'https://esm.sh/lodash@4.17.21';
                const sum = _.sum([1, 2, 3]);
                console.log(`Sum: ${sum}`);
            """,
            config = JS__Module__Execution__Config(
                cache_imports = True,  # Enable caching
                allow_url_imports = True
            )
        )

        result1 = self.module_executor.execute_module_js(request_cached)
        time1   = result1.execution_time_ms
        assert result1.success is True
        assert "Sum: 6" in result1.output


        # Second execution - should use cache (potentially faster)
        result2 = self.module_executor.execute_module_js(request_cached)
        time2   = result2.execution_time_ms
        assert result2.success is True
        assert "Sum: 6" in result2.output


        # Third execution with reload - should re-download
        request_no_cache = JS__Module__Execution__Request(
            code = request_cached.code,
            config = JS__Module__Execution__Config(
                cache_imports = False,  # Force reload
                allow_url_imports = True
            )
        )
        result3 = self.module_executor.execute_module_js(request_no_cache)
        time3 = result3.execution_time_ms
        assert result3.success is True
        assert "Sum: 6" in result3.output
        assert time1 < time3
        #assert time2 < time3 # 36 37 301       # note the significant impact of using the cache


    def test_12__build_module_permission_flags(self):                            # Test permission flag building
        config = JS__Module__Execution__Config(
            allow_url_imports = True,
            allowed_import_hosts = ['example.com', 'cdn.test.com'],
            cache_imports = False
        )

        flags = self.module_executor.build_module_permission_flags(config)

        # Should have import permissions
        assert any('--allow-import=' in flag for flag in flags)

        # Should have network permissions
        assert any('--allow-net=' in flag for flag in flags)

        # Should have reload flag when cache is disabled
        assert '--reload' in flags

        # Check that custom hosts are included
        import_flag = [f for f in flags if f.startswith('--allow-import=')][0]
        assert 'example.com' in import_flag
        assert 'cdn.test.com' in import_flag

    def test_13__error_handling_invalid_import(self):                            # Test error handling
        request = JS__Module__Execution__Request(
            code = """
                import something from 'https://invalid-url-that-does-not-exist.com/module.js';
                console.log('Should not reach here');
            """,
            config = JS__Module__Execution__Config(allow_url_imports = True,
                                                   capture_stderr = True)
        )

        result = self.module_executor.execute_module_js(request)
        assert result.success is False
        assert result.error is not None

    def test_14__error_handling_syntax_error(self):                              # Test syntax error handling
        request = JS__Module__Execution__Request(
            code = """
                import _ from 'https://esm.sh/lodash@4.17.21';
                const x = ;  // Syntax error
            """,
            config = JS__Module__Execution__Config(
                allow_url_imports = True
            )
        )

        result = self.module_executor.execute_module_js(request)

        assert result.success is False
        assert result.error.index("The module's source code could not be parsed: Expression expected at") == 24

    def test_15__complex_real_world_example(self):                               # Complex real-world example
        request = JS__Module__Execution__Request(
            code = """
                import _ from 'https://esm.sh/lodash@4.17.21';
                
                // Define input data
                const INPUT = {
                    minAge: 25,
                    users: [
                        {name: "Alice", age: 30, department: "Engineering"},
                        {name: "Bob", age: 22, department: "Engineering"},
                        {name: "Charlie", age: 35, department: "Sales"},
                        {name: "Diana", age: 28, department: "Engineering"},
                        {name: "Eve", age: 26, department: "Sales"}
                    ]
                };
                
                // Process users
                const validUsers = _.filter(INPUT.users, u => u.age >= INPUT.minAge);
                const grouped = _.groupBy(validUsers, 'department');
                const stats = _.mapValues(grouped, dept => ({
                    count: dept.length,
                    avgAge: _.meanBy(dept, 'age'),
                    names: _.map(dept, 'name')
                }));
                
                const result = {
                    totalUsers: INPUT.users.length,
                    validUsers: validUsers.length,
                    departments: Object.keys(grouped).length,
                    stats: stats
                };
                
                console.log(JSON.stringify(result));
            """,
            config = JS__Module__Execution__Config(
                allow_url_imports = True
            )
        )

        result = self.module_executor.execute_module_js(request)

        assert result.success is True
        output_data = json.loads(result.output)
        assert output_data == {  'departments': 2,
                                 'stats'      : {'Engineering': { 'avgAge': 29,
                                                                  'count' : 2,
                                                                  'names' : ['Alice', 'Diana']},
                                                 'Sales'      : {'avgAge': 30.5,
                                                                 'count': 2,
                                                                 'names': ['Charlie', 'Eve']}},
                                 'totalUsers': 5,
                                 'validUsers': 4 }  # Bob is excluded (age 22)

    def test_16__execute_with_different_cdn_sources(self):                       # Test different CDN sources
        # Test with esm.sh
        request_esm = JS__Module__Execution__Request(
            code = """
                import _ from 'https://esm.sh/lodash@4.17.21';
                const unique = _.uniq([1, 2, 2, 3, 3, 3]);
                console.log('esm.sh:', JSON.stringify(unique));
            """,
            config = JS__Module__Execution__Config(allow_url_imports = True)
        )

        result_esm = self.module_executor.execute_module_js(request_esm)
        assert result_esm.success is True
        assert "esm.sh: [1,2,3]" in result_esm.output

        # Test with Skypack
        request_skypack = JS__Module__Execution__Request(
            code = """
                import _ from 'https://cdn.skypack.dev/lodash@4';
                const unique = _.uniq([1, 2, 2, 3, 3, 3]);
                console.log('skypack:', JSON.stringify(unique));
            """,
            config = JS__Module__Execution__Config(allow_url_imports = True)
        )

        result_skypack = self.module_executor.execute_module_js(request_skypack)
        assert result_skypack.success is True
        assert "skypack: [1,2,3]" in result_skypack.output

    def test_17__execute_with_file_output(self):                                 # Test writing output to file
        request = JS__Module__Execution__Request(
            code = """
                import _ from 'https://esm.sh/lodash@4.17.21';
                
                const data = {
                    processed: true,
                    results: _.chunk([1, 2, 3, 4, 5, 6], 2),
                    timestamp: Date.now()
                };
                
                // Write to temp file
                const outputPath = '/tmp/test_output.json';
                await Deno.writeTextFile(outputPath, JSON.stringify(data, null, 2));
                
                console.log('Data written to:', outputPath);
                console.log('Results:', JSON.stringify(data.results));
            """,
            config = JS__Module__Execution__Config(allow_url_imports = True,
                                                   permissions       = JS__Execution__Permissions(allow_write = ['/tmp'])))



        result = self.module_executor.execute_module_js(request)

        assert result.success is True
        assert "Data written to: /tmp/test_output.json" in result.output
        assert "[[1,2],[3,4],[5,6]]" in result.output

    def test_18__but__execute_with_jsx__not_supported(self):                                         # Test JSX support (Deno supports it)

        request = JS__Module__Execution__Request(
            code = """
                /** @jsx h */
                function h(tag, props, ...children) {
                    return { tag, props, children };
                }
                
                const element = <div class="container">
                    <h1>Hello</h1>
                    <p>World</p>
                </div>;
                
                console.log(JSON.stringify(element));
            """,
            config = JS__Module__Execution__Config()
        )

        result = self.module_executor.execute_module_js(request)

        assert result.error.index("The module's source code could not be parsed: Expected '>', got 'class'") == 24
        assert result.success            is False                       # BUG: fails here with passing error
        assert result.output             == ""                          # BUG: we should have an output
        assert '"tag":"div"'         not in result.output
        assert '"class":"container"' not in result.output