from fastapi                                        import Request, Response
from osbot_fast_api.api.Fast_API                    import ENV_VAR__FAST_API__AUTH__API_KEY__NAME
from osbot_fast_api.api.routes.Routes__Set_Cookie   import Schema__Set_Cookie, Routes__Set_Cookie
from osbot_utils.type_safe.Type_Safe                import Type_Safe
from osbot_utils.utils.Env                          import get_env


class Hot_Patches(Type_Safe):

    def apply(self):
        self.add_missing_auth_routes()
        self.replace_method__set_auth_cookie()

    def add_missing_auth_routes(self):
        auth_paths = ['/auth/set-cookie-form']
        from osbot_fast_api.api.middlewares import Middleware__Check_API_Key
        for auth_path in auth_paths:
            assert auth_path not in Middleware__Check_API_Key.AUTH__EXCLUDED_PATHS
            Middleware__Check_API_Key.AUTH__EXCLUDED_PATHS.append(auth_path)

    def replace_method__set_auth_cookie(self):
        Routes__Set_Cookie.set_auth_cookie = self.set_auth_cookie

    def set_auth_cookie(self, set_cookie: Schema__Set_Cookie, request: Request, response: Response):  # Set the auth cookie via JSON request
        cookie_name = get_env(ENV_VAR__FAST_API__AUTH__API_KEY__NAME)
        secure_flag = request.url.scheme == 'https'
        response.set_cookie(key         = cookie_name            ,
                            value       = set_cookie.cookie_value,
                            httponly    = True                   ,
                            secure      = secure_flag            ,
                            samesite    ='strict'                )
        return {    "message"     : "Cookie set successfully",
                    "cookie_name" : cookie_name              ,
                    "cookie_value": set_cookie.cookie_value  }