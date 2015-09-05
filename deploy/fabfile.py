# coding: utf-8
#
# Copyright (C) 2014 Savoir-faire Linux Inc. (<www.savoirfairelinux.com>).
#
# This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import unicode_literals
from getpass import getuser
from fabric.api import lcd, cd, task, roles, env, local, run, runs_once, execute
from fabric.colors import red, green
from fabric.contrib.files import exists
from fabric.contrib.console import confirm

# Import socket to find the localhost IP address
import socket

# Import default variables
from default_vars import *

# Import local variables' overrides, if they exist
if path.exists(path.join(path.dirname(__file__), 'local_vars.py')):
    from local_vars import *


# Function to manage differents users, hosts, roles, and variables  #
#####################################################################
# Get info of the current user and host
user_name = getuser()
host_name = local("hostname", capture=True)

# Set the env dict with the roles and the hosts
env.roledefs['local'] = ["{}@{}".format(user_name, host_name)]
env.roledefs['docker'] = ["root@{}".format(AEGIR_HOSTNAME)]
env.roledefs['dk_aegir'] = ["aegir@{}".format(AEGIR_HOSTNAME)]

# Flag to use for install the site with or without translations
LOCALE = False

# The CONTAINER_IP will be set at the creation of the container, see @task docker_run_container
CONTAINER_IP = None


def set_env(role):
    """
    Helper function to set the correct values of the global variables in function of the role
    :param role: the role to use for define the host
    :return:
    """
    global WORKSPACE
    WORKSPACE = {
        'local': LOCAL_WORKSPACE,
        'docker': DOCKER_WORKSPACE,
        'dk_aegir': DOCKER_WORKSPACE
    }[role]

    # global APP_ROOT
    # APP_ROOT = {
    #     'local': LOCAL_APP_ROOT,
    #     'docker': DOCKER_APP_ROOT
    # }[role]

    global DOCKER_IFACE_IP
    DOCKER_IFACE_IP = None
    if CONTAINER_IP:
        DOCKER_IFACE_IP = [(s.connect((CONTAINER_IP, 80)), s.getsockname()[0], s.close())
                           for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]


def fab_run(role="local", cmd="", capture=False):
    """
    Helper function to run the task locally or remotely
    :param role: the role to use for define the host
    :param cmd: the command to execute
    :param capture: if it should return or not the output of the command
    :return: the function to execute the command locally or remotely
    """
    if role == "local":
        return local(cmd, capture)
    else:
        return run(cmd)


def fab_cd(role, directory):
    """
    Helper function to manage the context locally or remotely
    :param role: the role to use for define the host
    :param directory: the directory of context
    :return: the function to manage the context locally or remotely
    """
    if role == "local":
        return lcd(directory)
    else:
        return cd(directory)


def fab_exists(role, directory):
    """
    Herlper function to check if a directory exist locally or remotely
    :param role: the role to use for define the host.
    :param directory: the directory to check
    :return: the function for check the existence of the directory locally or remotely
    """
    if role == "local":
        return path.exists(directory)
    else:
        return exists(directory)


def fab_add_to_hosts(ip, site_hostname):
    """
    Helper function to add the ip and hostname to /etc/hosts
    :param ip:
    :param site_hostname:
    :return:
    """
    if confirm(green('Do you want add to the /etc/hosts the line "{}    {}"? '
                     'If you say yes you will be able to visit the site using a more frienldy url '
                     '"http://{}".'.format(ip, site_hostname, site_hostname))):
        # Add if not find the comment "# Docker auto-added host" to the file /etc/hosts
        local(
            'grep "# Docker auto-added host" /etc/hosts > /dev/null || '
            'sudo sed -i "$ a # Docker auto-added host" /etc/hosts')

        # Add the ip address and hostname after the comment "# Docker auto-added host"
        local('sudo sed -i "/# Docker auto-added host/i\{}     {}" /etc/hosts'.format(ip, site_hostname))


def fab_remove_from_hosts(site_hostname):
    """
    Helper function to remove the ip  and the hostname to /etc/hosts
    :param site_hostname:
    :return:
    """
    print(green('Enter your password to remove the {} from your /etc/hosts file'.format(site_hostname)))
    local('sudo sed -i "/{}/d" /etc/hosts'.format(site_hostname))


