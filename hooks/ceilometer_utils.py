from charmhelpers.contrib.openstack import (
    templating,
)
from ceilometer_contexts import (
    CeilometerServiceContext
)
from charmhelpers.contrib.openstack.utils import (
    get_os_codename_package
)

CEILOMETER_CONF = "/etc/ceilometer/ceilometer.conf"

CEILOMETER_AGENT_SERVICES = ['ceilometer-agent-compute']

CEILOMETER_AGENT_PACKAGES = [
    'python-ceilometer', 'ceilometer-common',
    'ceilometer-agent-compute'
]

NOVA_CONF = "/etc/nova/nova.conf"

NOVA_SETTINGS = {
    "nova": {
        "/etc/nova/nova.conf": {
            "sections": {
                "DEFAULT": [
                    ('instance_usage_audit', 'True'),
                    ('instance_usage_audit_period', 'hour'),
                    ('notification_driver', 'ceilometer.compute.nova_notifier')
                ]
            }
        }
    }
}

CONFIG_FILES = {
    CEILOMETER_CONF: {
        'hook_contexts': [CeilometerServiceContext()],
        'services': CEILOMETER_AGENT_SERVICES
    }
}

TEMPLATES = 'templates'


def register_configs():
    """
    Register config files with their respective contexts.
    Regstration of some configs may not be required depending on
    existing of certain relations.
    """
    # if called without anything installed (eg during install hook)
    # just default to earliest supported release. configs dont get touched
    # till post-install, anyway.
    release = get_os_codename_package('ceilometer-common', fatal=False) \
        or 'grizzly'
    configs = templating.OSConfigRenderer(templates_dir=TEMPLATES,
                                          openstack_release=release)

    for conf in CONFIG_FILES:
        configs.register(conf, CONFIG_FILES[conf]['hook_contexts'])

    return configs


def restart_map():
    '''
    Determine the correct resource map to be passed to
    charmhelpers.core.restart_on_change() based on the services configured.

    :returns: dict: A dictionary mapping config file to lists of services
                    that should be restarted when file changes.
    '''
    _map = {}
    for f, ctxt in CONFIG_FILES.iteritems():
        svcs = []
        for svc in ctxt['services']:
            svcs.append(svc)
        if svcs:
            _map[f] = svcs
    return _map
