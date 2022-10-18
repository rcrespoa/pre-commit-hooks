#!/bin/sh
SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
ENV_PATH=$SCRIPT_PATH/env
ROOT_PATH=$SCRIPT_PATH/..

############################################################################
# Set up main VENV
############################################################################
python3 -m venv $ENV_PATH
source $ENV_PATH/bin/activate
pip3 install -r $SCRIPT_PATH/dev-tools-requirements.txt

############################################################################
# Set up pre-commit hooks
############################################################################
pre-commit install