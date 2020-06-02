# Tasks

This directory contains a number of `ansible` task lists. These are common
administrative tasks that should be standardized and reused. Since they are all
relatively simple, only a few commands/modules, we opt to capture them here
rather than as full `ansible` roles.

These tasks can be imported in a playbooks with `import_tasks`, where they are
assigned to run on specific hosts.

This is demonstrated in the `env_dev/00_platform.yml` playbook:

```
- hosts: shell
  become: yes
  become_method: sudo
  pre_tasks:
    - import_tasks: "../ansible/tasks/vagrant_shell_bootstrap.yml"
```
