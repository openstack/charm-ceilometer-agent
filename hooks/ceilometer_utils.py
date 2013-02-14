import os
import uuid

NOVA_CONF = "/etc/nova/nova.conf"
CEILOMETER_CONF = "/etc/ceilometer/ceilometer.conf"
CEILOMETER_COMPUTE_SERVICES = ['ceilometer-agent-compute']
CEILOMETER_PACKAGES = ['python-ceilometer', 'ceilometer-common', 'ceilometer-agent-compute']
NOVA_SETTINGS = [
    ('DEFAULT', 'instance_usage_audit', 'True'),
    ('DEFAULT', 'instance_usage_audit_period', 'hour'),
    ('DEFAULT', 'notification_driver', 'ceilometer.compute.nova_notifier')]
