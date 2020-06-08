# Ansible Notes

These notes cover how we use [Ansible](https://www.ansible.com/) to provision,
configure, and administer the picoCTF platform.

The goal is that nothing should have to be done as a one off on the command
line. Every dependency, configuration, or process should be documented in code
or a configuration and then applied using Ansible.

This automation drastically simplifies the process of getting blank machines to
run the picoCTF platform. By using the same playbooks across the board we
achieve a robust, repeatable, and consistent experience across development and
production.  Additionally this allows the picoCTF platform to be deployed in
a wide variety of configurations with minor configuration changes.

## Tags

Tags are a convenient way of only running some tasks from the overall playbook.
Some common tags:


- `dependency`: runs dependencies
- `sync`: syncs source code
- `web`
  - `web-api`
  - `web-static`
- `shell`
  - `shell-api`
  - `deploy-all`
