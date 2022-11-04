#!/bin/sh

mkdir -p /deploy/logs
touch /deploy/logs/error.log
touch /deploy/logs/access.log

exec gunicorn --preload --bind 0.0.0.0:5000 -w 10 -c ./gunicorn.conf.py app_server:app --timeout 90