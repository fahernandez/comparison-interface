# This file contains the WSGI configuration required to serve up your
# web application.
# It works by setting the variable 'application' to a WSGI handler of some
# description.

import sys
import os

###########################
# This must be changed by the actual project's home absolute path
project_home = '{{project_home}}' # noqa
###########################
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

os.chdir(project_home)

# This import style will allow the project being deployed in PythonEveryWhere
from website import app as application # noqa
