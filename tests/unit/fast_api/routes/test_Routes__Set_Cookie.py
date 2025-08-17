from unittest                                import TestCase
from tests.unit.Service__Fast_API__Test_Objs import setup__service_fast_api_test_objs

class test_Routes__Set_Cookie(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        with setup__service_fast_api_test_objs() as _:
            cls.fast_api = _.fast_api
            cls.client   = _.fast_api__client

    def test__regression__auth_routes__did_not_have__auth_set_cookie_form(self):
        auth_path   = '/auth/set-cookie-form'
        #from osbot_fast_api.api.middlewares import Middleware__Check_API_Key
        #assert auth_path not in Middleware__Check_API_Key.AUTH__EXCLUDED_PATHS              # FIXED: BUG: auth path not in AUTH__EXCLUDED_PATHS list

        assert self.client.get('/docs'       ).status_code == 200
        #assert self.client.get(auth_path).status_code == 401                                # FIXED: BUG: which means we get a 401 here

        #Middleware__Check_API_Key.AUTH__EXCLUDED_PATHS.append(auth_path)                    # FIXED: BUG: if we add it manually to that list
        assert self.client.get(auth_path).status_code == 200                                 # FIXED: BUG: it will work
