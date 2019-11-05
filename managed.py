#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ipset import Ipset,Entry
from time import time
import re

class Net:
    #logs: List[Tuple[time, Dict[ip, (up, down, mark)]]]

    def __init__(self, name="langate", mark=(0, 1)):
        self.ipset = Ipset(name)
        self.reverse = Ipset(name + "-reverse")
        self.ipset.create("hash:ip")
        self.reverse.create("hash:ip", skbinfo=False)
        self.mark_start, self.mark_mod = mark
        self.mark_current = 0
        self.logs = list()

    def generate_iptables(self, match_internal = "-s 172.16.0.0/255.252.0.0", stop = False):
        pass

    def connect_user(self, ip, timeout=None, mark=None, up=None, down=None):
        if mark is None:
            mark = self.mark_current + self.mark_start
            self.mark_current = (self.mark_current+1) % self.mark_mod
        self.ipset.add(Entry(ip, skbmark=mark, bytes=up))
        self.reverse.add(Entry(ip, bytes=down))

    def disconnect_user(self, ip):
        self.ipset.delete(ip)
        self.reverse.delete(ip)
        pass

    def get_user_info(self, ip):
        """
        Get users information from his mac address.
        Obtained by the commands :
        'sudo ipset list langate | grep 1.1.1.1'

        :param ip: Mac address of the user.
        :return: User class containing their bandwidth usage and mark
        """
        entries = self.ipset.list().entries
        for entry in entries:
            if entry.elem == ip:
                mark = entry.skbmark[0] if entry.skbmark else None
                up = entry.bytes or 0
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

        return User(ip, mark, up=up, down=down)

    def clear(self):
        """
        Clear the set, by removing all entry from it. Equivalent to the command :
        'sudo ipset flush langate'
        """
        self.ipset.flush()
        self.reverse.flush()


    def get_all_connected(self):
        """
        Get all entries from the set, with how much bytes they transferred and what is their mark.
        Equivalent to the command : 'sudo ipset list langate"
        :return: Dictionary mapping device ip to a User class containing their bandwidth usage (down and up) and mark
        """
        entries = self.ipset.list().entries
        users = dict()
        for entry in entries:
            ip = entry.elem
            mark = entry.skbmark[0] if entry.skbmark else None
            up = entry.bytes or 0
            users[ip] = User(ip, mark, up=up)

        rev_entries = self.reverse.list().entries
        for entry in rev_entries:
            if entry.elem in users:
                users[entry.elem].down = entry.bytes or 0

        return users

    def delete(self):
        """
        Delete the set. Equivalent to the command :
        'sudo ipset destroy langate"
        """
        self.ipset.destroy()
        self.reverse.destroy()

    def log_statistics(self):
        """
        Add an entry to internal log. Equivalent to the command :
        'sudo ipset list langate'
        """
        self.logs.append((time(),self.get_all_connected()))

    def get_users_logs(self):
        """
        Get logs by users, sorted by date.
         -> List[Tuple[time, Dict[str, Tuple[up, down, mark]]]]

        :return: List sorted by date of tuple of date and dictionary, itself mapping device's
        ip to it's bandwith usage since last entry
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

        :return: List sorted by date of tuple of date and dictionary, itself mapping vpn mark
        to it's bandwith usage since last entry
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

    def clear_logs(self, after=None):
        """
        Clear internal logs (logs are never cleared otherwise, taking memory indefinitely).

        :param after: Time after which the cleaning must be done, now if not set.
        """
        after = after or time()
        while len(self.logs) and self.logs[0][0] < after:
            del(self.logs[0])

    def get_balance(self):
        """
        Get current mapping of vpn and mac (each entry contain the vpn number, with who is connected to it)

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
    def __init__(self, ip, mark, up=0, down=0):
        self.ip = ip
        self.mark = mark
        self.up = up
        self.down = down

    def to_dict(self):
        return {
            "ip": self.ip,
            "mark": self.mark,
            "up": self.up,
            "down": self.down
        }
