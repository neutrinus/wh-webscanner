#!/bin/bash
. selenium_common.bash
cache_selenium


echo $PID $PARENT_PID
trap 'echo jobs: $(jobs -p)' EXIT
/usr/bin/xvfb-run -s "-screen 0 1280x1024x8" java -jar "$SELENIUM_EXECUTABLE" -role node -nodeConfig "$SELENIUM_CONFIG"
