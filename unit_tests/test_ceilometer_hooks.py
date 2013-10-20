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
]


class CeilometerHooksTest(CharmTestCase):

    def setUp(self):
        super(CeilometerHooksTest, self).setUp(hooks, TO_PATCH)
        self.config.side_effect = self.test_config.get

    def test_configure_source(self):
        self.test_config.set('openstack-origin', 'cloud:precise-havana')
        hooks.hooks.execute(['hooks/install'])
        self.configure_installation_source.\
            assert_called_with('cloud:precise-havana')

    def test_install_hook(self):
        self.filter_installed_packages.return_value = \
            hooks.CEILOMETER_AGENT_PACKAGES
        hooks.hooks.execute(['hooks/install'])
        self.assertTrue(self.configure_installation_source.called)
        self.apt_update.assert_called_with(fatal=True)
        self.apt_install.assert_called_with(hooks.CEILOMETER_AGENT_PACKAGES,
                                            fatal=True)

    def test_ceilometer_changed(self):
        hooks.hooks.execute(['hooks/ceilometer-service-relation-changed'])
        self.assertTrue(self.CONFIGS.write_all.called)
