#!/usr/bin/env python3
# -*- coding: utf-8 -*-

try:
    from ipset import Ipset,Entry
except ModuleNotFoundError:
    from .ipset import Ipset,Entry
from time import time
import re

class Net:
    """
    A class made for network access control and bandwidth accounting based on linux ipsets.
    This spawn 2 ipsets for up and down bandwidth accounting.
    Instantiating it require root priviledges.
    For applicable commands, the command they run are indicated. This is indicative only, and
    won't include any optional parameters that are actually set.
    """

    def __init__(self, name="langate", mark=(0, 1)):
        """
        Create ipsets for access control and bandwidth accounting.
        Equivalent to:
        `ipset create langate hash:mac`

        :param name: name of the ipset. Second one will be <name>-reverse
        :param mark: tuple containing min mark and how many vpns to use
        """
        self.ipset = Ipset(name)
        self.ipset.create("hash:mac", skbinfo=True, comment=True)
        self.mark_start, self.mark_mod = mark
        self.mark_current = 0
        self.logs = list()

    def generate_iptables(self, match_internal = "-s 172.16.0.0/255.252.0.0", stop = False):
        pass

    def connect_user(self, mac, name=None, timeout=None, mark=None):
        """
        Add an entry to the ipsets.
        Equivalent to:
        `ipset add langate <mac>`

        :param mac: mac address of the user.
        :param name: name of the entry, stored as comment in the ipset.
        :param timeout: timeout of the entry. None for an entry that does not disapear.
        :param mark: mark for the entry. None to let the module balance users itself.
        """
        if mark is None:
            mark = self.mark_current + self.mark_start
            self.mark_current = (self.mark_current+1) % self.mark_mod
        self.ipset.add(Entry(mac, skbmark=mark, comment=name))

    def disconnect_user(self, mac):
        """
        Remove an entry from the ipsets.
        Equivalent to:
        `ipset del langate <entry mac>`

        :param mac: mac of the user.
        """
        self.ipset.delete(mac)
        pass

    def get_user_info(self, mac):
        """
        Get users information from his mac address.
        Equivalent to:
        `sudo ipset list langate`
        plus some processing

        :param mac: mac address of the user.
        :return: User class containing their bandwidth usage and mark
        """
        entries = self.ipset.list().entries
        for entry in entries:
            if entry.elem == mac.upper():
                mark = entry.skbmark[0] if entry.skbmark else None
                name = entry.comment
                break
        else:
            return None

        return User(mac, mark, name=name)

    def clear(self):
        """
        Remove all entry from the set.
        Equivalent to:
        `ipset flush langate`
        """
        self.ipset.flush()


    def get_all_connected(self):
        """
        Get all entries from the set.
        Equivalent to:
        `ipset list langate`

        :return: Dictionary mapping mac to a User class
        """
        entries = self.ipset.list().entries
        users = dict()
        for entry in entries:
            mac = entry.elem
            mark = entry.skbmark[0] if entry.skbmark else None
            name = entry.comment
            users[mac] = User(mac, mark, name=name)

        return users

    def delete(self):
        """
        Delete the set. After calling this function, the sets can't be used anymore as it no longer exist.
        Equivalent to:
        `sudo ipset destroy langate`
        """
        self.ipset.destroy()

    def get_balance(self):
        """
        Get mapping from vpn to user mac.
        Equivalent to:
        `ipset list langate`

        -> Dict[int, Set[mac]]

        :return: Dictionary composed of vpn and set of mac addresses
        """
        entries = self.ipset.list().entries
        balance = dict()
        for entry in entries:
            skbmark = entry.skbmark[0] if entry.skbmark else None
            if skbmark not in balance:
                balance[skbmark] = set()
            balance[skbmark].add(entry.elem)

        return balance

    def set_vpn(self, mac, vpn):
        """
        Move an user to a new vpn.
        Does not modify an entry not already in.
        Equivalent to:
        `ipset list langate` plus
        `ipset add langate <mac>`

        :param mac: mac address of the user.
        :param vpn: Vpn where move the user to.
        """
        entries = self.ipset.list().entries
        if type(vpn) is int:
            vpn = (vpn, (1<<32)-1)
        for entry in entries:
            if entry.elem == mac:
                entry.skbmark = vpn
                self.ipset.add(entry)
                break
        else:
            pass # not found


def verify_mac(mac: str) -> bool:
    """
    Verify if mac address is correctly formed.

    :param mac: Mac address to verify.
    :return: True is correctly formed, False if not.
    """
    return bool(re.match(r'^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$', mac))


def verify_ip(ip: str) -> bool:
    """
    Verify if ip address is correctly formed.

    :param ip: Ip address to verify.
    :return: True is correctly formed, False if not.
    """
    return bool(re.match(r'^([0-9]{1,3}\.){3}[0-9]{1,3}$', ip))


def get_ip(mac: str) -> str:
    """
    Get the ip address associated with a given mac address.

    :param mac: Mac address of the user.
    :return: Ip address of the user.
    """
    if not verify_mac(mac):
        raise InvalidAddressError("'{}' is not a valid mac address".format(mac))
    f = open('/proc/net/arp', 'r')
    lines = f.readlines()[1:]
    for line in lines:
        if line.startswith(mac, 41):  # 41=offset in line
            return line.split(' ')[0]
    raise UnknownAddress("'{}' does not have a known ip".format(mac))


# get mac from ip
def get_mac(ip: str) -> str:
    """
    Get the mac address associated with a given ip address.

    :param ip: Ip address of the user.
    :return: Mac address of the user.
    """
    if not verify_ip(ip):
        raise InvalidAddressError("'{}' is not a valid ip address".format(ip))
    f = open('/proc/net/arp', 'r')
    lines = f.readlines()[1:]
    for line in lines:
        if line.startswith(ip, 0):  # 41=offset in line
            return line[41:].split(' ')[0]
    raise UnknownAddress("'{}' does not have a known mac".format(ip))


class User:
    """
    A dataclass to help represent a single user.
    Depending on situations, up and down may represent total bandwidth usage,
    or usage since previous entry
    """
    def __init__(self, mac, mark, name=None):
        self.mac = mac
        self.mark = mark
        self.name = name

    def to_dict(self):
        return {
            "mac": self.mac,
            "mark": self.mark,
            "name": self.name,
        }
