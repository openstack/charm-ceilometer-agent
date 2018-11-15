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
    CeilometerServiceContext,
)
from charmhelpers.contrib.openstack.utils import (
    get_os_codename_package,
    get_os_codename_install_source,
    configure_installation_source,
    make_assess_status_func,
    pause_unit,
    resume_unit,
    os_application_version_set,
    token_cache_pkgs,
    enable_memcache,
    reset_os_release,
    CompareOpenStackReleases,
)
from charmhelpers.core.hookenv import (
    config,
    log,
)
from charmhelpers.fetch import (
    apt_update,
    apt_install,
    apt_upgrade,
    apt_purge,
    apt_autoremove,
    filter_missing_packages,
)

CEILOMETER_CONF_DIR = "/etc/ceilometer"
CEILOMETER_CONF = "%s/ceilometer.conf" % CEILOMETER_CONF_DIR

CEILOMETER_AGENT_SERVICES = ['ceilometer-agent-compute']

CEILOMETER_AGENT_PACKAGES = [
    'python-ceilometer', 'ceilometer-common',
    'ceilometer-agent-compute'
]

PY3_PACKAGES = [
    'python3-ceilometer',
    'python3-memcache',
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
            context.InternalEndpointContext(),
            context.MemcacheContext(package='ceilometer-common')],
        'services': CEILOMETER_AGENT_SERVICES
    },
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

    if enable_memcache(release=release):
        configs.register(
            MEMCACHED_CONF,
            [context.MemcacheContext(package='ceilometer-common')])

    return configs


def get_packages():
    release = CompareOpenStackReleases(get_os_codename_package(
        'ceilometer-common', fatal=False) or 'icehouse')

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
    release = CompareOpenStackReleases(get_os_codename_package(
        'ceilometer-common', fatal=False) or 'icehouse')
    if release >= 'rocky':
        pkgs = [p for p in CEILOMETER_AGENT_PACKAGES
                if p.startswith('python-')]
        pkgs.append('python-memcache')
        return pkgs
    return []


def remove_old_packages():
    '''Purge any packages that need ot be removed.

    :returns: bool Whether packages were removed.
    '''
    installed_packages = filter_missing_packages(determine_purge_packages())
    if installed_packages:
        apt_purge(installed_packages, fatal=True)
        apt_autoremove(purge=True, fatal=True)
    return bool(installed_packages)


def restart_map():
    '''
    Determine the correct resource map to be passed to
    charmhelpers.core.restart_on_change() based on the services configured.

    :returns: dict: A dictionary mapping config file to lists of services
                    that should be restarted when file changes.
    '''
    release = (get_os_codename_package('ceilometer-common', fatal=False) or
               'icehouse')
    _map = {}
    for f, ctxt in CONFIG_FILES.iteritems():
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
    reset_os_release()
    apt_install(packages=CEILOMETER_AGENT_PACKAGES,
                options=dpkg_opts,
                fatal=True)
    # Call apt_install a 2nd time to allow packages which are enabled
    # for specific OpenStack version to be installed . This is because
    # Openstack version for a subordinate should be derived from the
    # version of an installed package rather than relying on
    # openstack-origin which would not be present in a subordinate.
    apt_install(get_packages(), fatal=True)

    remove_old_packages()

    # set CONFIGS to load templates from new release
    configs.set_release(openstack_release=new_os_rel)


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
