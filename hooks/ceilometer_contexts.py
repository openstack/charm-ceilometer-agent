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

import base64
import os

from charmhelpers.core.hookenv import (
    relation_ids,
    relation_get,
    related_units,
)

from charmhelpers.contrib.openstack.context import (
    OSContextGenerator,
    context_complete
)


class CeilometerServiceContext(OSContextGenerator):
    interfaces = ['ceilometer-service']
    keys = [
        'debug',
        'verbose',
        'rabbitmq_host',
        'rabbitmq_user',
        'rabbitmq_password',
        'rabbitmq_virtual_host',
        'api_version',
        'auth_protocol',
        'auth_host',
        'auth_port',
        'admin_tenant_name',
        'admin_user',
        'admin_password',
        'metering_secret',
        'service_host',
        'service_protocol',
        'service_port',
        'signing_dir',
        'api_version',
    ]

    optional_keys = [
        'rabbit_ssl_port',
        'rabbit_ssl_ca'
    ]

    def __init__(self, ssl_dir=None):
        self.ssl_dir = ssl_dir

    def __call__(self):
        for relid in relation_ids('ceilometer-service'):
            for unit in related_units(relid):
                conf = {}
                for attr in self.keys:
                    conf[attr] = relation_get(
                        attr, unit=unit, rid=relid)
                if (conf['api_version'] is not None and
                        float(conf['api_version']) > 2):
                    self.keys.append('admin_domain_name')
                    conf['admin_domain_name'] = relation_get(
                        'admin_domain_name', unit=unit, rid=relid)
                if context_complete(conf):
                    for attr in self.optional_keys:
                        conf[attr] = relation_get(attr, unit=unit, rid=relid)
                    if conf.get('rabbit_ssl_ca') is not None:
                        ca_path = os.path.join(
                            self.ssl_dir, 'rabbit-client-ca.pem')
                        with open(ca_path, 'w') as fh:
                            fh.write(base64.b64decode(conf['rabbit_ssl_ca']))
                            conf['rabbit_ssl_ca'] = ca_path
                    return conf
        return {}
