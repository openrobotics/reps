#!/bin/bash
# Environment setup for OpenUSD v26.03+ tooling
# Set USD_INSTALL before sourcing, e.g.:
#   export USD_INSTALL=/path/to/openusd/install && source env.sh

if [ -z "${USD_INSTALL}" ]; then
    echo "ERROR: USD_INSTALL is not set. Point it to your OpenUSD install directory." >&2
    return 1 2>/dev/null || exit 1
fi

export PATH=${USD_INSTALL}/bin:${PATH}
export PYTHONPATH=${USD_INSTALL}/lib/python:${PYTHONPATH}
export LD_LIBRARY_PATH=${USD_INSTALL}/lib:${LD_LIBRARY_PATH}
