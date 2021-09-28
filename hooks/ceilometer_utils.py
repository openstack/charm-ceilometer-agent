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

from copy import deepcopy
from charmhelpers.contrib.openstack import (
    context,
    templating,
)
from ceilometer_contexts import (
    CeilometerAgentContext,
    CeilometerServiceContext,
)
from charmhelpers.contrib.openstack.utils import (
    get_os_codename_package,
    make_assess_status_func,
    pause_unit,
    resume_unit,
    os_application_version_set,
    token_cache_pkgs,
    enable_memcache,
    CompareOpenStackReleases,
)
from charmhelpers.fetch import (
    apt_purge,
    apt_autoremove,
    apt_mark,
    filter_missing_packages,
)

CEILOMETER_CONF_DIR = "/etc/ceilometer"
CEILOMETER_CONF = "%s/ceilometer.conf" % CEILOMETER_CONF_DIR
POLLING_CONF = "%s/polling.yaml" % CEILOMETER_CONF_DIR

CEILOMETER_AGENT_SERVICES = ['ceilometer-agent-compute']

CEILOMETER_AGENT_PACKAGES = [
    'python-ceilometer', 'ceilometer-common',
    'ceilometer-agent-compute'
]

PY3_PACKAGES = [
    'python3-ceilometer',
    'python3-memcache',
]

HELD_PACKAGES = [
    'python-memcache',
]

VERSION_PACKAGE = 'ceilometer-common'

NOVA_CONF = "/etc/nova/nova.conf"
MEMCACHED_CONF = '/etc/memcached.conf'

NOVA_SETTINGS = {
    "nova": {
        "/etc/nova/nova.conf": {
            "sections": {
                "DEFAULT": [
                    ('instance_usage_audit', 'True'),
                    ('instance_usage_audit_period', 'hour'),
                    ('notify_on_state_change', 'vm_and_task_state'),
                ]
            }
        }
    }
}

CONFIG_FILES = {
    CEILOMETER_CONF: {
        'hook_contexts': [
            CeilometerServiceContext(ssl_dir=CEILOMETER_CONF_DIR),
            context.AMQPContext(ssl_dir=CEILOMETER_CONF_DIR),
            context.InternalEndpointContext(),
            context.MemcacheContext(package='ceilometer-common')],
        'services': CEILOMETER_AGENT_SERVICES
    },
}

QUEENS_CONFIG_FILES = deepcopy(CONFIG_FILES)
QUEENS_CONFIG_FILES.update({
    POLLING_CONF: {
        'hook_contexts': [
            CeilometerAgentContext()
        ],
        'services': CEILOMETER_AGENT_SERVICES
    }
})

TEMPLATES = 'templates'

