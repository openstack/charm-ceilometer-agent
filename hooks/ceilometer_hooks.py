#!/usr/bin/python

import sys
import os
import json
from charmhelpers.fetch import (
    apt_install, filter_installed_packages,
    apt_update
)
from charmhelpers.core.hookenv import (
    config,
    Hooks, UnregisteredHookError,
    log,
    local_unit,
    relation_set,
    relations_of_type,
)
from charmhelpers.core.host import (
    restart_on_change,
    lsb_release,
)
from charmhelpers.contrib.openstack.utils import (
    configure_installation_source,
    openstack_upgrade_available
)
from ceilometer_utils import (
    restart_map,
    services,
    register_configs,
    CEILOMETER_AGENT_PACKAGES,
    NOVA_SETTINGS,
    do_openstack_upgrade
)

from charmhelpers.contrib.charmsupport.nrpe import NRPE

hooks = Hooks()
CONFIGS = register_configs()


@hooks.hook()
def install():
    origin = config('openstack-origin')
    if (lsb_release()['DISTRIB_CODENAME'] == 'precise'
            and origin == 'distro'):
        origin = 'cloud:precise-grizzly'
    configure_installation_source(origin)
    apt_update(fatal=True)
    apt_install(
        filter_installed_packages(CEILOMETER_AGENT_PACKAGES),
        fatal=True)


@hooks.hook('nova-ceilometer-relation-joined')
def nova_ceilometer_joined():
    relation_set(subordinate_configuration=json.dumps(NOVA_SETTINGS))


@hooks.hook("ceilometer-service-relation-changed",
            "upgrade-charm")
@restart_on_change(restart_map())
def ceilometer_changed():
    CONFIGS.write_all()
    update_nrpe_config()


@hooks.hook('config-changed')
@restart_on_change(restart_map(), stopstart=True)
def config_changed():
    if openstack_upgrade_available('ceilometer-common'):
        do_openstack_upgrade(CONFIGS)
    update_nrpe_config()
    CONFIGS.write_all()


@hooks.hook('nrpe-external-master-relation-joined',
            'nrpe-external-master-relation-changed')
def update_nrpe_config():
    # Find out if nrpe set nagios_hostname
    hostname = None
    host_context = None
    for rel in relations_of_type('nrpe-external-master'):
        if 'nagios_hostname' in rel:
            hostname = rel['nagios_hostname']
            host_context = rel['nagios_host_context']
            break
    nrpe = NRPE(hostname=hostname)
    apt_install('python-dbus')

    if host_context:
        current_unit = "%s:%s" % (host_context, local_unit())
    else:
        current_unit = local_unit()

    services_to_monitor = services()

    for service in services_to_monitor:
        upstart_init = '/etc/init/%s.conf' % service
        sysv_init = '/etc/init.d/%s' % service

        if os.path.exists(upstart_init):
            nrpe.add_check(
                shortname=service,
                description='process check {%s}' % current_unit,
                check_cmd='check_upstart_job %s' % service,
                )
        elif os.path.exists(sysv_init):
            cronpath = '/etc/cron.d/nagios-service-check-%s' % service
            cron_template = '*/5 * * * * root \
/usr/local/lib/nagios/plugins/check_exit_status.pl -s /etc/init.d/%s \
status > /var/lib/nagios/service-check-%s.txt\n' % (service, service)
            f = open(cronpath, 'w')
            f.write(cron_template)
            f.close()
            nrpe.add_check(
                shortname=service,
                description='process check {%s}' % current_unit,
                check_cmd='check_status_file.py -f \
                    /var/lib/nagios/service-check-%s.txt' % service,
                )

    nrpe.write()


if __name__ == '__main__':
    try:
        hooks.execute(sys.argv)
    except UnregisteredHookError as e:
        log('Unknown hook {} - skipping.'.format(e))
