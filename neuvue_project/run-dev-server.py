#!/usr/bin/python3

import subprocess

# Turn debug mode on in settings.py
with open('neuvue/settings.py', 'r') as f:
    settings = f.read()
    settings = settings.replace("DEBUG = False", "DEBUG = True")

with open('neuvue/settings.py', 'w') as f:
    f.write(settings)

# Get recent migrations to database
subprocess.run(['python3', 'manage.py', 'migrate'])

# Collect static files
subprocess.run(['python3', 'manage.py', 'collectstatic', '--no-input'])

# Run Dev server on localhost
subprocess.run(['python3', 'manage.py', 'runserver', 'localhost:8000'])
