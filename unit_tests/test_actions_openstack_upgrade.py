from mock import patch
import os

os.environ['JUJU_UNIT_NAME'] = 'ceilometer'

with patch('ceilometer_utils.register_configs') as register_configs:
    import openstack_upgrade

from test_utils import (
    CharmTestCase
)

TO_PATCH = [
    'config_changed',
    'do_action_openstack_upgrade',
    'register_configs',
    'uuid'
]


class TestCinderUpgradeActions(CharmTestCase):

    def setUp(self):
        super(TestCinderUpgradeActions, self).setUp(openstack_upgrade,
                                                    TO_PATCH)

    @patch('charmhelpers.contrib.openstack.utils.config')
    @patch('charmhelpers.contrib.openstack.utils.action_set')
    def test_openstack_upgrade_true(self, action_set, config):
        self.do_action_openstack_upgrade.return_value = True

        openstack_upgrade.openstack_upgrade()

        self.assertTrue(self.do_action_openstack_upgrade.called)
        self.assertTrue(self.config_changed.called)

    @patch('charmhelpers.contrib.openstack.utils.config')
    @patch('charmhelpers.contrib.openstack.utils.action_set')
    def test_openstack_upgrade_false(self, action_set, config):
        self.do_action_openstack_upgrade.return_value = False

        openstack_upgrade.openstack_upgrade()

        self.assertTrue(self.do_action_openstack_upgrade.called)
        self.assertFalse(self.config_changed.called)
