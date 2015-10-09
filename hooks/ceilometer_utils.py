from charmhelpers.contrib.openstack import (
    templating,
)
from ceilometer_contexts import (
    CeilometerServiceContext
)
from charmhelpers.contrib.openstack.utils import (
    get_os_codename_package,
    get_os_codename_install_source,
    configure_installation_source
)
from charmhelpers.core.hookenv import (
    config,
    log,
)
from charmhelpers.fetch import apt_update, apt_install, apt_upgrade

CEILOMETER_CONF_DIR = "/etc/ceilometer"
CEILOMETER_CONF = "%s/ceilometer.conf" % CEILOMETER_CONF_DIR

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
                    ('notify_on_state_change', 'vm_and_task_state'),
                    ('notification_driver',
                     'ceilometer.compute.nova_notifier'),
                    ('notification_driver',
                     'nova.openstack.common.notifier.rpc_notifier')
                ]
            }
        }
    }
}

CONFIG_FILES = {
    CEILOMETER_CONF: {
        'hook_contexts': [
            CeilometerServiceContext(ssl_dir=CEILOMETER_CONF_DIR)],
        'services': CEILOMETER_AGENT_SERVICES
    }
}

TEMPLATES = 'templates'

REQUIRED_INTERFACES = {
    'ceilometer': ['ceilometer-service'],
}


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
        or 'icehouse'
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


def services():
    ''' Returns a list of services associate with this charm '''
    _services = []
    for v in restart_map().values():
        _services = _services + v
    return list(set(_services))


def do_openstack_upgrade(configs):
    """
    Perform an upgrade.  Takes care of upgrading packages, rewriting
    configs, database migrations and potentially any other post-upgrade
    actions.

    :param configs: The charms main OSConfigRenderer object.
    """
    new_src = config('openstack-origin')
    new_os_rel = get_os_codename_install_source(new_src)

    log('Performing OpenStack upgrade to %s.' % (new_os_rel))

    configure_installation_source(new_src)
    dpkg_opts = [
        '--option', 'Dpkg::Options::=--force-confnew',
        '--option', 'Dpkg::Options::=--force-confdef',
    ]
    apt_update(fatal=True)
    apt_upgrade(options=dpkg_opts, fatal=True, dist=True)
    apt_install(packages=CEILOMETER_AGENT_PACKAGES,
                options=dpkg_opts,
                fatal=True)

    # set CONFIGS to load templates from new release
    configs.set_release(openstack_release=new_os_rel)
