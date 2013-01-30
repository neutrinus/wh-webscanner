#!/bin/bash
pushd $(dirname $0)
supervisord
popd
