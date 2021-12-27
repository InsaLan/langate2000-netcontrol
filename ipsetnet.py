#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from time import time
from pyroute2.ipset import IPSet
from exceptions import NetInvalidParameter, NetNotFound
from socket import AF_UNSPEC
import re

from net import Net

class IPSetNet(Net):
    """
    A class made for network access control and bandwidth accounting based on linux ipsets.
    This spawn 2 ipsets for up and down bandwidth accounting.
    Instantiating it require root priviledges.
    For applicable commands, the command they run are indicated. This is indicative only, and
    won't include any optional parameters that are actually set.
    """

    def __init__(self, name='langate', mark_start=0, mark_no=1):
        """
        Create ipsets for access control and bandwidth accounting.
        Equivalent to:
        `ipset create langate hash:mac`

        :param name: name of the ipset. Second one will be <name>-reverse
        :param mark: tuple containing min mark and how many vpns to use
        """
        if name is None:
            raise NetInvalidParameter('name cannot be None') 

        self.ipset = IPSet()
        self.ipset.create(name, stype='hash:mac', family=AF_UNSPEC, skbinfo=True, comment=True)
        self.name = name
        self.mark_start = mark_start
        self.mark_no = mark_no
        self.mark_curr = 0

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
            mark = self.mark_start + self.mark_curr
            self.mark_curr = (self.mark_curr + 1) % self.mark_no

        """
        skbinfo extension of ipsets allows to store
        a mark associated with a mark mask (see ipset(8)).
        We do not use the mask feature so set it to match all mark.
        """
        skbmark = (mark, 0xffffffff)
        
        self.ipset.add(self.name, mac, etype='mac', skbmark=skbmark, comment=name, timeout=timeout)

    def disconnect_user(self, mac):
        """
        Remove an entry from the ipsets.
        Equivalent to:
        `ipset del langate <entry mac>`

        :param mac: mac of the user.
        """
        self.ipset.delete(self.name, mac, etype='mac')

    def get_user_info(self, mac):
        """
        Get users information from his mac address.
        Equivalent to:
        `sudo ipset list langate`
        plus some processing

        :param mac: mac address of the user.
        :return: xxx 
        """
        entries = self.ipset.list(name=self.name)[0].get_attr('IPSET_ATTR_ADT').get_attrs('IPSET_ATTR_DATA')
       
        # iterate over the set entries for specified mac
        for item in entries:
            item_mac = item.get_attr('IPSET_ATTR_ETHER')

            if mac.lower() == item_mac.lower():
                item_mark = item.get_attr('IPSET_ATTR_SKBMARK')[0] # only retrieve the mark, disregard mask, see comment in connect_user
                item_name = item.get_attr('IPSET_ATTR_COMMENT')

                return {
                        'mac': item_mac,
                        'mark': item_mark,
                        'name': item_name
                }

        raise NetNotFound(f'mac {item_mac} not found in set')


    def clear(self):
        """
        Remove all entry from the set.
        Equivalent to:
        `ipset flush langate`
        """
        self.ipset.flush(self.name)

    def get_all_connected(self):
        """
        Get all entries from the set.
        Equivalent to:
        `ipset list langate`

        :return: Dictionary mapping mac to a User class
        """
        pass

    def delete(self):
        """
        Delete the set. After calling this function, the sets can't be used anymore as it no longer exist.
        Equivalent to:
        `sudo ipset destroy langate`
        """
        self.ipset.destroy(self.name)

    def get_balance(self):
        """
        Get mapping from vpn to user mac.
        Equivalent to:
        `ipset list langate`

        -> Dict[int, Set[mac]]

        :return: Dictionary composed of vpn and set of mac addresses
        """
        pass

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
        pass 
