from unittest import TestCase

from osbot_utils.helpers.duration.decorators.print_duration import print_duration
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