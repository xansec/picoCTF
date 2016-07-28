# picoCTF

The picoCTF platform is the infrastructure which is used to run
[picoCTF](https://picoctf.com/).

The platform is designed to be easily adapted to other CTF or
programming competitions. Additional documentation can be found on the
[wiki](https://github.com/picoCTF/picoCTF/wiki).

## Development Environment Quick Start

The following steps will use [Vagrant](https://www.vagrantup.com/) to
get you quickly up and running with the picoCTF platform by deploying
the code base to two local virtual machines.

1. `git clone https://github.com/picoCTF/picoCTF.git`
2. `cd picoCTF`
3. `vagrant up`
4. Navigate to http://192.168.2.2/
5. Register an account (this user will be the site administrator)

## Current Development

The picoCTF platform is currently being developed towards
version 3. This adds a number of features such as:
- Standardized challenge deployment
- Auto generated/Templated challenges
- Shell server support
- Automated provisioning, locally and in the cloud

If you are coming from
[picoCTF-Platform-2](https://github.com/picoCTF/picoCTF-platform-2)
please read the documentation on the wiki for
[forks of picoCTF-Platform-2](https://github.com/picoCTF/picoCTF/wiki/Repository-linage#forks-of-picoctf-platform-2).

## Project Overview

This project is broken down into a few discrete components that
compose to build a robust and full featured CTF platform. Specifically
the project is consists of the following:

1. [picoCTF-web](./picoCTF-web)
2. [picoCTF-shell](./picoCTF-shell)
3. [problems](./problems)
4. [ansible](./ansible)
5. [terraform](./terraform)
5. [vagrant examples](./vagrant)

Note: we keep everything in one repository so that anyone can bring up
the whole infrastructure at once. We've tried alternate methods, e.g.,
submodules, but we've found the one-big-repo workflow works best for
us.


### picoCTF-web

The competitor facing web site, the API for running a CTF, and the
management functionality for CTF organizers.  The development
[Vagrantfile](./Vagrantfile)) deploys picoCTF-web to a virtual machine
(web) at http://192.168.2.2/. If you want to modify the look and feel
of the website, this is the place to start.

### picoCTF-shell-manager

The tools to create, package, and deploy challenges for use with the
picoCTF platform. This supports the deployment of auto-generated
challenge instances and provides competitors shell access to aid in
challenge solving. The development [Vagrantfile](./Vagrantfile)
deploys the shell-server as a second virtual machine (shell) at
http://192.168.2.3/. If you want to modify challenge deployment
primitives, this is the place to start.

### picoCTF Compatible Problems

Example challenges that are compatible with the picoCTF platform.
These challenges can be easily shared, deployed, or adapted for use in
a CTF.  The development [Vagrantfile](./Vagrantfile) installs these
examples to the shell server and loads them into the web interface.
If you want to see how to create challenges or leverage the hacksport
library, this is the place to start.

### Ansible for Automated System Administration

The tool we use to install, configure, deploy, and administer the
picoCTF platform is [Ansible](https://www.ansible.com/).  This allows
us to create flexible, parameterized, automated playbooks and roles
that apply across development, staging, and production environments.
If you want to modify way the platform is configured, this is the
place to start.

### Terraform for automated AWS deployment

The tool we use to codify our infrastructure as code is
[Terraform](https://www.terraform.io/). This allows a simple process
for creating, destroying, and managing a public deployment of the
platform.  If you want to run a live competition on AWS, this is the
place to start.


## Credits

  - picoCTF PI: David Brumley
  - Copyright: Carnegie Mellon University
  - License: [MIT](./LICENSE)
  - Bug Reports: [GitHub Issues](https://github.com/picoCTF/picoCTF/issues)
  - Contributors (in no particular order): David Brumley, Tim Becker,
    Chris Ganas, Roy Ragsdale, Peter Chapman, Jonathan Burket, Collin
    Petty, Tyler Nighswander, Garrett Barboza
