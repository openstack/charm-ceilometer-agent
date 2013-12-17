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

    def __call__(self):
        for relid in relation_ids('ceilometer-service'):
            for unit in related_units(relid):
                conf = {}
                for attr in self.keys:
                    conf[attr] = relation_get(attr,
                                              unit=unit, rid=relid)
                if context_complete(conf):
                    return conf
        return {}
