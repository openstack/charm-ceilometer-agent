import os
import uuid
import ConfigParser

RABBIT_USER = "ceilometer"
RABBIT_VHOST = "ceilometer"
CEILOMETER_CONF = "/etc/ceilometer/ceilometer.conf"

SHARED_SECRET = "/etc/ceilometer/secret.txt"
CEILOMETER_SERVICES = ['ceilometer-agent-central', 'ceilometer-collector',
    'ceilometer-api']
CEILOMETER_DB = "ceilometer"
CEILOMETER_SERVICE = "ceilometer"
CEILOMETER_COMPUTE_SERVICES = ['ceilometer-agent-compute']
CEILOMETER_PACKAGES = ['python-ceilometer', 'ceilometer-common',
    'ceilometer-agent-central', 'ceilometer-collector', 'ceilometer-api']
CEILOMETER_AGENT_PACKAGES = ['python-ceilometer', 'ceilometer-common',
    'ceilometer-agent-compute']
CEILOMETER_PORT = 8777

NOVA_CONF = "/etc/nova/nova.conf"
NOVA_SETTINGS = [
    ('DEFAULT', 'instance_usage_audit', 'True'),
    ('DEFAULT', 'instance_usage_audit_period', 'hour'),
    ('DEFAULT', 'notification_driver', 'ceilometer.compute.nova_notifier')]


def get_shared_secret():
    secret = None
    if not os.path.exists(SHARED_SECRET):
        secret = str(uuid.uuid4())
        with open(SHARED_SECRET, 'w') as secret_file:
            secret_file.write(secret)
    else:
        with open(SHARED_SECRET, 'r') as secret_file:
            secret = secret_file.read().strip()
    return secret


def modify_config_file(nova_conf, values):
    # check if config file exists
    if not os.path.exists(nova_conf):
        juju_log('ERROR', 'nova config file must exist at this point')
        sys.exit(1)

    try:
        config = ConfigParser.ConfigParser()
        with open(nova_conf, "r") as f:
            config.readfp(f)

        # add needed config lines - tuple with section,key,value
        for value in values:
            config.set(value[0], value[1], value[2])

        with open(nova_conf, "w") as f:
            config.write(f)

        # add line at the end, it's a dupe and configparser doesn't handle it
        with open(nova_conf, "a") as f:
            f.write("notification_driver=nova.openstack.common.notifier.rabbit_notifier\n")

    except IOError as e:
        juju_log('ERROR', 'Error updating nova config file')
        sys.exit(1)
