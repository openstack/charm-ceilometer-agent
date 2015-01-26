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
from stat import S_ISBLK

from subprocess import (
    check_call,
    check_output,
    call
)


def is_block_device(path):
    '''
    Confirm device at path is a valid block device node.

    :returns: boolean: True if path is a block device, False if not.
    '''
    if not os.path.exists(path):
        return False
    return S_ISBLK(os.stat(path).st_mode)


def zap_disk(block_device):
    '''
    Clear a block device of partition table. Relies on sgdisk, which is
    installed as pat of the 'gdisk' package in Ubuntu.

    :param block_device: str: Full path of block device to clean.
    '''
    # sometimes sgdisk exits non-zero; this is OK, dd will clean up
    call(['sgdisk', '--zap-all', '--mbrtogpt',
          '--clear', block_device])
    dev_end = check_output(['blockdev', '--getsz',
                            block_device]).decode('UTF-8')
    gpt_end = int(dev_end.split()[0]) - 100
    check_call(['dd', 'if=/dev/zero', 'of=%s' % (block_device),
                'bs=1M', 'count=1'])
    check_call(['dd', 'if=/dev/zero', 'of=%s' % (block_device),
                'bs=512', 'count=100', 'seek=%s' % (gpt_end)])


def is_device_mounted(device):
    '''Given a device path, return True if that device is mounted, and False
    if it isn't.

    :param device: str: Full path of the device to check.
    :returns: boolean: True if the path represents a mounted device, False if
        it doesn't.
    '''
    is_partition = bool(re.search(r".*[0-9]+\b", device))
    out = check_output(['mount']).decode('UTF-8')
    if is_partition:
        return bool(re.search(device + r"\b", out))
    return bool(re.search(device + r"[0-9]+\b", out))
