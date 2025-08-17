#!/bin/bash

HOST="0.0.0.0"
PORT="10012"

uvicorn mgraph_ai_service_js.fast_api.lambda_handler:app \
  --reload     \
  --host $HOST \
  --port $PORT