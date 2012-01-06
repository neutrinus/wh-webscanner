#!/bin/bash
HERE=$(readlink -f $(dirname $0))

rm $HERE/../gpanel/*sqlite3
$HERE/../gpanel/manage.py syncdb --noinput
