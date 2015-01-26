# Copyright 2014-2015 Canonical Limited.
#
# This file is part of charm-helpers.
#
# charm-helpers is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3 as
# published by the Free Software Foundation.
#
# charm-helpers is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with charm-helpers.  If not, see <http://www.gnu.org/licenses/>.

import os
import re
from subprocess import (
    check_call,
    check_output,
)

import six


##################################################
# loopback device helpers.
##################################################
def loopback_devices():
    '''
    Parse through 'losetup -a' output to determine currently mapped
    loopback devices. Output is expected to look like:

        /dev/loop0: [0807]:961814 (/tmp/my.img)

    :returns: dict: a dict mapping {loopback_dev: backing_file}
    '''
    loopbacks = {}
    cmd = ['losetup', '-a']
    devs = [d.strip().split(' ') for d in
            check_output(cmd).splitlines() if d != '']
    for dev, _, f in devs:
        loopbacks[dev.replace(':', '')] = re.search('\((\S+)\)', f).groups()[0]
    return loopbacks


def create_loopback(file_path):
    '''
    Create a loopback device for a given backing file.

    :returns: str: Full path to new loopback device (eg, /dev/loop0)
    '''
    file_path = os.path.abspath(file_path)
    check_call(['losetup', '--find', file_path])
    for d, f in six.iteritems(loopback_devices()):
        if f == file_path:
            return d


def ensure_loopback_device(path, size):
    '''
    Ensure a loopback device exists for a given backing file path and size.
    If it a loopback device is not mapped to file, a new one will be created.

    TODO: Confirm size of found loopback device.

    :returns: str: Full path to the ensured loopback device (eg, /dev/loop0)
    '''
    for d, f in six.iteritems(loopback_devices()):
        if f == path:
            return d

    if not os.path.exists(path):
        cmd = ['truncate', '--size', size, path]
        check_call(cmd)

    return create_loopback(path)
