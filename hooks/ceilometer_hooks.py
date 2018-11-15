#!/usr/bin/python
#
# Copyright 2016 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import json
from charmhelpers.fetch import (
    apt_install, filter_installed_packages,
    apt_update
)
from charmhelpers.core.hookenv import (
    Hooks, UnregisteredHookError,
    log,
    is_relation_made,
    relation_set,
    status_set,
    relation_ids,
)
from charmhelpers.core.host import (
    service_restart
)
from charmhelpers.contrib.openstack.utils import (
    pausable_restart_on_change as restart_on_change,
    is_unit_paused_set,
    series_upgrade_prepare,
    series_upgrade_complete,
)
from ceilometer_utils import (
    restart_map,
    services,
    register_configs,
    NOVA_SETTINGS,
    assess_status,
    get_packages,
    pause_unit_helper,
    resume_unit_helper,
    remove_old_packages,
)
from charmhelpers.contrib.charmsupport import nrpe

hooks = Hooks()
CONFIGS = register_configs()


@hooks.hook('install.real')
def install():
    status_set('maintenance', 'Installing apt packages')
    apt_update(fatal=True)
    # Install -common package so we get accurate version determination
    apt_install(filter_installed_packages(['ceilometer-common']),
                fatal=True)
    apt_install(
        filter_installed_packages(get_packages()),
        fatal=True)


@hooks.hook('nova-ceilometer-relation-joined')
def nova_ceilometer_joined(relation_id=None):
    relation_set(relation_id=relation_id,
                 subordinate_configuration=json.dumps(NOVA_SETTINGS))


@hooks.hook("ceilometer-service-relation-changed")
@restart_on_change(restart_map())
def ceilometer_changed():
    CONFIGS.write_all()
    if is_relation_made('nrpe-external-master'):
        update_nrpe_config()


@hooks.hook("upgrade-charm")
def upgrade_charm():
    apt_install(
        filter_installed_packages(get_packages()),
        fatal=True)
    packages_removed = remove_old_packages()
    if packages_removed and not is_unit_paused_set():
        log("Package purge detected, restarting services", "INFO")
        for s in services():
            service_restart(s)
    # NOTE(jamespage): Ensure any changes to nova presented data are made
    #                  during charm upgrades.
    for rid in relation_ids('nova-ceilometer'):
        nova_ceilometer_joined(rid)


@hooks.hook('nova-ceilometer-relation-changed')
@hooks.hook('config-changed')
@restart_on_change(restart_map(), stopstart=True)
def config_changed():
    # if we are paused, delay doing any config changed hooks.
    # It is forced on the resume.
    if is_unit_paused_set():
        log("Unit is pause or upgrading. Skipping config_changed", "WARN")
        return

    apt_install(filter_installed_packages(get_packages()), fatal=True)
    if is_relation_made('nrpe-external-master'):
        update_nrpe_config()
    CONFIGS.write_all()


@hooks.hook('nrpe-external-master-relation-joined',
            'nrpe-external-master-relation-changed')
def update_nrpe_config():
    # python-dbus is used by check_upstart_job
    apt_install('python-dbus')
    hostname = nrpe.get_nagios_hostname()
    current_unit = nrpe.get_nagios_unit_name()
    nrpe_setup = nrpe.NRPE(hostname=hostname)
    nrpe.add_init_service_checks(nrpe_setup, services(), current_unit)
    nrpe_setup.write()


@hooks.hook('pre-series-upgrade')
def pre_series_upgrade():
    log("Running prepare series upgrade hook", "INFO")
    series_upgrade_prepare(
        pause_unit_helper, CONFIGS)


@hooks.hook('post-series-upgrade')
def post_series_upgrade():
    log("Running complete series upgrade hook", "INFO")
    series_upgrade_complete(
        resume_unit_helper, CONFIGS)


if __name__ == '__main__':
    try:
        hooks.execute(sys.argv)
    except UnregisteredHookError as e:
        log('Unknown hook {} - skipping.'.format(e))
    # set_os_workload_status(CONFIGS, REQUIRED_INTERFACES)
    assess_status(CONFIGS)
