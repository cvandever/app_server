#!/bin/bash

python3 -m gunicorn -b 0.0.0.0:5000 -w 2 -t 2 wsgi:app