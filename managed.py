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
    #logs: List[Tuple[time, Dict[ip, (up, down, mark)]]]

    def __init__(self, name="langate", mark=(0, 1)):
        """
        Create ipsets for access control and bandwidth accounting.
        Equivalent to:
        `ipset create langate hash:ip`

        :param name: name of the ipset. Second one will be <name>-reverse
        :param mark: tuple containing min mark and how many vpns to use
        """
        self.ipset = Ipset(name)
        self.reverse = Ipset(name + "-reverse")
        self.ipset.create("hash:ip", comment=True)
        self.reverse.create("hash:ip", skbinfo=False, comment=True)
        self.mark_start, self.mark_mod = mark
        self.mark_current = 0
        self.logs = list()

    def generate_iptables(self, match_internal = "-s 172.16.0.0/255.252.0.0", stop = False):
        pass

    def connect_user(self, ip, name=None, timeout=None, mark=None, up=None, down=None):
        """
        Add an entry to the ipsets.
        Equivalent to:
        `ipset add langate <ip>`

        :param ip: ip address of the user.
        :param name: name of they entry, stored as comment in the ipset.
        :param timeout: timeout of the entry. None for an entry that does not disapear.
        :param mark: mark for the entry. None to let the module balance users itself.
        :param up: set upload byte counter to this value, usefull when moving someone of vpns without losing track of their data.
        :param down: set download byte counter to this value, usefull when moving someone of vpns without losing track of their data.
        """
        if mark is None:
            mark = self.mark_current + self.mark_start
            self.mark_current = (self.mark_current+1) % self.mark_mod
        self.ipset.add(Entry(ip, skbmark=mark, bytes=up, comment=name))
        self.reverse.add(Entry(ip, bytes=down, comment=name))

    def disconnect_user(self, ip):
        """
        Remove an entry from the ipsets.
        Equivalent to:
        `ipset del langate <entry ip>`

        :param ip: ip of the user.
        """
        self.ipset.delete(ip)
        self.reverse.delete(ip)
        pass

    def get_user_info(self, ip):
        """
        Get users information from his ip address.
        Equivalent to:
        `sudo ipset list langate`
        plus some processing

        :param ip: ip address of the user.
        :return: User class containing their bandwidth usage and mark
        """
        entries = self.ipset.list().entries
        for entry in entries:
            if entry.elem == ip:
                mark = entry.skbmark[0] if entry.skbmark else None
                up = entry.bytes or 0
                name = entry.comment
                break
        else:
            return None

        rev_entries = self.reverse.list().entries
        for entry in rev_entries:
            if entry.elem == ip:
                down = entry.bytes or 0
                break
        else:
            down = 0

        return User(ip, mark, up=up, down=down, name=name)

    def clear(self):
        """
        Remove all entry from the set.
        Equivalent to:
        `ipset flush langate`
        """
        self.ipset.flush()
        self.reverse.flush()


    def get_all_connected(self):
        """
        Get all entries from the set.
        Equivalent to:
        `ipset list langate`

        :return: Dictionary mapping ip to a User class
        """
        entries = self.ipset.list().entries
        users = dict()
        for entry in entries:
            ip = entry.elem
            mark = entry.skbmark[0] if entry.skbmark else None
            up = entry.bytes or 0
            name = entry.comment
            users[ip] = User(ip, mark, up=up, name=name)

        rev_entries = self.reverse.list().entries
        for entry in rev_entries:
            if entry.elem in users:
                users[entry.elem].down = entry.bytes or 0

        return users

    def delete(self):
        """
        Delete the set. After calling this function, the sets can't be used anymore as it no longer exist.
        Equivalent to:
        `sudo ipset destroy langate`
        """
        self.ipset.destroy()
        self.reverse.destroy()

    def log_statistics(self):
        """
        Add an entry to internal log.
        Equivalent to:
        `ipset list langate`
        """
        self.logs.append((time(),self.get_all_connected()))

    def get_users_logs(self):
        """
        Get logs by users, sorted by date.
         -> List[Tuple[time, Dict[str, User]]]

        :return: List sorted by date of tuple of date and dictionary, itself mapping device ip to User
        """
        res = list()
        for ((new_time, new_dict), (old_time, old_dict)) in zip(self.logs[1:], self.logs):
            partial = dict()
            for k in new_dict:
                new = new_dict[k]
                if k in old_dict:
                    old = old_dict[k]

                    partial[k] = (new.up-old.up, new.down-old.down, new.mark)
                else:
                    partial[k] = (new.up, new.down, new.mark)

            res.append(((new_time + old_time)/2, partial))

        return res

    def get_vpn_logs(self):
        """
        Get logs by vpn sorted by date.
         -> List[Tuple[time, Dict[int, Tuple[int, int]]]]

        :return: List sorted by date of tuple of date and dictionary, vpn it's bandwith usage since last entry
        """
        res = list()
        for time,users in self.get_users_logs():
            partial = dict()
            for user in [users[k] for k in users]:
                if user[2] not in partial:
                    partial[user[2]] = (0,0)
                up,down = partial[user[2]]
                partial[user[2]] = (up + user[0], down + user[1])
            res.append((time, partial))

        return res

    def clear_logs(self, after=0):
        """
        Clear internal logs (logs are never cleared otherwise, taking memory indefinitely).

        :param after: Time after which the cleaning must be done. Positive values are considered absolute timestamps,
            negative and null are how many seconds to keep
            (examples: 0 delete all, -60 keep one minute, 1546300800 keep data from after 2019-01-01 00:00)
        """
        if after <= 0:
            after = time() + after
        while len(self.logs) and self.logs[0][0] < after:
            del(self.logs[0])

    def get_balance(self):
        """
        Get mapping from vpn to user ip.
        Equivalent to:
        `ipset list langate`

        -> Dict[int, Set[ip]]

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

    def set_vpn(self, ip, vpn):
        """
        Move an user to a new vpn.
        Does not modify an entry not already in.
        Equivalent to:
        `ipset list langate` plus
        `ipset add langate <ip>`

        :param ip: ip address of the user.
        :param vpn: Vpn where move the user to.
        """
        entries = self.ipset.list().entries
        if type(vpn) is int:
            vpn = (vpn, (1<<32)-1)
        for entry in entries:
            if entry.elem == ip:
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
    def __init__(self, ip, mark, up=0, down=0, name=None):
        self.ip = ip
        self.mark = mark
        self.up = up
        self.down = down
        self.name = name

    def to_dict(self):
        return {
            "ip": self.ip,
            "mark": self.mark,
            "up": self.up,
            "down": self.down,
            "name": self.name,
        }
