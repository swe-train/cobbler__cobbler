"""
Copyright 2014-2015. Jorgen Maas <jorgen.maas@gmail.com>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
02110-1301  USA
"""
from typing import Union

import netaddr
import re
import shlex

from cobbler.cexceptions import CX


RE_OBJECT_NAME = re.compile(r'[a-zA-Z0-9_\-.:]*$')
RE_HOSTNAME = re.compile(r'^([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])(\.([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9]))*$')

REPO_BREEDS = ["rsync", "rhn", "yum", "apt", "wget"]

VIRT_TYPES = ["<<inherit>>", "xenpv", "xenfv", "qemu", "kvm", "vmware", "openvz"]
VIRT_DISK_DRIVERS = ["<<inherit>>", "raw", "qcow2", "qed", "vdi", "vmdk"]

# blacklist invalid values to the repo statement in autoinsts
AUTOINSTALL_REPO_BLACKLIST = ['enabled', 'gpgcheck', 'gpgkey']


def object_name(name: str, parent: str) -> str:
    """
    Validate the object name.

    :param name: object name
    :param parent: Parent object name
    :returns: name or CX
    """
    if not isinstance(name, str) or not isinstance(parent, str):
        raise CX("Invalid input, name and parent must be strings")
    else:
        name = name.strip()
        parent = parent.strip()

    if name != "" and parent != "" and name == parent:
        raise CX("Self parentage is not allowed")

    if not RE_OBJECT_NAME.match(name):
        raise CX("Invalid characters in name: '%s'" % name)

    return name


def hostname(dnsname: str) -> str:
    """
    Validate the dns name.

    :param dnsname: Hostname or FQDN
    :returns: dnsname
    :raises CX: If the Hostname/FQDN is not a string or in an invalid format.
    """
    if not isinstance(dnsname, str):
        raise CX("Invalid input, dnsname must be a string")
    else:
        dnsname = dnsname.strip()

    if dnsname == "":
        # hostname is not required
        return dnsname

    if not RE_HOSTNAME.match(dnsname):
        raise CX("Invalid hostname format (%s)" % dnsname)

    return dnsname


def mac_address(mac: str, for_item=True) -> str:
    """
    Validate as an Eternet mac address.

    :param mac: mac address
    :param for_item: If the check should be performed for an item or not.
    :returns: str mac or CX
    """
    if not isinstance(mac, str):
        raise CX("Invalid input, mac must be a string")
    else:
        mac = mac.lower().strip()

    if for_item is True:
        # this value has special meaning for items
        if mac == "random":
            return mac

        # copying system collection will set mac to ""
        # netaddr will fail to validate this mac and throw an exception
        if mac == "":
            return mac

    if not netaddr.valid_mac(mac):
        raise CX("Invalid mac address format (%s)" % mac)

    return mac


def ipv4_address(addr: str) -> str:
    """
    Validate an IPv4 address.

    :param addr: IPv4 address
    :returns: str addr or CX
    """
    if not isinstance(addr, str):
        raise CX("Invalid input, addr must be a string")
    else:
        addr = addr.strip()

    if addr == "":
        return addr

    if not netaddr.valid_ipv4(addr):
        raise CX("Invalid IPv4 address format (%s)" % addr)

    if netaddr.IPAddress(addr).is_netmask():
        raise CX("Invalid IPv4 host address (%s)" % addr)

    return addr


def ipv4_netmask(addr: str) -> str:
    """
    Validate an IPv4 netmask.

    :param addr: ipv4 netmask
    :returns: str addr or CX
    """
    if not isinstance(addr, str):
        raise CX("Invalid input, addr must be a string")
    else:
        addr = addr.strip()

    if addr == "":
        return addr

    if not netaddr.valid_ipv4(addr):
        raise CX("Invalid IPv4 address format (%s)" % addr)

    if not netaddr.IPAddress(addr).is_netmask():
        raise CX("Invalid IPv4 netmask (%s)" % addr)

    return addr


def ipv6_address(addr: str) -> str:
    """
    Validate an IPv6 address.

    :param addr: ipv6 address
    :returns: The ipv6 address.
    """
    if not isinstance(addr, str):
        raise CX("Invalid input, addr must be a string")
    else:
        addr = addr.strip()

    if addr == "":
        return addr

    if not netaddr.valid_ipv6(addr):
        raise CX("Invalid IPv6 address format (%s)" % addr)

    return addr


def name_servers(nameservers: Union[str, list], for_item: bool = True) -> Union[str, list]:
    """
    Validate nameservers IP addresses, works for IPv4 and IPv6

    :param nameservers: string or list of nameserver addresses
    :param for_item: enable/disable special handling for Item objects
    :return: The list of valid nameservers.
    """
    if isinstance(nameservers, str):
        nameservers = nameservers.strip()
        if for_item is True:
            # special handling for Items
            if nameservers in ["<<inherit>>", ""]:
                return nameservers

        # convert string to a list; do the real validation
        # in the isinstance(list) code block below
        nameservers = shlex.split(nameservers)

    if isinstance(nameservers, list):
        for ns in nameservers:
            ip_version = netaddr.IPAddress(ns).version
            if ip_version == 4:
                ipv4_address(ns)
            elif ip_version == 6:
                ipv6_address(ns)
            else:
                raise CX("Invalid IP address format")
    else:
        raise CX("Invalid input type %s, expected str or list" % type(nameservers))

    return nameservers


def name_servers_search(search: Union[str, list], for_item: bool = True) -> Union[str, list]:
    """
    Validate nameservers search domains.

    :param search: One or more search domains to validate.
    :param for_item: (enable/disable special handling for Item objects)
    :return: The list of valid nameservers.
    """
    if isinstance(search, str):
        search = search.strip()
        if for_item is True:
            # special handling for Items
            if search in ["<<inherit>>", ""]:
                return search

        # convert string to a list; do the real validation
        # in the isinstance(list) code block below
        search = shlex.split(search)

    if isinstance(search, list):
        for sl in search:
            hostname(sl)
    else:
        raise CX("Invalid input type %s, expected str or list" % type(search))

    return search

# EOF
