# Copyright Red Hat
# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
try:
    from ansible.module_utils.cephadm_common import exit_module
except ImportError:
    from module_utils.cephadm_common import exit_module
import datetime


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ceph_orch_host
short_description: Manage Ceph hosts
version_added: "2.10"
description:
    - Manage Ceph hosts
options:
    action:
        description:
            - If 'add' is used, the module will add the host.
            - If 'rm' is used, the module will remove the host.
        required: false
        choices: ['ls', 'add', 'rm']
        default: ls
author:
    - Guillaume Abrioux <gabrioux@redhat.com>
'''

EXAMPLES = '''
- name: list hosts
  ceph_orch_host:
    action: ls
  register: hosts_list
'''

RETURN = '''#  '''


def main():
    module = AnsibleModule(
        argument_spec=dict(
            action=dict(type='str', required=False, default='ls', choices=['add', 'rm', 'ls']),  # noqa: E501
        ),
        supports_check_mode=True,
    )

    action = module.params.get('action')

    startd = datetime.datetime.now()

    if action == 'ls':
        cmd = generate_ceph_cmd('orch', 'ls', cluster=cluster, container_image=container_image)  # noqa: E501

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
        rc, out, err = module.run_command(cmd)
        exit_module(
            module=module,
            out=out,
            rc=rc,
            cmd=cmd,
            err=err,
            startd=startd,
            changed=True
        )


if __name__ == '__main__':
    main()
