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
            'rabbitmq_hosts': 'foo,bar',
            'rabbitmq_user': 'bar',
            'rabbitmq_password': 'baz',
            'rabbitmq_virtual_host': 'openstack',
            'rabbit_ssl_ca': None,
            'rabbit_ssl_port': None,
            'api_version': 3,
            'auth_protocol': 'http',
            'auth_host': 'keystone',
            'auth_port': '80',
            'service_protocol': 'http',
            'service_host': 'keystone',
            'service_port': '80',
            'signing_dir': '/var/lib/ceilometer',
            'admin_domain_name': 'admin_domain',
            'admin_tenant_name': 'admin',
            'admin_user': 'admin',
            'admin_password': 'password',
            'metering_secret': 'secret'
        }
        self.test_relation.set(data)
        self.assertEqual(contexts.CeilometerServiceContext()(), data)

    def test_ceilometer_service_context_not_related(self):
        self.relation_ids.return_value = []
        self.assertEqual(contexts.CeilometerServiceContext()(), {})
