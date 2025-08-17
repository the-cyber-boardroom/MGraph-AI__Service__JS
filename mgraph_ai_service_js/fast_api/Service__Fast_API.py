from osbot_fast_api.api.routes.Routes__Set_Cookie                     import Routes__Set_Cookie
from osbot_fast_api_serverless.fast_api.Serverless__Fast_API          import Serverless__Fast_API
from mgraph_ai_service_js.config                                      import FAST_API__TITLE
from mgraph_ai_service_js.fast_api.Hot_Patches                        import Hot_Patches
from mgraph_ai_service_js.fast_api.routes.Routes__Info                import Routes__Info
from mgraph_ai_service_js.fast_api.routes.Routes__JS__Execute         import Routes__JS__Execute
from mgraph_ai_service_js.fast_api.routes.Routes__JS__Module__Execute import Routes__JS__Module__Execute
from mgraph_ai_service_js.utils.Version                               import version__mgraph_ai_service_js


class Service__Fast_API(Serverless__Fast_API):

    def fast_api__title(self):                                                    # Service title
        return FAST_API__TITLE

    def setup(self):                                                              # Initialize service
        self.apply_hot_fixes()
        super().setup()
        self.setup_fast_api_title_and_version()
        return self

    def setup_fast_api_title_and_version(self):                                  # Configure API metadata
        app         = self.app()
        app.title   = self.fast_api__title()
        app.version = version__mgraph_ai_service_js

        # Update description to reflect JS execution capability
        app.description = """
MGraph-AI Service for secure JavaScript code execution.

This service provides a sandboxed environment for executing JavaScript code
using the Deno runtime with configurable security permissions and resource limits.

Features:
- Secure sandboxed execution
- Configurable permissions (file, network, environment)
- Resource limits (time, memory, output size)
- Syntax validation
- JSON input/output support
        """
        return self

    def setup_routes(self):                                                       # Configure API routes
        self.add_routes(Routes__Info               )
        self.add_routes(Routes__Set_Cookie         )
        self.add_routes(Routes__JS__Execute        )
        self.add_routes(Routes__JS__Module__Execute)

    def apply_hot_fixes(self):                                                   # Apply necessary patches
        Hot_Patches().apply()
        return self