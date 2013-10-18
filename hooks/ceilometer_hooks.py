#!/usr/bin/python

import sys
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
    restart_on_change
)
from charmhelpers.contrib.openstack.utils import (
    configure_installation_source
)
from ceilometer_utils import (
    restart_map,
    register_configs,
    CEILOMETER_AGENT_PACKAGES
)

hooks = Hooks()
CONFIGS = register_configs()


@hooks.hook()
def install():
    configure_installation_source(config('openstack-origin'))
    apt_update(fatal=True)
    apt_install(
        filter_installed_packages(CEILOMETER_AGENT_PACKAGES),
        fatal=True)

    # TODO(jamespage): Locally scoped relation for nova and others
    #ceilometer_utils.modify_config_file(ceilometer_utils.NOVA_CONF, 
    #    ceilometer_utils.NOVA_SETTINGS)


@hooks.hook("ceilometer-service-relation-changed")
@restart_on_change(restart_map())
def ceilometer_changed():
    CONFIGS.write_all()


if __name__ == '__main__':
    try:
        hooks.execute(sys.argv)
    except UnregisteredHookError as e:
        log('Unknown hook {} - skipping.'.format(e))
