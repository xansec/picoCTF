# Development Environment

This is the configuration and `ansible` inventory that are used by the default
`Vagrantfile`.

You should not need to modify any files in this directory.

## Usage

See

```
vagrant up
```

This will provision the vm and install all [challenges](../challenges). The
`Vagrantfile` provided is a simplified version of the default picoCTF [one][v],
adapted for our challenges and additional provisioning steps.

[v]:https://github.com/picoCTF/picoCTF/blob/master/Vagrantfile

You can also interact with this box directly with `ansible`, for example:

```
ansible-playbook site.yml --tags web
```

## Organization

- `ansible.cfg`: points to the relevant roles from both core `picoCTF` as well
- `inventory.yml`: sets all the configurable variables for platform deployment

- `00_platform.yml`: main playbook used by 
