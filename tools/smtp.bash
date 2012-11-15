#!/bin/bash
python -m smtpd -n -c DebuggingServer localhost:1025
#./../webscanner/manage.py mail_debug 1025
