#!/usr/bin/python

import sys
import time
import os
import utils
import ceilometer_utils


def install():
    utils.configure_source()
    utils.install(*ceilometer_utils.CEILOMETER_PACKAGES)
    utils.modify_config_file(ceilometer_utils.NOVA_CONF,
        ceilometer_utils.NOVA_SETTINGS)
    utils.restart(*ceilometer_utils.CEILOMETER_COMPUTE_SERVICES)


def get_ceilometer_conf():
    for relid in utils.relation_ids('ceilometer-service'):
        for unit in utils.relation_list(relid):
            conf = {
                'metering_secret': utils.relation_get('metering_secret',
                    unit, relid),
                'rabbit_host': utils.relation_get('rabbit_host', unit, relid),
                'rabbit_virtual_host': utils.relation_get(
                    'rabbit_virtual_host', unit, relid),
                'rabbit_userid': utils.relation_get('rabbit_userid',
                    unit, relid),
                'rabbit_password': utils.relation_get('rabbit_password',
                    unit, relid),
                'keystone_os_username': utils.relation_get(
                    'keystone_os_username', unit, relid),
                'keystone_os_password': utils.relation_get(
                    'keystone_os_password', unit, relid),
                'keystone_os_tenant': utils.relation_get('keystone_os_tenant',
                    unit, relid),
                'keystone_host': utils.relation_get('keystone_host',
                    unit, relid),
                'keystone_port': utils.relation_get('keystone_port',
                    unit, relid)
            }

            if None not in conf.itervalues():
                return conf
    return None


def ceilometer_changed():
    # read settings
    context = get_ceilometer_conf()
    if context:
        with open(ceilometer_utils.CEILOMETER_CONF, "w") as conf:
            conf.write(utils.render_template(os.path.basename(
                ceilometer_utils.CEILOMETER_CONF), context))
            utils.restart(*ceilometer_utils.CEILOMETER_COMPUTE_SERVICES)

utils.do_hooks({
    "install": install,
    "ceilometer-service-relation-changed": ceilometer_changed
})
sys.exit(0)
