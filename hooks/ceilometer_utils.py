import os
import uuid
from charmhelpers.fetch import apt_install as install

RABBIT_USER = "ceilometer"
RABBIT_VHOST = "ceilometer"
CEILOMETER_CONF = "/etc/ceilometer/ceilometer.conf"

SHARED_SECRET = "/etc/ceilometer/secret.txt"
CEILOMETER_SERVICES = [
    'ceilometer-agent-central', 'ceilometer-collector',
    'ceilometer-api'
]
CEILOMETER_DB = "ceilometer"
CEILOMETER_SERVICE = "ceilometer"
CEILOMETER_COMPUTE_SERVICES = ['ceilometer-agent-compute']
CEILOMETER_PACKAGES = [
    'python-ceilometer', 'ceilometer-common',
    'ceilometer-agent-central', 'ceilometer-collector', 'ceilometer-api'
]
CEILOMETER_AGENT_PACKAGES = [
    'python-ceilometer', 'ceilometer-common',
    'ceilometer-agent-compute'
]
CEILOMETER_PORT = 8777
CEILOMETER_ROLE = "ResellerAdmin"

NOVA_CONF = "/etc/nova/nova.conf"
NOVA_SETTINGS = [
    ('DEFAULT', 'instance_usage_audit', 'True'),
    ('DEFAULT', 'instance_usage_audit_period', 'hour'),
    ('DEFAULT', 'notification_driver', 'ceilometer.compute.nova_notifier')
]


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


TEMPLATES_DIR = 'templates'

try:
    import jinja2
except ImportError:
    install(['python-jinja2'])
    import jinja2


def render_template(template_name, context, template_dir=TEMPLATES_DIR):
    templates = \
        jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))
    template = templates.get_template(template_name)
    return template.render(context)
