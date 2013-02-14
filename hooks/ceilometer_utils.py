import os
import uuid

NOVA_CONF = "/etc/nova/nova.conf"
CEILOMETER_CONF = "/etc/ceilometer/ceilometer.conf"
CEILOMETER_COMPUTE_SERVICES = ['ceilometer-agent-compute']
CEILOMETER_PACKAGES = ['ceilometer-common', 'ceilometer-agent-compute']
NOVA_SETTINGS = ['instance_usage_audit=True',
    'instance_usage_audit_period=hour',
    'notification_driver=nova.openstack.common.notifier.rabbit_notifier',
    'notification_driver=ceilometer.compute.nova_notifier']
