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
    return True

utils.do_hooks({
    "install": install,
    "container-relation-joined": container_joined
})
sys.exit(0)
