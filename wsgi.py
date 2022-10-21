# This file contains the WSGI configuration required to serve up your
# web application at http://<your-username>.pythonanywhere.com/
# It works by setting the variable 'application' to a WSGI handler of some
# description.
#
# The below has been auto-generated for your Flask project

import sys
import os

###########################
# This must be changed by the actual project's home
project_home = '/home/fahernandez/comparison-interface'
###########################
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

os.chdir(project_home)

# import flask app but need to call it "application" for WSGI to work
from website import app as application  # noqa