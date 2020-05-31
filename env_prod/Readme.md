# Production Environment

This directory contains an automated way of deploying the picoCTF platform to
Amazon Web Services (AWS) for a public event. Before attempting to use this
configuration we strongly recommend you familiarize yourself with the provided
[Development Environment][dev] and supporting local development
[Vagrantfile][v].

This production environment provisions and configures the same two machine
(`web` and `shell`), but instead of using `Vagrant` uses `terraform` to create
the necessary "hardware" on AWS. Aside from this change in how the machines are
created all of the [ansible][a] automation remains the same. 

[dev]:../env_dev
[v]:../Vagrantfile
[a]:../ansible

## Assumptions

This guide assumes the following:

- cloned the repository
- have `ansible` and `terraform` installed locally
- have AWS credentials
- have shared ssh keys

## Ansbile and Terraform

Tested using `ansible 2.9.6` from [provider][a].

[a]:https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#installing-ansible-on-ubuntu

Using `Terraform v0.12.24` from [provider][t]

[t]:https://www.terraform.io/downloads.html


##  Quick Start

From your local machine (make sure the assumptions above are met).

1. In the [terraform directory][td] edit `variables.tf` and `terraform apply`
  a. Read through the [terraform/README.md][tr] for more details.
  b. This creates the virtual machines on AWS

[td]:./terraform

2. In this directory edit `inventory.yml`
  a. The minimal thing you will need to edit are the `ansible_host` for both
  `shell` and `web`. These can be the IP addresses as provided by `terraform` or
  they can be domain names.
  b. Using domain names is recommended, but you will have you configure those
  records manually with your DNS registrar.

3. Provision the infrastructure

```
ansible-playbook 00_bootstrap.yml
```

Once that successfully completes your CTF should be up and running. You can browse to
your web elastic IP address and register (the first account will be your admin).

## XXX Review

4. Update the appropriate ansible vault. You must update the passwords in your group_vars [vault.yml](../ansible/group_vars/remote_aws/vault.yml). Pico developed [rekey.py](../deploy/rekey.py) to assist in this process. You can also manually update these values simply by running the command `ansible-vault edit vault.yml` with the password of **pico**. The most important piece is that the `vault_shell_admin_password_crypt` must be the correctly formated hash of the `vault_shell_pass`. You can generate this hash on your own simply by running `perl -e 'print crypt("<vault_shell_pass>","\$6\$saltsalt\$") . "\n"'` in addition to the method suggested in the current _vault.yml_. You should also change your vault password with `ansible-vault rekey vault.yml`.

When prompted, the default vault password is `pico` (you should have changed
that however in the above step).
