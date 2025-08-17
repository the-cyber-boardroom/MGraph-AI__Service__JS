from unittest import TestCase

from osbot_utils.helpers.duration.decorators.print_duration import print_duration
from osbot_utils.utils.Dev import pprint
from osbot_utils.utils.Files                                import folder_exists, file_exists
from mgraph_ai_service_js.service.deno.Deno__Setup          import Deno__Setup


class test_Deno__Setup(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.deno_setup = Deno__Setup()

    def test_setUpClass(self):
        with self.deno_setup as _:
            assert type(_) is Deno__Setup

    def test_1__setup(self):
        with self.deno_setup as _:
            assert _.setup() == _
            assert folder_exists(_.folder_path__deno_js())

    def test_2__install(self):
        with self.deno_setup as _:
            print()
            with print_duration():
                assert _.install() is True
                assert file_exists(_.file_path__deno())

    def test_3__execute(self):
        with self.deno_setup as _:
            result = _.execute(['-h'])
            assert result == { 'cwd'      : '.',
                               'error'    : None,
                               'kwargs'   : {'cwd': '.', 'stderr': -1, 'stdout': -1, 'timeout': None},
                               'runParams': [ _.file_path__deno() , '-h'],
                               'status'   : 'ok',
                               'stderr'   : '',
                               'stdout'   : result.get('stdout')}

            assert _.execute([]) == { 'cwd': '.',
                                      'error': None,
                                      'kwargs': {'cwd': '.', 'stderr': -1, 'stdout': -1, 'timeout': None},
                                      'runParams': [ _.file_path__deno()],
                                      'status': 'ok',
                                      'stderr': '',
                                      'stdout': 'Deno 2.4.0\n'
                                                'exit using ctrl+d, ctrl+c, or close()\n'
                                                '\x1b[0m\x1b[33mREPL is running with all permissions '
                                                'allowed.\x1b[0m\n'
                                                'To specify permissions, run `deno repl` with allow flags.\n'}
