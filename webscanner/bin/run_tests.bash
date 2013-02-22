#!/bin/bash
WEBSCANNER_ENVIRONMENT=test DJANGO_SETTINGS_MODULE=webscanner.settings py.test "$@"
