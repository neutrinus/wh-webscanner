#!/bin/bash
PROXY_PORT=1267
LOCAL_PORT=8000

ssh spinus.pl@176.9.151.163 \
    -i ~/.ssh/eskapizm.pl/spinus.pl \
    -p 8022 \
    -R $PROXY_PORT:localhost:$LOCAL_PORT \
    -N \
    $@
