#!/bin/bash
PY=$(readlink -f `dirname $0`)/../py_env #katalog glowny
echo "PY ENV = $PY"
if [ ! -e "$PY" ];then
    virtualenv "$PY"
fi
. "$PY"/bin/activate
pip install -r "$PY/../requirements.txt"
