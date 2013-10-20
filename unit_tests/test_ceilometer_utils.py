from mock import patch, call

import ceilometer_utils as utils

from test_utils import CharmTestCase

TO_PATCH = [
    'get_os_codename_package',
    'templating',
    'CeilometerServiceContext',
]


class CeilometerUtilsTest(CharmTestCase):

    def setUp(self):
        super(CeilometerUtilsTest, self).setUp(utils, TO_PATCH)

    def tearDown(self):
        super(CeilometerUtilsTest, self).tearDown()

    def test_register_configs(self):
        configs = utils.register_configs()
        calls = []
        for conf in utils.CONFIG_FILES:
            calls.append(call(conf,
                              utils.CONFIG_FILES[conf]['hook_contexts']))
        configs.register.assert_has_calls(calls, any_order=True)

    def test_restart_map(self):
        restart_map = utils.restart_map()
        self.assertEquals(restart_map,
                          {'/etc/ceilometer/ceilometer.conf': [
                              'ceilometer-agent-compute']})
