#!/usr/bin/env bash

# stop the script if any command fails
set -ex

# install using pip into the conda build environment prefix
$PYTHON -m pip install . --no-deps --no-build-isolation -vv

