import config, json
from struct import unpack, pack
from socketserver import StreamRequestHandler, UnixStreamServer
from marshmallow import ValidationError

from protocol import QueryMsg
from ipsetnet import IPSetNet
from exceptions import ProtocolException

def send_msg(sock, data):
    message_size = len(data)
    raw_message = pack(f'>I{message_size}s', message_size, data.encode('utf-8'))
    sock.sendall(raw_message)

def recv_msg(sock):
    def _recv_bytes(size):
        data = b''
        while len(data) < size:
            received_bytes = sock.recv(size - len(data))
            if not received_bytes:
                raise ProtocolException(f'expected to receive {size} bytes but received only {len(data)}')

            data += received_bytes
        return data

    message_size_raw = _recv_bytes(4)
    message_size = unpack('>I', message_size_raw)[0]

    data = _recv_bytes(message_size)
    return data.decode()

class NetcontrolProtocolHandler(StreamRequestHandler):
    net_cls = IPSetNet

    def __init__(self, *args, **kwargs):
        self.net = NetcontrolProtocolHandler.net_cls()
        super().__init__(*args, **kwargs)

    def handle(self):
        response = {
                'success': True
        }

        try:
            json_payload = recv_msg(self.request)
            message = QueryMsg()
            message.context['net'] = self.net
            message.loads(json_payload)
            send_msg(self.request, json.dumps(response))
            
        except ValidationError as e:
            raw = json.dumps({'success': False, 'message': e.normalized_messages()})
            send_msg(self.request, raw)

        except Exception as e:
            raw = json.dumps({'success': False, 'message': str(e)})
            send_msg(self.request, raw)


if __name__ == "__main__":
    with UnixStreamServer(config.netcontrol_socket_file, NetcontrolProtocolHandler) as server:
        print(f"Listening on {config.netcontrol_socket_file}")
        server.serve_forever()