def fab_update_hosts(ip, site_hostname):
    """
    Helper function to update the file /etc/hosts
    :param ip:
    :param site_hostname:
    :return:
    """
    fab_remove_from_hosts(site_hostname)
    fab_add_to_hosts(ip, site_hostname)


# Helper functions to manage docker images and containers #
###########################################################

def docker_ps(running_only=False):
    args = '' if running_only else '-a'
    result = local('docker ps {}'.format(args), capture=True)
    lines = result.stdout.splitlines()
    # container name is supposed to be the last column
    assert lines[0].strip().endswith('NAMES')
    return [line.strip().split(' ')[-1] for line in lines[1:]]


def docker_tryrun(imgname, containername=None, opts='', mounts=None, cmd='', restart=True):
    # mounts is a list of (from, to, canwrite) path tuples. ``from`` is relative to the project root.
    # Returns True if the container was effectively ran (false if it was restarted or aborted)
    if not mounts:
        mounts = []
    if containername and containername in docker_ps(running_only=True):
        print green("{} already running".format(containername))
        return False
    if containername and containername in docker_ps(running_only=False):
        if restart:
            print green("{} already exists and is stopped. Restarting!".format(containername))
            local('docker restart {}'.format(containername))
            return True
        else:
            print red("There's a dangling container {}! That's not supposed to happen. Aborting".format(containername))
            print "Run 'docker rm {}' to remove that container".format(containername)
            return False
    for from_path, to_path, canwrite in mounts:
        abspath = from_path
        opt = ' -v {}:{}'.format(abspath, to_path)
        if not canwrite:
            opt += ':ro'
        opts += opt
    if containername:
        containername_opt = '-h {} --name {}'.format(containername, containername)
    else:
        containername_opt = ''
    local('docker run {} {} {} {}'.format(opts, containername_opt, imgname, cmd))
    return True


def docker_ensureruns(containername):
    # Makes sure that containername runs. If it doesn't, try restarting it. If the container
    # doesn't exist, spew an error.
    if containername not in docker_ps(running_only=True):
        if containername in docker_ps(running_only=False):
            local('docker restart {}'.format(containername))
            return True
        else:
            return False
    else:
        return True


def docker_ensure_data_container(containername, volume_paths=None, base_image='busybox'):
    # Make sure that we have our data containers running. Data containers are *never* removed.
    # Their only purpose is to hold volume data.
    # Returns whether a container was created by this call
    if containername not in docker_ps(running_only=False):
        if volume_paths:
            volume_args = ' '.join('-v %s' % volpath for volpath in volume_paths)
        else:
            volume_args = ''
        local('docker create %s --name %s %s' % (volume_args, containername, base_image))
        return True
    return False


def docker_isrunning(containername):
    # Check if the containername is running.
    if containername not in docker_ps(running_only=True):
        return False
    else:
        return True


def docker_images():
    result = local('docker images', capture=True)
    lines = result.stdout.splitlines()
    # image name is supposed to be the first column
    assert lines[0].strip().startswith('REPOSITORY')
    return [line.strip().split(' ')[0] for line in lines]


# Task to manage docker's images and containers generally in the localhost#
###########################################################################

@task(alias='icreate')
@roles('local')
def docker_create_image(role='local'):
    """
    Create docker images
    """
    set_env(role)
    with fab_cd(role, WORKSPACE):
        if '{}/{}'.format(PROJECT_NAME, PROJECT_TYPE) in docker_images():
            print(red('Docker image {}/{} was found, you has already build this image'.format(PROJECT_NAME,
                                                                                              PROJECT_TYPE)))
        else:
            fab_run(role, 'docker build -t {}/{} .'.format(PROJECT_NAME, PROJECT_TYPE))
            print(green('Docker image {}/{} was build successful'.format(PROJECT_NAME, PROJECT_TYPE)))


