import pytest, unittest, json
from contextlib import contextmanager
from time import sleep
from os import getuid
from random import randint
from pytest import skip
from ipsetnet import IPSetNet
from socket import AF_UNSPEC

@contextmanager
def setup():
    if getuid() != 0:
        skip('need to be root')

    rand = randint(0, 1000)
    name = f'langate-tests-{rand}'
    net = IPSetNet(name, mark_start=1, mark_no=2)
    
    yield net

    net.ipset.destroy(name)


def test_connect_user():
    with setup() as net:
        mac = 'FF:FF:FF:FF:FF:FF'
        net.connect_user(mac, name='foo')
        assert net.ipset.test(net.name, mac, family=AF_UNSPEC, etype='mac')

def test_disconnect_user():
    with setup() as net:
        mac = 'FF:FF:FF:FF:FF:FF'
        net.connect_user(mac, name='foo')
        assert net.ipset.test(net.name, mac, family=AF_UNSPEC, etype='mac')
        net.disconnect_user(mac)
        assert not net.ipset.test(net.name, mac, family=AF_UNSPEC, etype='mac')

def test_user_info():
    with setup() as net:
        mac = 'BE:EF:BE:EF:BE:EF'
        net.connect_user(mac, name='beef')

        mac = 'CA:FE:CA:FE:CA:FE'
        net.connect_user(mac, name='cafe')

        info = net.get_user_info(mac)
        assert info['mac'] == mac.lower()
        assert info['mark'] == 2
        assert info['name'] == 'cafe'

