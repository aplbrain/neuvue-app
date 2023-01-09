#!/usr/bin/python3

import subprocess
from sys import platform

# Turn debug mode on in settings.py
with open("neuvue/settings.py", "r") as f:
    settings = f.read()
    settings = settings.replace("DEBUG = False", "DEBUG = True")

with open("neuvue/settings.py", "w") as f:
    f.write(settings)

if platform == "win32":
    # Get recent migrations to database
    subprocess.run(["python", "manage.py", "migrate"], shell=True)

    # Collect static files
    subprocess.run(["python", "manage.py", "collectstatic", "--no-input"], shell=True)

    # Run Dev server on localhost
    subprocess.run(["python", "manage.py", "runserver", "localhost:8000"], shell=True)
else:
    # Get recent migrations to database
    subprocess.run(["python3", "manage.py", "migrate"])

    # Collect static files
    subprocess.run(["python3", "manage.py", "collectstatic", "--no-input"])

    # Run Dev server on localhost
    subprocess.run(["python3", "manage.py", "runserver", "localhost:8000"])