@task(alias='crun')
@roles('local')
def docker_run_container(role='local'):
    """
    Run docker containers
    """
    set_env(role)
    with fab_cd(role, WORKSPACE):
        if '{}/{}'.format(PROJECT_NAME, PROJECT_TYPE) in docker_images():
            if docker_tryrun('{}/{}'.format(PROJECT_NAME, PROJECT_TYPE),
                             '{}_container'.format(PROJECT_NAME),
                             '-d -p {}:80'.format(DOCKER_PORT_TO_BIND),
                             mounts=[(WORKSPACE, DOCKER_WORKSPACE, True)]):
                # If container was successful build, get the IP address and show it to the user.
                ip = fab_run(role, 'docker inspect -f "{{{{.NetworkSettings.IPAddress}}}}" '
                                   '{}_container'.format(PROJECT_NAME), capture=True)
                fab_update_hosts(ip, AEGIR_HOSTNAME)
                print(green('Docker container {}_container was build successful. '
                            'To visit the Website open a web browser in http://{} or '
                            'http://localhost:{}.'.format(PROJECT_NAME, AEGIR_HOSTNAME, DOCKER_PORT_TO_BIND)))

        else:
            print(red('Docker image {}/{} not found and is a requirement to run the {}_container.'
                      'Please, run first "fab create" in order to build the {}/{} '
                      'image'.format(PROJECT_NAME, PROJECT_TYPE, PROJECT_NAME, PROJECT_NAME, PROJECT_TYPE)))


@task(alias='cstop')
@roles('local')
def docker_stop_container(role='local'):
    """
    Stop docker containers
    """
    set_env(role)
    with fab_cd(role, WORKSPACE):
        if '{}_container'.format(PROJECT_NAME) in docker_ps():
            fab_remove_from_hosts(AEGIR_HOSTNAME)
            fab_run(role, 'docker stop {}_container'.format(PROJECT_NAME))
            print(green('Docker container {}_container was successful stopped'.format(PROJECT_NAME)))
        else:
            print(red('Docker container {}_container was not running or paused'.format(PROJECT_NAME)))


@task(alias='cremove')
@roles('local')
def docker_remove_container(role='local'):
    """
    Stop docker containers
    """
    set_env(role)
    with fab_cd(role, WORKSPACE):
        if '{}_container'.format(PROJECT_NAME) in docker_ps():
            fab_remove_from_hosts(AEGIR_HOSTNAME)
            fab_run(role, 'docker rm -f {}_container'.format(PROJECT_NAME))
            print(green('Docker container {}_container was successful removed'.format(PROJECT_NAME)))
        else:
            print(red('Docker container {}_container was already removed'.format(PROJECT_NAME)))


@task(alias='iremove')
@roles('local')
def docker_remove_image(role='local'):
    """
    Remove docker container and images
    """
    set_env(role)
    with fab_cd(role, WORKSPACE):
        if docker_isrunning('{}_container'.format(PROJECT_NAME)):
            print(red('Docker container {}_container is running, '
                      'you should stopped it after remove the image {}/{}'.format(PROJECT_NAME, PROJECT_NAME,
                                                                                  PROJECT_TYPE)))
        if '{}/{}'.format(PROJECT_NAME, PROJECT_TYPE) in docker_images():
            fab_run(role, 'docker rmi -f {}/{}'.format(PROJECT_NAME, PROJECT_TYPE))
            # Remove dangling docker images to free space.
            if '<none>' in docker_images():
                fab_run(role, 'docker images --filter="dangling=true" -q | xargs docker rmi -f')
            print(green('Docker image {}/{} was successful removed'.format(PROJECT_NAME, PROJECT_TYPE)))
        else:
            print(red('Docker image {}/{} was not found'.format(PROJECT_NAME, PROJECT_TYPE)))


@task(alias='connect')
@roles('local')
def docker_connect(role='local'):
    """
    Connect to a docker container using "docker -it exec <name> bash".
    This is a better way to connect to the container than using ssh'
    """
    set_env(role)
    with fab_cd(role, WORKSPACE):
        if docker_isrunning('{}_container'.format(PROJECT_NAME)):
            fab_run(role, 'docker exec -it {}_container bash'.format(PROJECT_NAME))
        else:
            print(red('Docker container {}_container is not running, it should be running to be able to connect.'))


