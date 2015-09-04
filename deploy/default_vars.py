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

# Variables to use at your local machine
LOCAL_WORKSPACE = path.join(path.dirname(__file__), path.pardir)

#=================#
# The Apache user #
#=================#
APACHE = 'www-data'

#===================#
# Genkins variables #
#===================#
JENKINS = 'jenkins'
JENKINS_HOSTNAME = 'local.jenkins.sfl'

#=================#
# Aegir variables #
#=================#
AEGIR = 'aegir'
AEGIR_HOSTNAME = 'local.aegir.sfl'
PROJECT_NAME = 'aegir'
PROJECT_TYPE = 'drupal'
DOCKER_WORKSPACE = "/opt/"
DOCKER_PORT_TO_BIND = 8431
ROOT_PASS = ''
DB_USER = 'dev'
DB_PASS = 'dev'
DB_HOST = 'localhost'
