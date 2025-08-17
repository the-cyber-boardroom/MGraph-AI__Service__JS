import json
from unittest                                 import TestCase
from tests.unit.Service__Fast_API__Test_Objs  import setup__service_fast_api_test_objs
from tests.unit.Service__Fast_API__Test_Objs  import TEST_API_KEY__NAME, TEST_API_KEY__VALUE


class test_Routes__JS__Module__Execute__client(TestCase):

    @classmethod
    def setUpClass(cls):
        with setup__service_fast_api_test_objs() as _:
            cls.client = _.fast_api__client
            cls.client.headers[TEST_API_KEY__NAME] = TEST_API_KEY__VALUE

            # Add the module routes to the FastAPI app
            from mgraph_ai_service_js.fast_api.routes.Routes__JS__Module__Execute import Routes__JS__Module__Execute
            routes_module = Routes__JS__Module__Execute()
            routes_module.setup_routes()
            _.fast_api.add_routes(Routes__JS__Module__Execute)

    def test__module_health(self):                                               # Test health endpoint
        response = self.client.get('/js-module/health')

        assert response.status_code == 200
        result = response.json()
        assert result['service'] == 'js-module-execution'
        assert result['runtime'] == 'deno'
        assert result['module_support'] is True
        assert result['status'] in ['healthy', 'degraded', 'unhealthy']

    def test__module_info(self):                                                 # Test info endpoint
        response = self.client.get('/js-module/info')

        assert response.status_code == 200
        result = response.json()

        # Check allowed hosts
        assert 'default_allowed_hosts' in result
        assert 'esm.sh' in result['default_allowed_hosts']
        assert 'cdn.skypack.dev' in result['default_allowed_hosts']

        # Check features
        assert result['features']['url_imports'] is True
        assert result['features']['npm_packages'] is True
        assert result['features']['typescript'] is True
        assert result['features']['top_level_await'] is True

        # Check examples exist
        assert 'examples' in result
        assert 'lodash_import' in result['examples']
        assert 'deno_std' in result['examples']

    def test__execute_with_url_import(self):                                     # Test URL import
        request_data = {
            "code": """
                import { chunk } from 'https://cdn.skypack.dev/lodash@4';
                const result = chunk(['a', 'b', 'c', 'd'], 2);
                console.log(JSON.stringify(result));
            """
        }

        response = self.client.post('/js-module/execute', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert '[["a","b"],["c","d"]]' in result['output']

    def test__execute_with_lodash_esm(self):                                     # Test lodash from esm.sh
        request_data = {
            "code": """
                import _ from 'https://esm.sh/lodash@4.17.21';
                const sum = _.sum([10, 20, 30]);
                console.log(`Sum: ${sum}`);
            """
        }

        response = self.client.post('/js-module/execute', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert "Sum: 60" in result['output']

    def test__execute_with_deno_std(self):                                       # Test Deno standard library
        request_data = {
            "code": """
                import { assertEquals } from 'https://deno.land/std@0.208.0/testing/asserts.ts';
                
                assertEquals(2 + 2, 4);
                console.log('Test passed!');
            """
        }

        response = self.client.post('/js-module/execute', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert "Test passed!" in result['output']

    def test__execute_with_typescript(self):                                     # Test TypeScript support
        request_data = {
            "code": """
                interface Point {
                    x: number;
                    y: number;
                }
                
                const points: Point[] = [
                    {x: 1, y: 2},
                    {x: 3, y: 4}
                ];
                
                const sumX: number = points.reduce((sum, p) => sum + p.x, 0);
                console.log(`Sum of X coordinates: ${sumX}`);
            """
        }

        response = self.client.post('/js-module/execute', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert "Sum of X coordinates: 4" in result['output']

    def test__execute_with_async(self):                                          # Test async/await
        request_data = {
            "code": """
                import { delay } from 'https://deno.land/std@0.208.0/async/delay.ts';
                
                async function process() {
                    console.log('Start');
                    await delay(50);
                    console.log('End');
                    return 'Done';
                }
                
                const result = await process();
                console.log(result);
            """
        }

        response = self.client.post('/js-module/execute', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert "Start" in result['output']
        assert "End" in result['output']
        assert "Done" in result['output']

    def test__execute_with_multiple_imports(self):                               # Test multiple imports
        request_data = {
            "code": """
                import _ from 'https://esm.sh/lodash@4.17.21';
                import { format } from 'https://deno.land/std@0.208.0/datetime/format.ts';
                
                const numbers = [1, 2, 3, 4, 5];
                const sum = _.sum(numbers);
                const date = new Date(2024, 0, 1);
                const formatted = format(date, 'yyyy-MM-dd');
                
                console.log(`Sum: ${sum}, Date: ${formatted}`);
            """
        }

        response = self.client.post('/js-module/execute', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert "Sum: 15" in result['output']
        assert "2024-01-01" in result['output']

    def test__execute_with_cache_disabled(self):                                 # Test with cache disabled
        request_data = {
            "code": """
                import _ from 'https://esm.sh/lodash@4.17.21';
                const sum = _.sum([5, 10, 15]);
                console.log(`No cache sum: ${sum}`);
            """,
            "config": {
                "cache_imports": False
            }
        }

        response = self.client.post('/js-module/execute', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert "No cache sum: 30" in result['output']

    def test__execute_with_custom_import_hosts(self):                            # Test custom allowed hosts
        request_data = {
            "code": """
                import _ from 'https://esm.sh/lodash@4';
                console.log('Import successful');
            """,
            "config": {
                "allowed_import_hosts": ["esm.sh", "cdn.skypack.dev"]
            }
        }

        response = self.client.post('/js-module/execute', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert "Import successful" in result['output']

    def test__execute_with_file_write(self):                                     # Test file write permission
        request_data = {
            "code": """
                const data = { test: true, timestamp: Date.now() };
                await Deno.writeTextFile('/tmp/test.json', JSON.stringify(data));
                console.log('File written successfully');
            """,
            "config": {
                "allow_write": ["/tmp"]
            }
        }

        response = self.client.post('/js-module/execute', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert "File written successfully" in result['output']

    def test__execute_with_error_handling(self):                                 # Test error handling
        request_data = {
            "code": """
                import nonexistent from 'https://invalid-domain-xyz123.com/module.js';
                console.log('Should not reach here');
            """,
            "config": {
                "capture_stderr": True
            }
        }

        response = self.client.post('/js-module/execute', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['success'] is False
        assert result['error'] is not None

    def test__execute_with_timeout(self):                                        # Test timeout handling
        request_data = {
            "code": """
                // Infinite loop to test timeout
                while (true) {
                    // This should timeout
                }
            """,
            "config": {
                "max_execution_time_ms": 100
            }
        }

        response = self.client.post('/js-module/execute', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['success'] is False
        assert result['execution_time_ms'] >= 100

    def test__execute_complex_data_processing(self):                             # Complex data processing example
        request_data = {
            "code": """
                import _ from 'https://esm.sh/lodash@4.17.21';
                
                // Define input data directly
                const INPUT = {
                    sales: [
                        {"product": "Widget", "amount": 100},
                        {"product": "Gadget", "amount": 150},
                        {"product": "Widget", "amount": 200},
                        {"product": "Gadget", "amount": 175},
                        {"product": "Widget", "amount": 150},
                        {"product": "Doohickey", "amount": 75}
                    ]
                };
                
                // Group by product
                const byProduct = _.groupBy(INPUT.sales, 'product');
                
                // Calculate stats per product
                const stats = _.mapValues(byProduct, (items, product) => ({
                    product: product,
                    totalRevenue: _.sumBy(items, 'amount'),
                    avgRevenue: _.meanBy(items, 'amount'),
                    count: items.length,
                    maxSale: _.maxBy(items, 'amount')
                }));
                
                // Find top product
                const topProduct = _.maxBy(
                    Object.values(stats), 
                    'totalRevenue'
                );
                
                const result = {
                    productStats: stats,
                    topProduct: topProduct.product,
                    topRevenue: topProduct.totalRevenue
                };
                
                console.log(JSON.stringify(result));
            """
        }

        response = self.client.post('/js-module/execute', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True

        output_data = json.loads(result['output'])
        assert output_data['topProduct'] == 'Widget'  # Widget has 450 total
        assert output_data['topRevenue'] == 450

    def test__execute_validation_errors(self):                                   # Test input validation
        # Test with empty code
        response = self.client.post('/js-module/execute', json={"code": ""})
        assert response.status_code == 400

        # Test with code too large
        huge_code = "x" * 2000000  # Over 1MB limit
        response = self.client.post('/js-module/execute', json={"code": huge_code})
        assert response.status_code == 400

        # Test with invalid config values
        request_data = {
            "code": "console.log('test');",
            "config": {
                "max_execution_time_ms": 50  # Below minimum (100)
            }
        }
        response = self.client.post('/js-module/execute', json=request_data)
        assert response.status_code == 400

    def test__execute_real_world_csv_transformation(self):                       # Real-world: CSV data transformation
        request_data = {
            "code": """
                import _ from 'https://esm.sh/lodash@4.17.21';
                
                // Define CSV data
                const csvData = "name,category,price\\nApple,Fruit,1.50\\nBanana,Fruit,0.75\\nCarrot,Vegetable,0.50\\nBroccoli,Vegetable,2.00";
                
                // Parse CSV
                const lines = csvData.trim().split('\\n');
                const headers = lines[0].split(',');
                
                const data = _.tail(lines).map(line => {
                    const values = line.split(',');
                    return _.zipObject(headers, values);
                });
                
                // Group by category and calculate stats
                const grouped = _.groupBy(data, 'category');
                const summary = _.mapValues(grouped, (items, cat) => ({
                    category: cat,
                    count: items.length,
                    items: _.map(items, 'name')
                }));
                
                console.log(JSON.stringify(summary));
            """
        }

        response = self.client.post('/js-module/execute', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True

        output_data = json.loads(result['output'])
        from osbot_utils.utils.Dev import pprint
        assert output_data == { 'Fruit'    : { 'category': 'Fruit'    , 'count': 2, 'items': ['Apple' , 'Banana'  ]},
                                'Vegetable': { 'category': 'Vegetable', 'count': 2, 'items': ['Carrot', 'Broccoli']}}


    def test__execute_with_different_cdn_providers(self):                        # Test different CDN providers
        # Test with esm.sh
        request_esm = {
            "code": """
                import _ from 'https://esm.sh/lodash@4.17.21';
                console.log('esm.sh:', _.VERSION);
            """
        }

        response = self.client.post('/js-module/execute', json=request_esm)
        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True
        assert result['output'] == 'esm.sh: 4.17.21'

        # Test with Skypack
        request_skypack = {
            "code": """
                import _ from 'https://cdn.skypack.dev/lodash@4';
                console.log('skypack:', typeof _);
            """
        }

        response = self.client.post('/js-module/execute', json=request_skypack)
        result   = response.json()
        assert response.status_code == 200
        assert result['success']    is True
        assert result['output']     == "skypack: function"

    def test__execute_syntax_error(self):                                        # Test syntax error handling
        request_data = {
            "code": """
                import _ from 'https://esm.sh/lodash@4.17.21';
                const x = ;  // Syntax error
            """
        }

        response = self.client.post('/js-module/execute', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['success'] is False
        assert result['error'] is not None
        assert result['error'].index("The module's source code could not be parsed: Expression expected at") == 24

    def test__execute_with_function_return(self):                                # Test using function to simulate return
        request_data = {
            "code": """
                import _ from 'https://esm.sh/lodash@4.17.21';
                
                function processData() {
                    const numbers = [1, 2, 3, 4, 5];
                    const doubled = _.map(numbers, n => n * 2);
                    return { 
                        original: numbers, 
                        doubled: doubled,
                        sum: _.sum(doubled)
                    };
                }
                
                const result = processData();
                console.log(JSON.stringify(result));
            """
        }

        response = self.client.post('/js-module/execute', json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result['success'] is True

        output_data = json.loads(result['output'])
        assert output_data == {'doubled' : [2, 4, 6, 8, 10],
                               'original': [1, 2, 3, 4, 5 ],
                               'sum'     : 30              }   # 2+4+6+8+10