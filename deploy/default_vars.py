#********************************
# WARNING WARNING WARNING
#********************************

# YOU MUST NOT MODIFY THIS FILE!

# If you need to override the values of the variables defined in this file you should
# Copy and paste this file with the name local_vars.py and set your values there.

# When you create a file local_vars.py and define the values there, the fabfile.py file will use
# your values and not the values defined in this file.


#********************************
# END WARNING
#********************************

from os import path

# The Apache user
APACHE = 'www-data'

# The Aegir user
AEGIR = 'aegir'
# The Genkins user
JENKINS = 'jenkins'

# Variables to use at your local machine
LOCAL_WORKSPACE = path.join(path.dirname(__file__), path.pardir)


# Variables to use inside the docker container
DOCKER_WORKSPACE = "/opt/"
DOCKER_PORT_TO_BIND = 8431

# Aegir hostname
AEGIR_HOSTNAME = 'local.aegir.sfl'

# Projects variables
PROJECT_NAME = 'aegir'
PROJECT_TYPE = 'drupal'

# Database variables
ROOT_PASS = ''
DB_USER = 'dev'
DB_PASS = 'dev'
DB_HOST = 'localhost'
