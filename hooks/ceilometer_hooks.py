#!/usr/bin/python

import sys
import json
from charmhelpers.fetch import (
    apt_install, filter_installed_packages,
    apt_update
)
from charmhelpers.core.hookenv import (
    config,
    Hooks, UnregisteredHookError,
    log,
    relation_set
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
    CEILOMETER_AGENT_PACKAGES,
    NOVA_SETTINGS
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


@hooks.hook('nova-ceilometer-relation-joined')
def nova_ceilometer_joined():
    relation_set(subordinate_configuration=json.dumps(NOVA_SETTINGS))


@hooks.hook("ceilometer-service-relation-changed",
            "upgrade-charm")
@restart_on_change(restart_map())
def ceilometer_changed():
    CONFIGS.write_all()


if __name__ == '__main__':
    try:
        hooks.execute(sys.argv)
    except UnregisteredHookError as e:
        log('Unknown hook {} - skipping.'.format(e))
