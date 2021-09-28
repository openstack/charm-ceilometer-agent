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

import json
from unittest.mock import patch

import ceilometer_utils

with patch('ceilometer_utils.register_configs'):
    with patch('ceilometer_utils.restart_map'):
        import ceilometer_hooks as hooks

from test_utils import CharmTestCase

TO_PATCH = [
    'CONFIGS',
    'apt_install',
    'apt_update',
    'filter_installed_packages',
    'get_packages',
    'releases_packages_map',
    'services',
    'is_relation_made',
    'is_unit_paused_set',
    'relation_set',
    'update_nrpe_config',
]


class CeilometerHooksTest(CharmTestCase):

    def setUp(self):
        super(CeilometerHooksTest, self).setUp(hooks, TO_PATCH)

    @patch('charmhelpers.core.hookenv.config')
    def test_install_hook(self, mock_config):
        ceil_pkgs = ['pkg1', 'pkg2']
        self.filter_installed_packages.return_value = ceil_pkgs
        hooks.hooks.execute(['hooks/install'])
        self.apt_update.assert_called_with(fatal=True)
        self.apt_install.assert_called_with(ceil_pkgs, fatal=True)

    @patch('charmhelpers.core.hookenv.config')
    def test_ceilometer_changed(self, mock_config):
        hooks.hooks.execute(['hooks/ceilometer-service-relation-changed'])
        self.assertTrue(self.CONFIGS.write_all.called)
        self.assertTrue(self.update_nrpe_config.called)

    @patch('charmhelpers.core.hookenv.config')
    def test_ceilometer_changed_no_nrpe(self, mock_config):
        self.is_relation_made.return_value = False

        hooks.hooks.execute(['hooks/ceilometer-service-relation-changed'])
        self.assertTrue(self.CONFIGS.write_all.called)
        self.assertFalse(self.update_nrpe_config.called)

    @patch('charmhelpers.core.hookenv.config')
    def test_nova_ceilometer_joined(self, mock_config):
        mocked_releases_packages_map = {
            'ussuri': {
                'deb': {
                    'install': [
                        'ceilometer-common', 'ceilometer-agent-compute',
                        'python3-ceilometer', 'python3-memcache'],
                    'purge': ['python-ceilometer'],
                }}}
        mocked_services = ['ceilometer-agent-compute']

        self.releases_packages_map.return_value = mocked_releases_packages_map
        self.services.return_value = mocked_services
        hooks.hooks.execute(['hooks/nova-ceilometer-relation-joined'])
        self.relation_set.assert_called_with(
            relation_id=None,
            relation_settings={
                'subordinate_configuration': json.dumps(
                    ceilometer_utils.NOVA_SETTINGS),
                'releases-packages-map': json.dumps(
                    mocked_releases_packages_map, sort_keys=True),
                'services': json.dumps(mocked_services)})

    @patch('charmhelpers.core.hookenv.config')
    def test_config_changed(self, mock_config):
        self.is_relation_made.return_value = True
        self.is_unit_paused_set.return_value = False
        self.filter_installed_packages.return_value = ['pkg1', 'pkg2']
        hooks.hooks.execute(['hooks/config-changed'])
        self.update_nrpe_config.assert_called_once_with()
        self.CONFIGS.write_all.assert_called_once_with()
        self.apt_install.assert_called_once_with(['pkg1', 'pkg2'], fatal=True)
        self.is_relation_made.assert_called_once_with('nrpe-external-master')

    @patch('charmhelpers.core.hookenv.config')
    def test_config_changed_no_nrpe(self, mock_config):
        self.is_relation_made.return_value = False
        self.is_unit_paused_set.return_value = False
        self.filter_installed_packages.return_value = ['pkg1', 'pkg2']
        hooks.hooks.execute(['hooks/config-changed'])
        self.assertFalse(self.update_nrpe_config.called)
        self.CONFIGS.write_all.assert_called_once_with()
        self.apt_install.assert_called_once_with(['pkg1', 'pkg2'], fatal=True)
        self.is_relation_made.assert_called_once_with('nrpe-external-master')

    @patch('charmhelpers.core.hookenv.config')
    def test_config_changed_paused(self, mock_config):
        self.is_relation_made.return_value = True
        self.is_unit_paused_set.return_value = True
        self.filter_installed_packages.return_value = ['pkg1', 'pkg2']
        hooks.hooks.execute(['hooks/config-changed'])
        self.assertFalse(self.update_nrpe_config.called)
        self.assertFalse(self.CONFIGS.write_all.called)
        self.assertFalse(self.apt_install.called)
