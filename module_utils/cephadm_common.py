def container_exec(binary, container_image, interactive=False):
    '''
    Build the docker CLI to run a command inside a container
    '''

    container_binary = os.getenv('CEPH_CONTAINER_BINARY', 'podman')
    command_exec = [container_binary, 'run']

    if interactive:
        command_exec.extend(['--interactive'])

    command_exec.extend(['--rm',
                         '--net=host',
                         '-v', '/etc/ceph:/etc/ceph:z',
                         '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                         '-v', '/var/log/ceph/:/var/log/ceph/:z',
                         '--entrypoint=' + binary, container_image])
    return command_exec

def pre_generate_ceph_cmd(container_image=None, interactive=False):
    '''
    Generate ceph prefix comaand
    '''
    if container_image:
        cmd = container_exec('ceph', container_image, interactive=interactive)
    else:
        cmd = ['ceph']

    return cmd

def generate_ceph_cmd(sub_cmd, args, user_key=None, cluster='ceph', user='client.admin', container_image=None, interactive=False):
    '''
    Generate 'ceph' command line to execute
    '''

    if not user_key:
        user_key = '/etc/ceph/{}.{}.keyring'.format(cluster, user)

    cmd = pre_generate_ceph_cmd(container_image=container_image, interactive=interactive)

    base_cmd = [
        '-n',
        user,
        '-k',
        user_key,
        '--cluster',
        cluster
    ]
    base_cmd.extend([sub_cmd])
    cmd.extend(base_cmd + [args])

    return cmd

def exit_module(module, out, rc, cmd, err, startd, changed=False):
    endd = datetime.datetime.now()
    delta = endd - startd

    result = dict(
        cmd=cmd,
        start=str(startd),
        end=str(endd),
        delta=str(delta),
        rc=rc,
        stdout=out.rstrip("\r\n"),
        stderr=err.rstrip("\r\n"),
        changed=changed,
    )
    module.exit_json(**result)


def fatal(message, module):
    '''
    Report a fatal error and exit
    '''

    if module:
        module.fail_json(msg=message, rc=1)
    else:
        raise(Exception(message))
