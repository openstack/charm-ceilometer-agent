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
from mock import patch, MagicMock

import ceilometer_utils
# Patch out register_configs for import of hooks
_register_configs = ceilometer_utils.register_configs
ceilometer_utils.register_configs = MagicMock()

import ceilometer_hooks as hooks

# Renable old function
ceilometer_utils.register_configs = _register_configs

from test_utils import CharmTestCase

TO_PATCH = [
    'configure_installation_source',
    'apt_install',
    'apt_update',
    'config',
    'filter_installed_packages',
    'CONFIGS',
    'relation_set',
    'openstack_upgrade_available',
    'do_openstack_upgrade',
    'update_nrpe_config',
    'is_relation_made',
    'get_packages',
    'os_release',
]


class CeilometerHooksTest(CharmTestCase):

    def setUp(self):
        super(CeilometerHooksTest, self).setUp(hooks, TO_PATCH)
        self.config.side_effect = self.test_config.get

    @patch('charmhelpers.core.hookenv.config')
    def test_configure_source(self, mock_config):
        self.test_config.set('openstack-origin', 'cloud:precise-havana')
        hooks.hooks.execute(['hooks/install'])
        self.configure_installation_source.\
            assert_called_with('cloud:precise-havana')

    @patch('charmhelpers.core.hookenv.config')
    def test_install_hook(self, mock_config):
        ceil_pkgs = ['pkg1', 'pkg2']
        self.filter_installed_packages.return_value = ceil_pkgs
        hooks.hooks.execute(['hooks/install'])
        self.assertTrue(self.configure_installation_source.called)
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
        hooks.hooks.execute(['hooks/nova-ceilometer-relation-joined'])
        self.relation_set.assert_called_with(
            relation_id=None,
            subordinate_configuration=json.dumps(
                ceilometer_utils.NOVA_SETTINGS))

    @patch('charmhelpers.core.hookenv.config')
    def test_config_changed_no_upgrade(self, mock_config):
        self.openstack_upgrade_available.return_value = False
        self.os_release.return_value = 'liberty'
        hooks.hooks.execute(['hooks/config-changed'])
        self.openstack_upgrade_available.\
            assert_called_with('ceilometer-common')
        self.assertFalse(self.do_openstack_upgrade.called)
        self.assertTrue(self.CONFIGS.write_all.called)
        self.assertTrue(self.update_nrpe_config.called)
        self.assertFalse(self.apt_install.called)

    @patch('charmhelpers.core.hookenv.config')
    def test_config_changed_partial_upgrade(self, mock_config):
        self.openstack_upgrade_available.return_value = False
        self.os_release.return_value = 'mitaka'
        hooks.hooks.execute(['hooks/config-changed'])
        self.openstack_upgrade_available.\
            assert_called_with('ceilometer-common')
        self.assertFalse(self.do_openstack_upgrade.called)
        self.assertTrue(self.CONFIGS.write_all.called)
        self.assertTrue(self.update_nrpe_config.called)
        self.assertTrue(self.apt_install.called)

    @patch('charmhelpers.core.hookenv.config')
    def test_config_changed_upgrade(self, mock_config):
        self.openstack_upgrade_available.return_value = True
        hooks.hooks.execute(['hooks/config-changed'])
        self.openstack_upgrade_available.\
            assert_called_with('ceilometer-common')
        self.assertTrue(self.do_openstack_upgrade.called)
        self.assertTrue(self.CONFIGS.write_all.called)
        self.assertTrue(self.update_nrpe_config.called)

    def test_config_changed_with_openstack_upgrade_action(self):
        self.openstack_upgrade_available.return_value = True
        self.test_config.set('action-managed-upgrade', True)

        hooks.hooks.execute(['hooks/config-changed'])

        self.assertFalse(self.do_openstack_upgrade.called)

    @patch('charmhelpers.core.hookenv.config')
    def test_config_changed_no_nrpe(self, mock_config):
        self.openstack_upgrade_available.return_value = False
        self.os_release.return_value = 'mitaka'
        self.is_relation_made.return_value = False

        hooks.hooks.execute(['hooks/config-changed'])
        self.openstack_upgrade_available.\
            assert_called_with('ceilometer-common')
        self.assertFalse(self.do_openstack_upgrade.called)
        self.assertTrue(self.CONFIGS.write_all.called)
        self.assertFalse(self.update_nrpe_config.called)
