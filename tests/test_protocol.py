import pytest, json
from contextlib import contextmanager
from socket import socket, AF_UNIX, SOCK_STREAM
from os import unlink
from sys import exc_info
from time import sleep
from threading import Thread
from random import randint
from socketserver import UnixStreamServer
from unittest import TestCase

from netcontrol import NetcontrolProtocolHandler, send_msg, recv_msg
from exceptions import NetNotFound
from protocol import QueryMsg
from net import Net
from . import WrappedThread

DUMMY_IP = '172.16.1.1'
DUMMY_MAC = 'ff:ff:ff:ff:ff:ff'

class DummyNet(Net):
    def __init__(self, name='langate-tests', start_mark=0, mark_no=1):
        super().__init__(name, start_mark, mark_no)
    
    def get_device_info(self, mac: str):
        if mac == DUMMY_MAC:
            return {
                'mac': DUMMY_MAC,
                'mark': 1,
                'name': 'foo'
            }
        
        raise NetNotFound(f'mac {mac} not found in set')

    def get_ip(self, mac: str) -> str:
        return DUMMY_IP

    def get_mac(self, ip: str) -> str:
        return DUMMY_MAC 

@contextmanager
def setup_server():
    
    rand = randint(0, 1000)
    sock_name = f'/tmp/netcontrol-test-{rand}'
    proto_handler = NetcontrolProtocolHandler
    proto_handler.net_cls = DummyNet

    server = UnixStreamServer(sock_name, proto_handler)
    
    # def handle_error(x,y):
    #     # HACK to reraise any exception that occured during
    #     # stream handling, because by default exceptions are
    #     # silently dismissed (to prevent the server from crashing).
    #     raise exc_info()[1]

    # server.handle_error = handle_error
    thread = WrappedThread(target=server.serve_forever)
    thread.start()
    
    yield sock_name

    server.shutdown()
    thread.join()
    unlink(sock_name)

class ProtocolTests(TestCase):

    def test_garbage(self):
        with setup_server() as unix_fname:
            with socket(AF_UNIX, SOCK_STREAM) as sock:
                sock.connect(unix_fname)
                send_msg(sock, '\xff\xff\xff\xff')
                raw_msg = json.loads(recv_msg(sock))
                self.assertFalse(raw_msg['success'])
                self.assertEqual('wrong message format', raw_msg['message'])

    def test_undefined_query_message(self):
        with setup_server() as unix_fname:
            with socket(AF_UNIX, SOCK_STREAM) as sock:
                sock.connect(unix_fname)
                msg = json.dumps({'query': 'undefined'})
                send_msg(sock, msg)
                raw_msg = json.loads(recv_msg(sock))
                self.assertFalse(raw_msg['success'])
                self.assertEqual({'query': ['Unsupported value: undefined']}, raw_msg['message'])

    def test_message_too_big(self):
        with setup_server() as unix_fname:
            with socket(AF_UNIX, SOCK_STREAM) as sock:
                sock.connect(unix_fname)
                msg = json.dumps({'query': 'connect_device', 'mac': 'ff:'*0x1ff, 'name': 'kkkk'})
                send_msg(sock, msg)
                raw_msg = json.loads(recv_msg(sock))
                self.assertFalse(raw_msg['success'])
                self.assertTrue(raw_msg['message'].startswith('message size exceeds the maximum allowed'))

    def test_connect_device(self):
        with setup_server() as unix_fname:
            with socket(AF_UNIX, SOCK_STREAM) as sock:
                sock.connect(unix_fname)
                msg = json.dumps({'query': 'connect_device', 'mac': 'ff:ff:ff:ff:ff:ff', 'name': 'kkkk'})
                send_msg(sock, msg)
                raw_msg = json.loads(recv_msg(sock))
                self.assertTrue(raw_msg['success'])

    def test_connect_device_missing_mac(self):
        with setup_server() as unix_fname:
            with socket(AF_UNIX, SOCK_STREAM) as sock:
                sock.connect(unix_fname)
                msg = json.dumps({'query': 'connect_device', 'name': 'ii'})
                send_msg(sock, msg)
                raw_msg = json.loads(recv_msg(sock))
                self.assertFalse(raw_msg['success'])
                self.assertEqual({'mac': ['Missing data for required field.']}, raw_msg['message'])

    def test_connect_device_bad_mac_format(self):
        with setup_server() as unix_fname:
            with socket(AF_UNIX, SOCK_STREAM) as sock:
                sock.connect(unix_fname)
                msg = json.dumps({'query': 'connect_device', 'mac': 'bad', 'name': 'kkkk'})
                send_msg(sock, msg)
                raw_msg = json.loads(recv_msg(sock))
                self.assertFalse(raw_msg['success'])

    def test_disconnect_device_missing_mac(self):
        with setup_server() as unix_fname:
            with socket(AF_UNIX, SOCK_STREAM) as sock:
                sock.connect(unix_fname)
                msg = json.dumps({'query': 'disconnect_device'})
                send_msg(sock, msg)
                raw_msg = json.loads(recv_msg(sock))
                self.assertFalse(raw_msg['success'])
                self.assertEqual({'mac': ['Missing data for required field.']}, raw_msg['message'])

    def test_get_device_info(self):
        with setup_server() as unix_fname:
            with socket(AF_UNIX, SOCK_STREAM) as sock:
                sock.connect(unix_fname)
                msg = json.dumps({'query': 'get_device_info', 'mac': 'ff:ff:ff:ff:ff:ff'})
                send_msg(sock, msg)
                raw_msg = json.loads(recv_msg(sock))
                self.assertTrue(raw_msg['success'])
                self.assertEqual(raw_msg['info']['mark'], 1)
                self.assertEqual(raw_msg['info']['name'], 'foo')

    def test_get_device_info_missing_device(self):
        with setup_server() as unix_fname:
            with socket(AF_UNIX, SOCK_STREAM) as sock:
                sock.connect(unix_fname)
                msg = json.dumps({'query': 'get_device_info', 'mac': 'ff:ff:ff:ff:ff:fe'})
                send_msg(sock, msg)
                raw_msg = json.loads(recv_msg(sock))
                self.assertFalse(raw_msg['success'])

    def test_get_mac(self):
        with setup_server() as unix_fname:
            with socket(AF_UNIX, SOCK_STREAM) as sock:
                sock.connect(unix_fname)
                msg = json.dumps({'query': 'get_mac', 'ip': DUMMY_IP})
                send_msg(sock, msg)
                raw_msg = json.loads(recv_msg(sock))
                self.assertTrue(raw_msg['success'])
                self.assertEqual(raw_msg['mac'], DUMMY_MAC)

    def test_get_ip(self):
        with setup_server() as unix_fname:
            with socket(AF_UNIX, SOCK_STREAM) as sock:
                sock.connect(unix_fname)
                msg = json.dumps({'query': 'get_ip', 'mac': DUMMY_MAC})
                send_msg(sock, msg)
                raw_msg = json.loads(recv_msg(sock))
                self.assertTrue(raw_msg['success'])
                self.assertEqual(raw_msg['ip'], DUMMY_IP)
