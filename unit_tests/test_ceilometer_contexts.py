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
            'debug': True,
            'verbose': False,
            'rabbitmq_host': 'foo',
            'rabbitmq_user': 'bar',
            'rabbitmq_password': 'baz',
            'rabbitmq_virtual_host': 'openstack',
            'rabbit_ssl_ca': None,
            'rabbit_ssl_port': None,
            'auth_protocol': 'http',
            'auth_host': 'keystone',
            'auth_port': '80',
            'admin_tenant_name': 'admin',
            'admin_user': 'admin',
            'admin_password': 'password',
            'metering_secret': 'secret'
        }
        self.test_relation.set(data)
        self.assertEquals(contexts.CeilometerServiceContext()(), data)

    def test_ceilometer_service_context_not_related(self):
        self.relation_ids.return_value = []
        self.assertEquals(contexts.CeilometerServiceContext()(), {})
