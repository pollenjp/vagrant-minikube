# coding: utf-8
# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.define 'minikube' do |machine|
    machine.vm.box = "ubuntu/focal64"
    machine.vm.hostname = 'minikube'
    machine.vm.network :private_network,ip: "192.168.56.10"
    machine.vm.provider "virtualbox" do |vbox|
      vbox.gui = false
      vbox.cpus = 4
      vbox.memory = 16384
    end
  end
end