REQUIRED_INTERFACES = {
    'ceilometer': ['ceilometer-service'],
    'messaging': ['amqp'],
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
    release = _get_current_release()
    configs = templating.OSConfigRenderer(templates_dir=TEMPLATES,
                                          openstack_release=release)

    if CompareOpenStackReleases(release) >= 'queens':
        _config_files = QUEENS_CONFIG_FILES
    else:
        _config_files = CONFIG_FILES

    for conf in _config_files:
        configs.register(conf, _config_files[conf]['hook_contexts'])

    if enable_memcache(release=release):
        configs.register(
            MEMCACHED_CONF,
            [context.MemcacheContext(package='ceilometer-common')])

    return configs


def get_packages():
    release = _get_current_release()

    packages = deepcopy(CEILOMETER_AGENT_PACKAGES)
    packages.extend(token_cache_pkgs(release=release))

    if release >= 'rocky':
        packages = [p for p in packages if not p.startswith('python-')]
        packages.extend(PY3_PACKAGES)

    return packages


def determine_purge_packages():
    '''
    Determine list of packages that where previously installed which are no
    longer needed.

    :returns: list of package names
    '''
    release = _get_current_release()
    if release >= 'rocky':
        pkgs = [p for p in CEILOMETER_AGENT_PACKAGES
                if p.startswith('python-')]
        return pkgs
    return []


def releases_packages_map():
    '''Provide a map of all supported releases and their packages.

    NOTE(lourot): this is a simplified version of a more generic
    implementation:
    https://github.com/openstack/charms.openstack/blob/master/charms_openstack/charm/core.py

    :returns: Map of release, package type and install / purge packages.
        Example:
        {
            'mitaka': {
                'deb': {
                    'install': ['python-ldappool'],
                    'purge': []
                }
            },
            'rocky': {
                'deb': {
                    'install': ['python3-ldap', 'python3-ldappool'],
                    'purge': ['python-ldap', 'python-ldappool']}
            }
        }
    :rtype: Dict[str,Dict[str,List[str]]]
    '''
    return {
        _get_current_release(): {
            'deb': {
                'install': get_packages(),
                'purge': determine_purge_packages(),
            }
        }
    }


def remove_old_packages():
    '''Purge any packages that need ot be removed.

    :returns: bool Whether packages were removed.
    '''
    installed_packages = filter_missing_packages(determine_purge_packages())
    if installed_packages:
        apt_mark(filter_missing_packages(determine_held_packages()),
                 'auto')
        apt_purge(installed_packages, fatal=True)
        apt_autoremove(purge=True, fatal=True)
    return bool(installed_packages)


def determine_held_packages():
    '''Return a list of packages to mark as candidates for removal
    for the current OS release'''
    release = _get_current_release()
    if release >= 'rocky':
        return HELD_PACKAGES
    return []


def restart_map():
    '''
    Determine the correct resource map to be passed to
    charmhelpers.core.restart_on_change() based on the services configured.

    :returns: dict: A dictionary mapping config file to lists of services
                    that should be restarted when file changes.
    '''
    release = _get_current_release()

    if CompareOpenStackReleases(release) >= 'queens':
        _config_files = QUEENS_CONFIG_FILES
    else:
        _config_files = CONFIG_FILES

    _map = {}
    for f, ctxt in _config_files.items():
        svcs = []
        for svc in ctxt['services']:
            svcs.append(svc)
        if svcs:
            _map[f] = svcs
    if enable_memcache(release=release):
        _map[MEMCACHED_CONF] = ['memcached']
    return _map


def services():
    ''' Returns a list of services associate with this charm '''
    _services = []
    for v in restart_map().values():
        _services = _services + v
    return list(set(_services))


def assess_status(configs):
    """Assess status of current unit
    Decides what the state of the unit should be based on the current
    configuration.
    SIDE EFFECT: calls set_os_workload_status(...) which sets the workload
    status of the unit.
    Also calls status_set(...) directly if paused state isn't complete.
    @param configs: a templating.OSConfigRenderer() object
    @returns None - this function is executed for its side-effect
    """
    assess_status_func(configs)()
    os_application_version_set(VERSION_PACKAGE)


def assess_status_func(configs):
    """Helper function to create the function that will assess_status() for
    the unit.
    Uses charmhelpers.contrib.openstack.utils.make_assess_status_func() to
    create the appropriate status function and then returns it.
    Used directly by assess_status() and also for pausing and resuming
    the unit.

    NOTE(ajkavanagh) ports are not checked due to race hazards with services
    that don't behave sychronously w.r.t their service scripts.  e.g.
    apache2.
    @param configs: a templating.OSConfigRenderer() object
    @return f() -> None : a function that assesses the unit's workload status
    """
    return make_assess_status_func(
        configs, REQUIRED_INTERFACES,
        services=services(), ports=None)


def pause_unit_helper(configs):
    """Helper function to pause a unit, and then call assess_status(...) in
    effect, so that the status is correctly updated.
    Uses charmhelpers.contrib.openstack.utils.pause_unit() to do the work.
    @param configs: a templating.OSConfigRenderer() object
    @returns None - this function is executed for its side-effect
    """
    _pause_resume_helper(pause_unit, configs)


def resume_unit_helper(configs):
    """Helper function to resume a unit, and then call assess_status(...) in
    effect, so that the status is correctly updated.
    Uses charmhelpers.contrib.openstack.utils.resume_unit() to do the work.
    @param configs: a templating.OSConfigRenderer() object
    @returns None - this function is executed for its side-effect
    """
    _pause_resume_helper(resume_unit, configs)


def _pause_resume_helper(f, configs):
    """Helper function that uses the make_assess_status_func(...) from
    charmhelpers.contrib.openstack.utils to create an assess_status(...)
    function that can be used with the pause/resume of the unit
    @param f: the function to be used with the assess_status(...) function
    @returns None - this function is executed for its side-effect
    """
    # TODO(ajkavanagh) - ports= has been left off because of the race hazard
    # that exists due to service_start()
    f(assess_status_func(configs),
      services=services(),
      ports=None)


def _get_current_release():
    return (get_os_codename_package('ceilometer-common', fatal=False)
            or 'icehouse')
