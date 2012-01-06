#!/bin/bash
. ~/guardier-scanner/py_env/bin/activate
pushd ~/guardier-scanner/gworker
./worker_filler.py >>../worker_filler.log 2>>../worker_filler.errorlog &
popd
