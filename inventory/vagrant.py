#!/usr/bin/env python3
"""
{
    "minikube": {"hosts": ["minikube"]},
    "meta_info": {
        "hostvars": {
            "minikube": {
                "ansible_host": "127.0.0.1",
                "ansible_port": "2222",
                "ansible_user": "vagrant",
                "ansible_ssh_private_key_file": "/path/to/.vagrant/machines/vagrant0/virtualbox/private_key",
                "ansible_ssh_common_args": "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null",
            },
        }
    },
}
"""

# Standard Library
import argparse
import json
import logging
import subprocess
import sys
import typing as t
from logging import getLogger

# Third Party Library
import paramiko
from pydantic import BaseModel
from pydantic import Field

logging.basicConfig(
    format="[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)d] - %(message)s",
    level=logging.WARNING,
)
logger = getLogger(__name__)
# logger.setLevel(logging.INFO)


class Meta(BaseModel):
    hostvars: t.Dict[str, t.Any]


class VagrantHost(BaseModel):
    ansible_host: str
    ansible_port: str
    ansible_user: str
    ansible_ssh_private_key_file: str
    ansible_ssh_common_args: str


class GroupModel(BaseModel):
    vars: t.Optional[t.Dict[str, t.Any]] = None
    hosts: t.List[str] = Field(default_factory=list)
    children: t.List[str] = Field(default_factory=list)


class ListOutputModel(BaseModel):
    vagrants: GroupModel
    minikube: GroupModel
    alias_meta: t.Optional[Meta] = Field(alias="_meta")


class Args(BaseModel):
    list: bool
    host: str


def parse_args() -> Args:
    parser = argparse.ArgumentParser(description="Vagrant inventory script")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true")
    group.add_argument("--host", type=str)
    _args = parser.parse_args()
    return Args(
        list=_args.list,
        host=_args.host if not _args.list else "",
    )


class VagrantInventory:
    def __init__(self) -> None:
        args = parse_args()
        if args.list:
            list_output = self.format_list_output()
            logger.info(f"{list_output=}")
            json.dump(list_output.dict(by_alias=True, exclude_none=True), sys.stdout)
        else:
            host: VagrantHost = self.get_host_details(args.host)
            json.dump(host.dict(by_alias=True, exclude_none=True), sys.stdout)

    def format_list_output(self) -> ListOutputModel:

        vagrants_group: GroupModel = GroupModel(hosts=self.list_running_hosts())
        vagrant_name_set: t.Set[str] = set(vagrants_group.hosts)

        minikube_group: GroupModel = GroupModel(hosts=["minikube"])
        if not set(minikube_group.hosts).issubset(vagrant_name_set):
            raise ValueError(f"{ minikube_group.hosts } is not a subset of { vagrant_name_set }")

        return ListOutputModel(
            vagrants=vagrants_group,
            minikube=GroupModel(hosts=["minikube"]),
            _meta=Meta(hostvars={name: self.get_host_details(name) for name in vagrant_name_set}),
        )

    def list_running_hosts(self) -> t.List[str]:
        """List runnning host names"""
        vagrant_list: t.List[str] = []

        cmd: str = "vagrant status --machine-readable"
        status: str = subprocess.check_output(cmd.split()).decode(sys.stdout.encoding)

        host: str
        key: str
        value: str
        for line in status.splitlines():
            (_, host, key, value) = line.split(",")[:4]
            if key == "state" and value == "running":
                vagrant_list.append(host)
        return vagrant_list

    def get_host_details(self, host: str) -> VagrantHost:
        cmd: str = f"vagrant ssh-config {host}"
        p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
        config: paramiko.SSHConfig = paramiko.SSHConfig()
        if p.stdout is None:
            raise Exception("paramiko.SSHConfig return no stdout")
        out: str = p.stdout.read().decode(sys.stdout.encoding)
        config.parse(out.splitlines())
        c: paramiko.config.SSHConfigDict = config.lookup(host)
        return VagrantHost(
            ansible_host=c["hostname"],
            ansible_port=c["port"],
            ansible_user=c["user"],
            ansible_ssh_private_key_file=c["identityfile"][0],
            ansible_ssh_common_args="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null",
        )


def main() -> None:
    VagrantInventory()


if __name__ == "__main__":
    main()
