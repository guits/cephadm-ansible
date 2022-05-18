# Copyright Red Hat
# SPDX-License-Identifier: Apache-2.0
# Author: Guillaume Abrioux <gabrioux@redhat.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import, division, print_function
from typing import List, Tuple
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule  # type: ignore
try:
    from ansible.module_utils.ceph_common import exit_module, build_base_cmd  # type: ignore
except ImportError:
    from module_utils.ceph_common import exit_module, build_base_cmd
import datetime
import json


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ceph_orch_host
short_description: add/remove hosts
version_added: "2.9"
description:
    - Add or remove hosts from ceph orchestration.
options:
    fsid:
        description:
            - the fsid of the Ceph cluster to interact with.
        required: false
    name:
        description:
            - name of the host
        required: true
    address:
        description:
            - address of the host
        required: true when state is present
    set_admin_label:
        description:
            - enforce '_admin' label on the host specified
              in 'name'
        required: false
        default: false
    labels:
        description:
            - list of labels to apply on the host
        required: false
        default: []
    state:
        description:
            - if set to 'present', it will ensure the name specified
              in 'name' will be present.
            - if set to 'present', it will remove the host specified in
              'name'.
            - if set to 'drain', it will schedule to remove all daemons
              from the host specified in 'name'.
        required: false
        default: present
author:
    - Guillaume Abrioux <gabrioux@redhat.com>
'''

EXAMPLES = '''
- name: add a host
  ceph_orch_host:
    name: my-node-01
    address: 10.10.10.101

- name: add a host
  ceph_orch_host:
    name: my-node-02
    labels:
      - mon
      - mgr
      - grp013
    address: 10.10.10.102

- name: remove a host
  ceph_orch_host:
    name: my-node-01
    state: absent
'''


def get_current_state(module: "AnsibleModule") -> Tuple[int, List[str], str, str]:
    cmd = build_base_cmd(module)
    cmd.extend(['host', 'ls', '--format', 'json'])
    rc, out, err = module.run_command(cmd)

    if rc:
        raise RuntimeError(err)

    return rc, cmd, out, err


def update_label(module: "AnsibleModule",
                 action: str,
                 host: str,
                 label: str = '') -> Tuple[int, List[str], str, str]:
    cmd = build_base_cmd(module)
    cmd.extend(['host', 'label', action,
                host, label])
    rc, out, err = module.run_command(cmd)

    if rc:
        raise RuntimeError(err)

    return rc, cmd, out, err


def update_host(module: "AnsibleModule",
                action: str,
                name: str,
                address: str = '',
                labels: List[str] = None) -> Tuple[int, List[str], str, str]:
    cmd = build_base_cmd(module)
    cmd.extend(['host', action, name])
    if action == 'add':
        cmd.append(address)
    if labels:
        cmd.extend(labels)
    rc, out, err = module.run_command(cmd)

    if rc:
        raise RuntimeError(err)

    return rc, cmd, out, err


def main() -> None:
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            address=dict(type='str', required=False),
            set_admin_label=dict(type=bool, required=False, default=False),
            labels=dict(type=list, required=False, default=[]),
            state=dict(type='str',
                       required=False,
                       choices=['present', 'absent', 'drain'],
                       default='present'),
            docker=dict(type=bool,
                        required=False,
                        default=False),
            fsid=dict(type='str', required=False)
        ),
        required_if=[['state', 'present', ['address']]]
    )

    name = module.params.get('name')
    address = module.params.get('address')
    set_admin_label = module.params.get('set_admin_label')
    labels = module.params.get('labels')
    state = module.params.get('state')

    startd = datetime.datetime.now()
    changed = False

    cmd = ['cephadm']

    rc, cmd, out, err = get_current_state(module)
    current_state = json.loads(out)
    current_names = [name['hostname'] for name in current_state]

    if state == 'present':
        if name in current_names:
            current_state_host = [host for host in current_state if host['hostname'] == name][0]
            if set_admin_label:
                labels.append('_admin')
            if labels:
                differences = set(labels) ^ set(current_state_host['labels'])
                if differences:
                    _out = []
                    for diff in differences:
                        if diff in current_state_host['labels']:
                            action = 'rm'
                        else:
                            action = 'add'
                        rc, cmd, out, err = update_label(module, action, current_state_host['hostname'], diff)
                        _out.append(out)
                        if rc:
                            exit_module(rc=rc,
                                        startd=startd,
                                        module=module,
                                        cmd=cmd,
                                        out=out,
                                        err=err,
                                        changed=False)
                    exit_module(rc=rc,
                                startd=startd,
                                module=module,
                                cmd=cmd,
                                out=''.join(_out),
                                err=err,
                                changed=True)
                out = '{} is already present, skipping.'.format(name)
        else:
            rc, cmd, out, err = update_host(module, 'add', name, address, labels)
            if not rc:
                changed = True

    if state in ['absent', 'drain']:
        if name not in current_names:
            out = '{} is not present, skipping.'.format(name)
        else:
            rc, cmd, out, err = update_host(module, state, name)
            changed = True

    if module.check_mode:
        exit_module(
            module=module,
            out='',
            rc=0,
            cmd=cmd,
            err='',
            startd=startd,
            changed=False
        )
    else:
        exit_module(
            module=module,
            out=out,
            rc=rc,
            cmd=cmd,
            err=err,
            startd=startd,
            changed=changed
        )


if __name__ == '__main__':
    main()
