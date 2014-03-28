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
        'auth_protocol',
        'auth_host',
        'auth_port',
        'admin_tenant_name',
        'admin_user',
        'admin_password',
        'metering_secret'
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
