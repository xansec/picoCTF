# Development Environment

This is the configuration and `ansible` inventory that are used by the default
`Vagrantfile`. This is customized for a simple, yet representative, development
environment.

If you are using this as a development environment, either to work on the
picoCTF platform or develop challenges, you should not need to modify any files
in this directory.

If you are looking to use the local Vagrant VMs for some other purpose, such as
a local event, you will want to make a copy of this `env_dev` directory and
modify the configurations accordingly (e.g. setting passwords). If you are
interested in additional configuration parameters, please consult the
[env_prod][e] directory.

[e]:../env_prod

## Usage

1. Build the virtual machines and install the picoCTF platform.
```
vagrant up
```

For more information on using vagrant consult the [documentation][vd] and
commands such as `vagrant ssh shell` which will provide you a terminal on the
`shell` server where you can use `shell_manager` to manually deploy challenges
or `vagrant reload --provision` which will ensure the platform is properly
installed and configured.

[vd]:../docs/vagrant.md

2. Use `ansible` to apply changes.

This is the preferred way of interacting with the machines once they are created
(as opposed to using `vagrant` or `ssh`). By using the provided playbooks you
ensure that all of your changes are replicable and will work just as well in
a remote production environment.

This does require you to have `ansible` installed on your local machine.

```
ansible-playbook  site.yml
```

Will run all the platform provisioning steps on both `web` and `shell`. This
will take some time and is essentially what is performed the first time you run
`vagrant up` or `vagrant reload --provision`

You can limit the tasks to just a single host:

```
ansible-playbook site.yml --limit web
```

As well as run just a portion of the playbook (e.g. just the `pico-web` tasks).
This will speed up the process.

```
ansible-playbook site.yml --limit web --tags pico-web
```

## Organization

- `ansible.cfg`: points to the relevant roles from both core `picoCTF` as well
- `inventory.yml`: sets all the configurable variables for platform deployment
- `site.yml`: main playbook used to configure the picoCTF platform

### inventory.yml

This inventory file serves to specify two important things.

1. Hosts
2. Variables

Since this inventory is already configured for the local development environment
you should not need to make any changes, however a better understanding will
help you understand the configurable options that are available with the picoCTF
platform.

**Hosts**. These are the machines created with the provided `Vagrantfile`. This
specifies how `ansible` can connect to the machines. In the default case
`vagrant` will set each machine up with a custom `private_key` file. This allows
`vagrant ssh` to work. We also use this key to connect to the machines without
needing a password.

**Variables**. These are configurable options which determine how the platform
is deployed. Again in the local development environment these are tailored for
convenience (e.g. automatically add a shell server and challenges) as well as
simplicity (e.g. no passwords) and should not need to be changed.

### site.yml

This is an `ansible` "playbook". A playbook  matches hosts from the inventory to
the "roles" which should be run on them.

For example:

```
- hosts: shell
  become: yes
  become_method: sudo
  roles:
    - {role: common     , tags: ["common"]}
    - {role: pico-docker, tags: ["pico-docker"]}
    - {role: pico-shell , tags: ["pico-shell"]}
```

This causes the tasks from the `common`, `pico-docker`, and `pico-shell` roles
to run on the `shell` host. Ansible knows how to connect to the `shell` host
because it is configured in the `inventory.yml` hosts section. These roles
perform all the necessary steps to setup a picoCTF shell server, including
installing the `shell_manger` utility, the custom SSH pam modules, and
a `docker` daemon. These roles are configurable by the vars section of the
`inventory.yml`
