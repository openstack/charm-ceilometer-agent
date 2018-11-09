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

from mock import MagicMock, patch

# python-apt is not installed as part of test-requirements but is imported by
# some charmhelpers modules so create a fake import.
mock_apt = MagicMock()
sys.modules['apt'] = mock_apt
mock_apt.apt_pkg = MagicMock()

import ceilometer_utils as utils

from test_utils import CharmTestCase


TO_PATCH = [
    'get_os_codename_package',
    'templating',
    'CeilometerServiceContext',
    'config',
    'get_os_codename_install_source',
    'configure_installation_source',
    'apt_install',
    'apt_update',
    'apt_upgrade',
    'log',
    'os_application_version_set',
    'token_cache_pkgs',
    'enable_memcache',
]


class CeilometerUtilsTest(CharmTestCase):

    def setUp(self):
        super(CeilometerUtilsTest, self).setUp(utils, TO_PATCH)

    def tearDown(self):
        super(CeilometerUtilsTest, self).tearDown()

    def test_register_configs(self):
        self.enable_memcache.return_value = False
        configs = utils.register_configs()
        registered_configs = [c[0][0] for c in configs.register.call_args_list]
        self.assertTrue(utils.CEILOMETER_CONF in registered_configs)
        self.assertFalse(utils.MEMCACHED_CONF in registered_configs)

    def test_register_configs_newton(self):
        self.enable_memcache.return_value = True
        configs = utils.register_configs()
        registered_configs = [c[0][0] for c in configs.register.call_args_list]
        for config in utils.CONFIG_FILES.keys():
            self.assertTrue(config in registered_configs)

    def test_restart_map(self):
        self.enable_memcache.return_value = False
        restart_map = utils.restart_map()
        self.assertEqual(restart_map,
                         {'/etc/ceilometer/ceilometer.conf': [
                             'ceilometer-agent-compute']})

    def test_restart_map_newton(self):
        self.enable_memcache.return_value = True
        restart_map = utils.restart_map()
        expect = {
            '/etc/ceilometer/ceilometer.conf': ['ceilometer-agent-compute'],
            '/etc/memcached.conf': ['memcached']}
        self.assertEqual(restart_map, expect)

    def test_assess_status(self):
        with patch.object(utils, 'assess_status_func') as asf:
            callee = MagicMock()
            asf.return_value = callee
            utils.assess_status('test-config')
            asf.assert_called_once_with('test-config')
            callee.assert_called_once_with()
            self.os_application_version_set.assert_called_with(
                utils.VERSION_PACKAGE
            )

    @patch.object(utils, 'REQUIRED_INTERFACES')
    @patch.object(utils, 'services')
    @patch.object(utils, 'make_assess_status_func')
    def test_assess_status_func(self,
                                make_assess_status_func,
                                services,
                                REQUIRED_INTERFACES):
        services.return_value = 's1'
        utils.assess_status_func('test-config')
        # ports=None whilst port checks are disabled.
        make_assess_status_func.assert_called_once_with(
            'test-config', REQUIRED_INTERFACES, services='s1', ports=None)

    def test_pause_unit_helper(self):
        with patch.object(utils, '_pause_resume_helper') as prh:
            utils.pause_unit_helper('random-config')
            prh.assert_called_once_with(utils.pause_unit, 'random-config')
        with patch.object(utils, '_pause_resume_helper') as prh:
            utils.resume_unit_helper('random-config')
            prh.assert_called_once_with(utils.resume_unit, 'random-config')

    @patch.object(utils, 'services')
    def test_pause_resume_helper(self, services):
        f = MagicMock()
        services.return_value = 's1'
        with patch.object(utils, 'assess_status_func') as asf:
            asf.return_value = 'assessor'
            utils._pause_resume_helper(f, 'some-config')
            asf.assert_called_once_with('some-config')
            # ports=None whilst port checks are disabled.
            f.assert_called_once_with('assessor', services='s1', ports=None)

    def test_determine_purge_packages(self):
        'Ensure no packages are identified for purge prior to rocky'
        self.get_os_codename_package.return_value = 'queens'
        self.assertEqual(utils.determine_purge_packages(), [])

    def test_determine_purge_packages_rocky(self):
        'Ensure python packages are identified for purge at rocky'
        self.get_os_codename_package.return_value = 'rocky'
        self.assertEqual(utils.determine_purge_packages(),
                         [p for p in utils.CEILOMETER_AGENT_PACKAGES
                          if p.startswith('python-')])

    def test_get_packages_queens(self):
        self.get_os_codename_package.return_value = 'queens'
        self.token_cache_pkgs.return_value = []
        self.assertEqual(utils.get_packages(),
                         utils.CEILOMETER_AGENT_PACKAGES)

    def test_get_packages_rocky(self):
        self.get_os_codename_package.return_value = 'rocky'
        self.token_cache_pkgs.return_value = []
        self.assertEqual(sorted(utils.get_packages()),
                         sorted([p for p in utils.CEILOMETER_AGENT_PACKAGES
                                 if not p.startswith('python-')] +
                                ['python3-ceilometer', 'python3-memcache']))
