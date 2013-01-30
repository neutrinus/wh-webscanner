#!/bin/bash
#trap 'kill 0' EXIT SIGINT SIGTERM
. selenium_common.bash
cache_selenium

java -jar "$SELENIUM_EXECUTABLE" -role hub -host localhost
