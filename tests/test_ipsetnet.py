import pytest, json
from contextlib import contextmanager
from time import sleep
from os import getuid
from random import randint
from ipsetnet import IPSetNet
from socket import AF_UNSPEC
from unittest import TestCase
from exceptions import NetException

@contextmanager
def setup():
    if getuid() != 0:
        pytest.skip('need to be root')

    rand = randint(0, 1000)
    name = f'langate-tests-{rand}'
    net = IPSetNet(name, mark_start=1, mark_no=2)
    
    yield net

    net.ipset.destroy(name)

class IPSetNetTests(TestCase):

    def test_connect_device(self):
        with setup() as net:
            mac = 'FF:FF:FF:FF:FF:FF'
            net.connect_device(mac, name='foo')
            self.assertTrue(net.ipset.test(net.name, mac, family=AF_UNSPEC, etype='mac'))
    
    def test_disconnect_device(self):
        with setup() as net:
            mac = 'FF:FF:FF:FF:FF:FF'
            net.connect_device(mac, name='foo')
            self.assertTrue(net.ipset.test(net.name, mac, family=AF_UNSPEC, etype='mac'))
            
            net.disconnect_device(mac)
            self.assertFalse(net.ipset.test(net.name, mac, family=AF_UNSPEC, etype='mac'))
    
    def test_device_info(self):
        with setup() as net:
            mac = 'BE:EF:BE:EF:BE:EF'
            net.connect_device(mac, name='beef')
    
            mac = 'CA:FE:CA:FE:CA:FE'
            net.connect_device(mac, name='cafe')
    
            info = net.get_device_info(mac)
            self.assertEqual(info['mac'], mac.lower())
            self.assertEqual(info['mark'], 2)
            self.assertEqual(info['name'], 'cafe')
    
    def test_device_info_nonexistent(self):
        with setup() as net:
            mac = 'FF:FF:FF:FF:FF:FF'

            with self.assertRaises(NetException):
                net.get_device_info(mac)
