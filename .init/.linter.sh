#!/bin/bash
cd /home/kavia/workspace/code-generation/kindleplus-mobile-platform-40871-40880/backend_api
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

