from mock import patch

import ceilometer_contexts as contexts

from test_utils import CharmTestCase

TO_PATCH = [
    'relation_get',
    'relation_ids',
    'related_units',
]


class CeilometerContextsTest(CharmTestCase):

    def setUp(self):
        super(CeilometerContextsTest, self).setUp(contexts, TO_PATCH)
        self.relation_get.side_effect = self.test_relation.get

    def tearDown(self):
        super(CeilometerContextsTest, self).tearDown()

    def test_ceilometer_service_context(self):
        self.relation_ids.return_value = ['ceilometer-service:0']
        self.related_units.return_value = ['ceilometer/0']
        data = {
            'metering_secret': 'mysecret',
            'keystone_host': 'test'
        }
        self.test_relation.set(data)
        self.assertEquals(contexts.CeilometerServiceContext()(), data)

    def test_ceilometer_service_context_not_related(self):
        self.relation_ids.return_value = []
        self.assertEquals(contexts.CeilometerServiceContext()(), {})
