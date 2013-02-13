#!/usr/bin/python

import sys
import time
import os
import utils
import ceilometer_utils

def install():
    utils.configure_source()
    packages = ['ceilometer-common', 'ceilometer-agent-compute']
    utils.install(*packages)

def container_joined():
    utils.modify_config_file(ceilometer_utils.NOVA_CONF)
    utils.restart(*ceilometer_utils.CEILOMETER_COMPUTE_SERVICES)

def ceilometer_joined():
    pass

def ceilometer_changed():
    # read settings
    for relid in utils.relation_ids('ceilometer'):
        for unit in utils.relation_list(relid):
            conf = {
                'metering_secret': utils.relation_get('metering_secret', unit, relid),
                'rabbit_host': utils.relation_get('rabbit_host', unit, relid),
                'rabbit_virtual_host': utils.relation_get('rabbit_virtual_host', unit, relid),
                'rabbit_userid': utils.relation_get('rabbit_userid', unit, relid),
                'rabbit_password': utils.relation_get('rabbit_password', unit, relid),
                'keystone_os_username': utils.relation_get('keystone_os_username', unit, relid),
                'keystone_os_password': utils.relation_get('keystone_os_password', unit, relid),
                'keystone_os_tenant': utils.relation_get('keystone_os_tenant', unit, relid),
                'keystone_host': utils.relation_get('keystone_host', unit, relid),
                'keystone_port': utils.relation_get('keystone_port', unit, relid)
            }
                

utils.do_hooks({
    "install": install,
    "container-relation-joined": container_joined,
    "ceilometer-service-relation-joined": ceilometer_joined,
    "ceilometer-service-relation-changed": ceilometer_changed
})
sys.exit(0)