@task(alias='ssh')
@roles('local')
def docker_ssh(role='local', path_key='~/.ssh/id_rsa'):
    """
    Connect to a docker container through ssh protocol using you private key that should be in '~/.ssh/id_rsa'
    """
    set_env(role)
    ip = fab_run(role, 'docker inspect -f "{{{{.NetworkSettings.IPAddress}}}}" {}_container'.format(PROJECT_NAME),
                 capture=True)
    if ip:
        fab_run(role, 'ssh -i {} root@{}'.format(path_key, ip))


@task(alias='dkuh')
@roles('docker')
def docker_update_host():
    """
    Helper function to update the ip and hostname in docker container
    # Fix complains of sendmail about "unable to qualify my own domain name"
    :return:
    """
    # Get the ip of the container, this
    ip = local('docker inspect -f "{{{{.NetworkSettings.IPAddress}}}}" {}_container'.format(PROJECT_NAME), capture=True)
    run("sed  '/{}/c\{} {} {}_container localhost localhost.domainlocal' "
        "/etc/hosts > /root/hosts.backup".format(ip, ip, AEGIR_HOSTNAME, PROJECT_NAME))
    run("cat /root/hosts.backup > /etc/hosts")


@task(alias='cp_keys')
@roles('local')
def copy_ssh_keys(role='local', ):
    """
    Copy your ssh keys to use it in the docker container to clone git projects and to connect to it using ssh protocol
    """
    set_env(role)
    copy = True
    if fab_exists(role, '{}/deploy/id_rsa.pub'.format(WORKSPACE)):
        if confirm(red('There is a SSH public key in your deploy directory Say [Y] to keep this key, say [n] to '
                       'overwrite the key')):
            copy = False

    with fab_cd(role, WORKSPACE):
        if copy:
            fab_run(role, 'cp ~/.ssh/id_rsa.pub deploy/')
            print(green('SSH public key copied successful'))
        else:
            print(red('Keeping the existing SSH public key'))


@task(alias='cau')
@roles('docker')
def create_aegir_user(role='docker'):
    """
    Create the Aegir user
    The same that run: $ fab cau
    """
    set_env(role)
    # Create aegir dir and Setup ssh keys to use fabric
    fab_run(role, 'mkdir /var/aegir')
    fab_run(role, 'mkdir /var/aegir/.ssh')
    fab_run(role, 'cp /opt/deploy/id_rsa* /var/aegir/.ssh')
    fab_run(role, 'cat /root/.ssh/id_rsa.pub >> /var/aegir/.ssh/authorized_keys')
    fab_run(role, 'chmod 600 /var/aegir/.ssh/id_rsa*')
    fab_run(role, 'adduser --system --group --home /var/aegir --shell /bin/bash aegir')
    fab_run(role, 'chown -R aegir:aegir /var/aegir')
    fab_run(role, 'passwd aegir')
    fab_run(role, 'adduser aegir www-data')
    fab_run(role, 'a2enmod rewrite')


@task(alias='websc')
@roles('docker')
def webserver_config(role='docker'):
    """
    Webserver configuration
    The same that run: $ fab websc
    """
    set_env(role)
    fab_run(role, 'ln -s /var/aegir/config/apache.conf /etc/apache2/conf-available/aegir.conf')


@task(alias='phpc')
@roles('docker')
def php_config(role='docker'):
    """
    PHP configuration
    The same that run: $ fab phpc
    """
    set_env(role)
    fab_run(role, 'sudo sed -i "s@memory_limit = 128M@memory_limit = 512M@g" /etc/php5/cli/php.ini')
    fab_run(role, 'sudo sed -i "s@memory_limit = 128M@memory_limit = 512M@g" /etc/php5/apache2/php.ini')


@task(alias='sudoc')
@roles('docker')
def sudo_config(role='docker'):
    """
    Sudo configuration
    The same that run: $ fab sudoc
    """
    set_env(role)
    fab_run(role, 'touch /etc/sudoers.d/aegir')
    fab_run(role, 'echo "Defaults:aegir  !requiretty" > /etc/sudoers.d/aegir')
    fab_run(role, 'echo "aegir ALL=NOPASSWD: /usr/sbin/apache2ctl" > /etc/sudoers.d/aegir')


