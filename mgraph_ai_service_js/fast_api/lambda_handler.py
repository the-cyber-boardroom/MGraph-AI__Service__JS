import os



if os.getenv('AWS_REGION'):  # only execute if we are not running inside an AWS Lambda function

    from osbot_aws.aws.lambda_.boto3__lambda import load_dependencies       # using the lightweight file (which only has the boto3 calls required to load_dependencies)
    from mgraph_ai_service_js.config         import LAMBDA_DEPENDENCIES__FAST_API_SERVERLESS
    load_dependencies(LAMBDA_DEPENDENCIES__FAST_API_SERVERLESS)

    def clear_osbot_modules():                            # todo: add this to load_dependencies method, since after it runs we don't need the osbot_aws.aws.lambda_.boto3__lambda
        import sys
        for module in list(sys.modules):
            if module.startswith('osbot_aws'):
                del sys.modules[module]

    clear_osbot_modules()

from mgraph_ai_service_js.fast_api.Service__Fast_API import Service__Fast_API

with Service__Fast_API() as _:
    _.setup()
    service_fast_api = _                                    # capture the Service__Fast_API object (useful for tests)
    handler          = _.handler()                          # capture the handler                  (needed by the run methods below)
    app              = _.app()                              # capture the app                      (needed by uvicorn executable)

def run(event, context=None):
    return handler(event, context)