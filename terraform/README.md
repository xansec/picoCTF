# Terrafrom Notes

These notes cover how to use [Terraform](https://www.terraform.io/) to deploy the picoCTF platform to [Amazon Web Services](https://aws.amazon.com/) (AWS).  We use Terraform to standardize, and version control the configuration of our remote servers. This is like Vagrant for the cloud.

If you are not familiar with Terraform, it is recommended that you read through through the [introduction](https://www.terraform.io/intro/index.html) and [getting started](https://www.terraform.io/intro/getting-started/install.html) prior to deploying picoCTF.

Getting picoCTF deployed to AWS is a two step process. Terraform is the first step to create the virtual machines and configure networking, however this does not actually install or launch the picoCTF platform. For that second step please see the [Ansible Readme](../ansible/README.md).

## **WARNING**
Following this guide will create real resources on AWS that will cost money.  This may only be a few dollars, but we're not responsible for any charges that may incur.  If you're not using your AWS resources be sure to destroy them so you are not charged.  You may be able to run a competition at no cost if your account qualifies under the AWS [free-tier](https://aws.amazon.com/free/) However you should check your bill regularly, especially if this is your first time running a live CTF.

## Pre-Requisites

1. AWS
    - A deployment specific [Identity and Access Management (IAM)](https://console.aws.amazon.com/iam/home) account with at least the `AmazonEC2FullAccess` permission.
    - The following authentication variables `ACCESS_KEY_ID` and `SECRET_ACCESS_KEY` for the account.
2. Terraform
    - Follow the installation [instructions](https://www.terraform.io/intro/getting-started/install.html) on your local host.
    - Or consider using the preconfigured Vagrant [Jump Box](../vagrant/jump_box/).
3. Deployment SSH key
    - This key will be authorized the virtual machines you create on AWS and will allow `ssh` access.
    - You can use an existing key (simply uncomment the configuration in [production/main.tf](../production/main.tf)).
    - Or generate a new environmental specific key with a command like the following:
    - `ssh-keygen -f ~/.ssh/picoCTF_production_rsa -C "admin@picoCTF_production" -N ""`

## Quick Start

This quick start is for a Linux system but the steps should be generally applicable. If you do not have a Linux system easily accessible we recommend using the preconfigured Vagrant [Jump Box](../vagrant/jump_box/) which already has all the necessary tools installed and has been tested to work with this process. At a high level it is as simple as:

1. Providing AWS credentials (through environment variables)
2. Running Terraform.

```
export AWS_ACCESS_KEY_ID="XXX_PUT_AWS_ACCESS_KEY_XXX" 
export AWS_SECRET_ACCESS_KEY="XXX_PUT_AWS_ACCESS_KEY_XXX"

cd production

terraform get
terraform init
terrafrom plan
terraform apply
```

Following these steps will automatically create the following resources on AWS:

1. Virtual Private Cloud (VPC) aka a private network
2. Internet Gateway, Routes, Subnets
3. Security Groups aka firewall rules
4. Instances aka virtual servers
5. Instance Related resources like Elastic IP addresses and Elastic Block Storage

If that completed successfully, you now have two servers (`web` and `shell`) running on AWS ready to host your competition. The IP addresses should have been provided at the completion of `terraform apply`.  In order to actually start a competition you need to provision the servers with [Ansible](../ansible/README.md). 

**NOTE:** You might not see these resources in your [AWS EC2 Dashboard](https://console.aws.amazon.com/ec2/v2/home?region=us-east-1) if your region does not match the region in which you created your terraform instances. The terraform default is **us-east-1 (N. Virgina)**. You can change your AWS default region using the dropdown menu to the left of support (to the right of your user-name).

You should be able to ssh into your remote instances at this point. By default, this script uses `~/.ssh/picoCTF_production_rsa` as your ssh key, and `ubuntu` is the default user account for Ubuntu bionic 18.04 LTS. As such, you can test sshing into your instances using the below command:
    
    ssh -i ~/.ssh/picoCTF_production_rsa ubuntu@<instance-elastic-IP-address>

If you just wanted to test this script and are not ready to run a competition  you should be sure to destroy all the resources that where created.  Don't worry it's just as easy to get them back later thanks to the power of Terraform. To destroy the servers and resources that where created run:

    terraform destroy

Please consider reading along for a more in depth explanation of how our Terraform configuration is structured. Also this will discuss how you can modify the configuration to meet your needs.

## Follow-on Steps

After following above, you will have the bare-boned hardware neccesary to run Pico remotely (on AWS), but these instances have none of the required software installed. Other sections cover the below steps in more detail but here is a quick summary of the basic next steps to get the competition up and running:

1. Deploy (copy) your picoCTF repository to `/picoCTF` on the newly created instances. The below list of steps is the simplest method for demonstration purpose, but [mkdeploy.sh](../mkdeploy.sh) was developed to deploying your own custom repo. Read this script to learn how to use it.
    
    sudo git clone https://github.com/picoCTF/picoCTF.git /picoCTF
    chown -R ubuntu:ubuntu /picoCTF

2. Install ansible on terraformed instances

    chmod +x /picoCTF/vagrant/provision_scripts
    /picoCTF/vagrant/provision_scripts/install_ansible

3. Update the appropriate ansible inventory (see [remote_aws_single_tier_example](../ansible/inventories/remote_aws_single_tier_example) for a very simple example of a single tier AWS inventory).

4. Update the appropriate ansible vault. You must update the passwords in your group_vars [vault.yml](../ansible/group_vars/remote_aws/vault.yml). Pico developed [rekey.py](../deploy/rekey.py) to assist in this process but do not ever reference it in any documentation I could find. You can also manually update these values simply by running the command `ansible-vault edit vault.yml` with the password of **pico**. The most important piece is that the `vault_shell_admin_password_crypt` must be the correctly formated hash of the `vault_shell_pass`. You can generate this hash on your own simply by running `perl -e 'print crypt("<vault_shell_pass>","\$6\$saltsalt\$") . "\n"'` in addition to the method suggested in the current _vault.yml_. You should also change your vault password with `ansible-vault rekey vault.yml`.

5. Run ansible playbook on your terraformed instances. See the [ansible README](../ansible/README.md) for more information but you can simply run `ansible-playbook --vault-id @prompt -i /picoCTF/ansible/inventories/remote_aws --limit="shell"  "$@" site.yml` for shell or `ansible-playbook --vault-id @prompt -i /picoCTF/ansible/inventories/remote_aws --limit="db,web"  "$@" site.yml` for the web/db from `\picoCTF\ansible`. When prompted, the default vault password is `pico` (you should have changed that however in the above step).

At this point, your ctf should be up and running. You can browse to your web elastic IP address and register (the first account will be your admin). You will still need to deploy problems on your shell server as well as to add them your shell server to your web management. You can also simply update *auto_add_shell*, *auto_load_problems*, and *auto_start_competition* in [vars.yml](../ansible/groups_vars/remote_aws/vars.yml) to **True** and re-run your ansible playbook on shell first and then web to automate this process. Good luck.

## Overview of Files

The Terraform configuration is broken down into two primary parts:

1. [Modules](./modules) which contains the building blocks for the picoCTF infrastructure.
2. Environmental configurations such as [production](./production) which compose the basic modules into a specific configuration.

### Modules
Each module represents a specific set of resources that need to be created on AWS. These are functionally broken out into common reusable components and are parameterized to accommodate many possible configurations. At the top of each module file it defines the interface for using the module with `Inputs` and `Outputs`.  Input variable must be passed in when instantiated from configurations such as [production/main.tf](./production/main.tf). Outputs are variables that are then made available to the calling root module for further composition.

Modules do not create resources directly, they are only instantiated through [Environmental Configurations](#environmental-configurations). In general the existing modules should not need modification, you can change how they are composed in an environmental configuration, but certainly you can add any other resources that might be appropriate for your scenario.

On their own each modules only creates a part of the infrastructure necessary to run a competition, however they can also be nested to create a full environment. An example of this is the [single_tier_aws](./modules/single_tier_aws/single_tier_aws.tf) module which forms the baseline deployment configuration for picoCTF.  The `single_tier_aws` module brings together all the other modules necessary and defines sane default configurations.  This single module can then be instantiated in the various environmental configurations.

### Environmental Configurations
Environmental configuration specify how to configure a copy of the picoCTF infrastructure. They provide specific configuration values to instantiate the modules in a manner that is appropriate for the environment. For example your `testing` instances likely do not need to be as large as your `production` instances. Other examples of common configurations that you might changes per environment are ssh keys, tags, and perhaps AWS region.

In the simplest scenario you might only want to deploy the picoCTF platform to production for a live competition. In that case you can focus only on the [production](./production) directory. However it can also be useful to have a testing infrastructure to play test on prior to a competition. These infrastructures might have different resource requirements and be hosting different data, but for consistency sake you want them to be configured the same way.  Terraform makes this easy by allowing you to compose the same building block (modules) into multiple different configurations.

Each environmental configuration will create a separate set of infrastructure, so you if do a `terraform apply` in both `production` and `testing` you will have 4 different servers running (production web and shell, testing web and shell). If you then run `terraform destroy` in the `testing` directory it will remove all those resources, but won't effect your `production` servers.  Each environment will require provisioning and administration, but fortunately [ansible](../ansible) handles most of that complexity for you.

Each environmental configuration is specified in a single file `main.tf`.

#### Terraform Configuration (`main.tf`)
This is the primary file you will want to make changes to if you are using the default configurations.  This configuration creates a running instance of your infrastructure when you run `terraform apply` from an environmental configuration directory. All it does is pass your environmental configuration variables to the appropriate modules (building blocks).

### Terraform State
One particularly important part of using Terraform is keeping track of the [state](https://www.terraform.io/docs/state/). By default this is stored in your environmental configuration directory as `terraform.tfstate`. This is how Terraform knows what resources have been created and what their status. If you don't have this file Terraform will no longer be able to manage your resources and you may have to go into the AWS  [Management Console](https://console.aws.amazon.com) and manually modify/remove orphaned elements.

This repository defaults to ignore `terraform.tfstate` from version control. This is the simplest and works well when there is a single person responsible for deploying your infrastructure.  If a second member of the team wants to modify the current infrastructure they will need to manually copy the `terraform.tfstate` file out of band.

Another method is to commit `terraform.tfstate` into version control. This works well for when you are developing and deploying from a private copy of the repository. Then on every change the `terraform.tfstate` file would be committed and tracked so all users could deploy. 

Alternatively Terraform provides a number of more complex options for [remote state](https://www.terraform.io/docs/state/remote/index.html) that might better suit your needs.

## Common Tasks

### Basic Workflow
1. Make edits to the appropriate configuration file
2. Check what changes it will have
    - `terraform plan`
    - look for things like improperly templated/applied variables
    - `terraform init`
3. Apply the changes
    - `terraform apply` 
4. If you are tracking `terraform.tfstate` in private source control commit the newly modified `terraform.tfstate`

### Rebuild a single server

1. Find resource name
    - `terraform show`
    - ex: `aws_instance.web`
2. Taint the resource
    - `terraform taint aws_instance.web`
    - this will only mark the server for recreation
3. Capture the plan
    - `terraform plan`
    - this should show only the deletion of the instance and perhaps the modification of attached resources (eg: Elastic IP (eip), Elastic Block Storage (ebs)) that rely on the instance id
4. Apply the plan
    - `terraform apply`
    - this is the step that actually destroys the server and creates a new instance
5. Commit the results (only if you are tracking `terraform.tfstate` in private source control)
    - `git add terraform.tfstate*`
    - `git commit -m "[APPLY] - success rebuilding server aws_instance.web"`
8. Remove stale host key
    - `ssh-keygen -f "~/.ssh/known_hosts" -R 203.0.113.254`
6. Test ssh
    - `ssh -i ~/.ssh/picoCTF_production_rsa admin@203.0.113.254`
9. Re-provision/Configure
    - run the relevant ansible playbooks

### Other Notes
- Error waiting for Volume (vol-XYZABC) to detach from Instance
    - This is caused when an instance with an attached volume attempts to mutate
    - Use `terrafrom taint aws_instance.XXX` to cause a full deletion and recreation
    - Check with `terraform plan` then if it makes sense apply with `terraform apply` 
