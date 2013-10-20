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

    def __call__(self):
        for relid in relation_ids('ceilometer-service'):
            for unit in related_units(relid):
                conf = relation_get(unit=unit, rid=relid)
                if context_complete(conf):
                    return conf
        return {}
