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

    def __init__(self, name: str, start_mark=0, mark_no=1):
        pass

    def connect_device(self, mac: str, name=None, timeout=None, mark=None):
        pass

    def disconnect_device(self, mac: str):
        pass

    def get_device_info(self, mac: str):
        pass

    def set_mark(self, mac: str, mark: int):
        pass 

    def clear(self):
        pass

    def get_ip(self, mac: str) -> str:
        return ''

    def get_mac(self, ip: str) -> str:
        return ''

