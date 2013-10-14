#!/usr/bin/python

import sys
import os
import ceilometer_utils
from socket import gethostname as get_host_name

from charmhelpers.fetch import (
    apt_install, filter_installed_packages,
    apt_update
)

from charmhelpers.core.hookenv import (
    config,
    relation_ids,
    related_units,
    relation_get,
    Hooks, UnregisteredHookError,
    log
)
from charmhelpers.core.host import (
    service_restart
)

from charmhelpers.contrib.openstack.utils import configure_installation_source

hooks = Hooks()


@hooks.hook()
def install():
    configure_installation_source(config('openstack-origin'))
    apt_update(fatal=True)
    apt_install(filter_installed_packages(ceilometer_utils.CEILOMETER_AGENT_PACKAGES),
                fatal=True)

    # TODO(jamespage): Locally scoped relation for nova and others
    #ceilometer_utils.modify_config_file(ceilometer_utils.NOVA_CONF, 
    #    ceilometer_utils.NOVA_SETTINGS)


def get_conf():
    for relid in relation_ids('ceilometer-service'):
        for unit in related_units(relid):
            conf = {
                "rabbit_host": relation_get('rabbit_host', unit, relid),
                "rabbit_virtual_host": ceilometer_utils.RABBIT_VHOST,
                "rabbit_userid": ceilometer_utils.RABBIT_USER,
                "rabbit_password": relation_get('rabbit_password',
                                                unit, relid),
                "keystone_os_username": relation_get('keystone_os_username',
                                                     unit, relid),
                "keystone_os_password": relation_get('keystone_os_password',
                                                     unit, relid),
                "keystone_os_tenant": relation_get('keystone_os_tenant',
                                                   unit, relid),
                "keystone_host": relation_get('keystone_host', unit, relid),
                "keystone_port": relation_get('keystone_port', unit, relid),
                "metering_secret": relation_get('metering_secret', unit, relid)
            }
            if None not in conf.itervalues():
                return conf
    return None


def render_ceilometer_conf(context):
    if (context and os.path.exists(ceilometer_utils.CEILOMETER_CONF)):
        context['service_port'] = ceilometer_utils.CEILOMETER_PORT
        context['ceilometer_host'] = get_host_name()

        with open(ceilometer_utils.CEILOMETER_CONF, "w") as conf:
            conf.write(ceilometer_utils.render_template(
                os.path.basename(ceilometer_utils.CEILOMETER_CONF), context))

        for svc in ceilometer_utils.CEILOMETER_COMPUTE_SERVICES:
            service_restart(svc)
        return True
    return False


@hooks.hook("ceilometer-service-relation-changed")
def ceilometer_changed():
    # check if we have rabbit and keystone already set
    context = get_conf()
    if context:
        render_ceilometer_conf(context)
    else:
        # still waiting
        log("ceilometer: rabbit and keystone "
            "credentials not yet received from peer.")


if __name__ == '__main__':
    try:
        hooks.execute(sys.argv)
    except UnregisteredHookError as e:
        log('Unknown hook {} - skipping.'.format(e))