@task(alias='dbc')
@roles('docker')
def database_config(role='docker'):
    """
    Database configuration
    The same that run: $ fab dbc
    """
    set_env(role)
    fab_run(role, 'mysql -uroot -e "GRANT ALL PRIVILEGES ON *.* TO \'{}\'@\'%\' '
                  'IDENTIFIED BY \'{}\'; FLUSH PRIVILEGES;"'.format(DB_USER, DB_PASS))
    fab_run(role, 'mysql_secure_installation')


@task(alias='iac')
@roles('dk_aegir')
def install_aegir_components(role='dk_aegir'):
    """
    Install Aegir components
    The same that run: $ fab iac
    """
    set_env(role)
    fab_run(role, 'ls')
    fab_run(role, 'drush dl provision-7.x')
    fab_run(role, 'drush cc drush')
    fab_run(role, 'drush hostmaster-install')


@task(alias='eac')
@roles('docker')
def enable_aegir_conf(role='docker'):
    """
    Enable Aegir configuration
    The same that run: $ fab eac
    """
    set_env(role)
    fab_run(role, 'a2enconf aegir')
    fab_run(role, 'service apache2 reload')


@task(alias='cju')
@roles('docker')
def create_jenkins_user(role='docker'):
    """
    Create the Jenkins user
    The same that run: $ fab cju
    """
    set_env(role)
    # Create aegir dir and Setup ssh keys to use fabric
    fab_run(role, 'adduser --system --group --shell /bin/bash jenkins')
    fab_run(role, 'passwd jenkins')
    fab_run(role, 'adduser jenkins www-data')
    fab_run(role, 'adduser jenkins aegir')


@task(alias='cju')
@roles('local')
def get_aegir_host_ip(role='local'):
    """
    Create the Jenkins user
    The same that run: $ fab cju
    """
    set_env(role)
    ip = fab_run(role, 'docker inspect -f "{{{{.NetworkSettings.IPAddress}}}}" {}_container'.format(PROJECT_NAME),
            capture=True)
    print ip


@task(alias='rjc')
@roles('local')
def run_jenkins_container(role='local'):
    """
    Create the Jenkins user
    The same that run: $ fab cju
    """
    set_env(role)
    # Change permision in jenkins_home dir and run the container using the official image
    fab_run(role, 'sudo chmod -R 777 {}/jenkins_home'.format(WORKSPACE))
    fab_run(role, 'docker run -p 50000:50000 -v {}/jenkins_home:/var/jenkins_home -h {} --name jenkins_container '
                  'jenkins'.format(WORKSPACE, JENKINS_HOSTNAME))


@task(alias='srjc')
@roles('local')
def stop_remove_jenkins_container(role='local'):
    """
    Create the Jenkins user
    The same that run: $ fab cju
    """
    set_env(role)
    # Create aegir dir and Setup ssh keys to use fabric
    fab_run(role, 'docker stop jenkins_container && docker rm jenkins_container')


@task(alias='ajh')
@roles('local')
def add_jenkins_host(role='local'):
    """
    Create the Jenkins user
    The same that run: $ fab cju
    """
    ip = fab_run(role, 'docker inspect -f "{{{{.NetworkSettings.IPAddress}}}}" jenkins_container'.format(PROJECT_NAME),
            capture=True)
    fab_update_hosts(ip, JENKINS_HOSTNAME)
    print(green('Now you can visit your the site at http://{}:8080'.format(JENKINS_HOSTNAME)))


@task(alias='ds')
@runs_once
def docker_setup():
    """
    Complete docker setup process, used generally when building the docker image for install and configure Aegir.
    The same that run: $ fab
    """
    execute(copy_ssh_keys)
    execute(docker_create_image)
    execute(docker_run_container)
    execute(docker_update_host)
    execute(create_aegir_user)
    execute(webserver_config)
    execute(php_config)
    execute(sudo_config)
    execute(database_config)
    execute(install_aegir_components)
    execute(enable_aegir_conf)
    execute(create_jenkins_user)
    execute(run_jenkins_container)
    print green('Docker setup finished with success!')
