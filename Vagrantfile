# -*- mode: ruby -*-
# vi: set ft=ruby :

# TODO:
# - mount_options looks really fishy
# - use double quote correctly

require 'etc'

# Extract suffix if working directory starts with prefix; otherwise return "".
def compute_auto_name_suffix(prefix = "picoCTF")
  dirname = File.basename(Dir.getwd)
  return dirname.start_with?(prefix) ? dirname[prefix.length..-1] : ""
end

Vagrant.configure("2") do |config|

  config.vm.define "shell", primary: true do |shell|
    shell.vm.box = "ubuntu/bionic64"
    shell.vm.network "private_network", ip: (ENV['SIP'] || '192.168.2.3'), nic_type: "virtio"

    shell.vm.synced_folder ".", "/vagrant", disabled: true
    shell.vm.synced_folder ".", "/picoCTF",
                           owner: "vagrant", group: "vagrant",
                           mount_options: ["dmode=775", "fmode=775"]

    # uses ansible_local so that a user does not need to have ansible installed
    shell.vm.provision :ansible_local do |ansible|
      ansible.install = "yes"
      ansible.install_mode = "default"
      ansible.compatibility_mode = "2.0"
      ansible.playbook = "site.yml"
      ansible.provisioning_path = "/picoCTF/infra_local/"
      ansible.inventory_path = "inventory.yml"
      ansible.extra_vars = {ansible_connection:"local"}
      ansible.verbose = ENV['V']
    end

    shell.vm.provider "virtualbox" do |vb|
      vb.name = "picoCTF-shell-dev" + compute_auto_name_suffix()
      # Overridable settings
      vb.cpus = [(ENV['J'] || '1').to_i, Etc.nprocessors].min
      vb.gui = ENV['G']
      vb.memory = (ENV['M'] || '2').to_i * 1024
      # Others
      vb.customize [
        "modifyvm", :id,
        "--uartmode1", "file", File.join(Dir.pwd, vb.name + "-console.log")
      ]
    end
  end

  config.vm.define "web", primary: true do |web|
    web.vm.box = "ubuntu/bionic64"
    web.vm.network "private_network", ip: (ENV['WIP'] || '192.168.2.2'), nic_type: "virtio"

    web.vm.synced_folder ".", "/vagrant", disabled: true
    web.vm.synced_folder ".", "/picoCTF",
                         owner: "vagrant", group: "vagrant",
                         mount_options: ["dmode=775", "fmode=775"]

    # uses ansible_local so that a user does not need to have ansible installed
    web.vm.provision :ansible_local do |ansible|
      ansible.install = "yes"
      ansible.install_mode = "default"
      ansible.compatibility_mode = "2.0"
      ansible.playbook = "site.yml"
      ansible.provisioning_path = "/picoCTF/infra_local/"
      ansible.inventory_path = "inventory.yml"
      ansible.extra_vars = {ansible_connection:"local"}
      ansible.verbose = ENV['V']
    end

    web.vm.provider "virtualbox" do |vb|
      vb.name = "picoCTF-web-dev" + compute_auto_name_suffix()
      # Overridable settings
      vb.cpus = [(ENV['J'] || '1').to_i, Etc.nprocessors].min
      vb.gui = ENV['G']
      vb.memory = (ENV['M'] || '2').to_i * 1024
      # Others
      vb.customize [
        "modifyvm", :id,
        "--uartmode1", "file", File.join(Dir.pwd, vb.name + "-console.log")
      ]
    end
  end
end
