import pytest, unittest, json
from contextlib import contextmanager
from socket import socket, AF_UNIX, SOCK_STREAM
from os import unlink
from sys import exc_info
from time import sleep
from threading import Thread
from random import randint
from socketserver import UnixStreamServer
from netcontrol import NetcontrolProtocolHandler, send_msg, recv_msg
from protocol import QueryMsg
from net import Net
from . import WrappedThread

class DummyNet(Net):
    pass

@contextmanager
def setup_server():
    
    rand = randint(0, 1000)
    sock_name = f'/tmp/netcontrol-test-{rand}'
    proto_handler = NetcontrolProtocolHandler
    proto_handler.net_cls = DummyNet

    server = UnixStreamServer(sock_name, proto_handler)
    
    def handle_error(x,y):
        # HACK to reraise any exception that occured during
        # stream handling, because by default exceptions are
        # silently dismissed (to prevent the server from crashing).
        raise exc_info()[1]

    server.handle_error = handle_error
    thread = WrappedThread(target=server.serve_forever)
    thread.start()
    
    yield sock_name

    server.shutdown()
    thread.join()
    unlink(sock_name)


def test_connect_user():
    with setup_server() as unix_fname:
        with socket(AF_UNIX, SOCK_STREAM) as sock:
            sock.connect(unix_fname)
            msg = json.dumps({'query': 'connect_user', 'mac': 'ff:ff:ff:ff:ff:ff', 'name': 'kkkk'})
            send_msg(sock, msg)
            raw_msg = json.loads(recv_msg(sock))
            assert raw_msg['success']


def test_connect_user_bad_mac_format():
    with setup_server() as unix_fname:
        with socket(AF_UNIX, SOCK_STREAM) as sock:
            sock.connect(unix_fname)
            msg = json.dumps({'query': 'connect_user', 'mac': 'bad', 'name': 'kkkk'})
            send_msg(sock, msg)
            raw_msg = json.loads(recv_msg(sock))
            assert not raw_msg['success']
