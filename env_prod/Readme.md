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

1. In the [terraform directory][td] edit `variables.tf` and `terraform apply`.
  a. Read through the [terraform/README.md][tr] for more details.
  b. This creates the virtual machines on AWS

[td]:./terraform

2. In this directory edit `inventory.yml`.
  a. The minimal thing you will need to edit are the `ansible_host` for both
  `shell` and `web`. These can be the IP addresses as provided by `terraform` or
  they can be domain names.
  b. Using domain names is recommended, but you will have you configure those
  records manually with your DNS registrar.

3. Generate secure secrets and credentials to be stored in an `ansible-vault`.

```
./gen_vault.py
```

4. Provision the infrastructure.

```
ansible-playbook 00_bootstrap.yml
```

Once that successfully completes your CTF should be up and running. You can browse to
your web elastic IP address and register (the first account will be your admin).

## Secure Secrets (ansible-vault)

In a production setup you will have a number of sensitive variables such as
passwords and secret values. In order to store these securely, while still
allowing automation, we use ansible-vault. With ansible-vault your secrets are
stored in an  encrypted file and only decrypted with a password when a playbook
is run. For more information please consult the [documentation][ad]

[ad]:http://docs.ansible.com/ansible/playbooks_vault.html

In order to make this process smooth, we have provided a script
(`./gen_vault.py`) which chooses random values for all necessary secrets and
passwords and properly encrypts them to produce `vault.yml`. Since it is
encrypted you can (and should) commit `vault.yml` into git.

### Password

The current setup balances convenience with security and writes your password to
a plain text file (`vault_pass.txt`) which is then loaded by default in the
`ansible.cfg`. You should not commit this file (it is `.gitignore`'d by
default). If you do not like this behavior you can remove the file and edit
`ansible.cfg` to instead prompt you or use one of the other mechanisms for
providing a `vault-pass`

### View your secrets

```
ansible-vault view vault.yml
```

### Edit your secrets

Currently the picoCTF automation does not support changing all secrets in an
automated fashion.

If you have an existing platform deployed and want to change your credentials it
is recommend that you do so manually and then update the `vault.yml` with:

```
ansible-vault edit vault.yml
```

### Re-key your vault

Re-keying is the process of changing the password that secures your vault. It
does not change any of the protected secrets.

```
ansible-vault rekey vault.yml
```

Once you do this you will need to update `vault_pass.txt` with your new password
(if you are using it).
