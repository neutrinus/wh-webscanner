#!/bin/bash

if [ -f $PATH_TMPSCAN ]; then
    echo 'ustaw zmienna srodowiskowa PATH_TMPSCAN'
    exit 1
fi

find $PATH_TMPSCAN/* -mtime +60 -exec rm {} \;
