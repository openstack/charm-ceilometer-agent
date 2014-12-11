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
    'do_openstack_upgrade'
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
        self.filter_installed_packages.return_value = \
            hooks.CEILOMETER_AGENT_PACKAGES
        hooks.hooks.execute(['hooks/install'])
        self.assertTrue(self.configure_installation_source.called)
        self.apt_update.assert_called_with(fatal=True)
        self.apt_install.assert_called_with(hooks.CEILOMETER_AGENT_PACKAGES,
                                            fatal=True)

    @patch('charmhelpers.core.hookenv.config')
    def test_ceilometer_changed(self, mock_config):
        hooks.hooks.execute(['hooks/ceilometer-service-relation-changed'])
        self.assertTrue(self.CONFIGS.write_all.called)

    @patch('charmhelpers.core.hookenv.config')
    def test_nova_ceilometer_joined(self, mock_config):
        hooks.hooks.execute(['hooks/nova-ceilometer-relation-joined'])
        self.relation_set.assert_called_with(
            subordinate_configuration=json.dumps(ceilometer_utils.NOVA_SETTINGS))

    @patch('charmhelpers.core.hookenv.config')
    def test_config_changed_no_upgrade(self, mock_config):
        self.openstack_upgrade_available.return_value = False
        hooks.hooks.execute(['hooks/config-changed'])
        self.openstack_upgrade_available.\
            assert_called_with('ceilometer-common')
        self.assertFalse(self.do_openstack_upgrade.called)
        self.assertTrue(self.CONFIGS.write_all.called)

    @patch('charmhelpers.core.hookenv.config')
    def test_config_changed_upgrade(self, mock_config):
        self.openstack_upgrade_available.return_value = True
        hooks.hooks.execute(['hooks/config-changed'])
        self.openstack_upgrade_available.\
            assert_called_with('ceilometer-common')
        self.assertTrue(self.do_openstack_upgrade.called)
        self.assertTrue(self.CONFIGS.write_all.called)
