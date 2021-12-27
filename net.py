#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from time import time
import re

class Net:
    """
    This is the abstract class representing the Network abstraction for netcontrol
    It provides the high level methods (connect, disconnect device...) and should
    provide an implementation for it.
    """

    def __init__(self, start_mark=0, mark_no=1):
        pass

    def connect_user(self, mac, name=None, timeout=None, mark=None):
        pass

    def disconnect_user(self, mac):
        pass

    def get_user_info(self, mac):
        pass

    def clear(self):
        pass

    def get_all_connected(self):
        pass

    def delete(self):
        pass

    def get_balance(self):
        pass

    def set_vpn(self, mac, vpn):
        pass 

    @staticmethod
    def get_ip(mac: str) -> str:
        """
        Get the ip address associated with a given mac address.
    
        :param mac: Mac address of the user.
        :return: Ip address of the user.
        """
        if not verify_mac(mac):
            raise NetInvalidAddress(f'{mac} is not a valid mac address')
        
        f = open('/proc/net/arp', 'r')
        lines = f.readlines()[1:]
        for line in lines:
            if line.startswith(mac, 41):  # 41=offset of mac in line
                return line.split(' ')[0]
        
        raise NetException(f'{mac} does not have a known ip')
    
    @staticmethod
    def get_mac(ip: str) -> str:
        """
        Get the mac address associated with a given ip address.
    
        :param ip: Ip address of the user.
        :return: Mac address of the user.
        """
        if not verify_ip(ip):
            raise NetInvalidAddress('{ip} is not a valid ip address')

        f = open('/proc/net/arp', 'r')
        lines = f.readlines()[1:]
        for line in lines:
            if line.startswith(ip + " "):
                return line[41:].split(' ')[0] # 41=offset of mac in line
        
        raise NetException(f'{ip} does not have a known mac')
    
    
