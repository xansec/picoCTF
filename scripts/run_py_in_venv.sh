#!/bin/bash

# Utility wrapper to allow ansible-playbooks to run a script within a
# specified virtual environment.

set -e

VENV=$1
CMD=$2
ARGS=${@:3}

echo "Running \`python ${CMD}\` in virtualenv:${VENV}"
echo "args: ${ARGS}"

source ${VENV}/bin/activate
python ${CMD} ${ARGS}
