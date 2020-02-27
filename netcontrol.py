import config
import os, struct, traceback
import socket, pickle
import traceback
from ipset import IpsetError
from managed import Net, User, get_ip, get_mac

"""
This is the main script for langate2000-netcontrol.
This component is an interface between the langate2000 web pages and
the kernel network components of the gateway used during the events.

Having this component in between is important because we don't want the web server
to have privileged access to kernel components as it is needed for this script.

Both the langate2000 django server and this components communicate using UNIX sockets.
The messages exchanged begin with the size of the payload (as a 4 bytes int) followed by
the payload itself. The payload is always a pickle-encoded python dict.

Example format of a *query* payload, sent by langate2000 webserver :

    {
        "query": "get_mac",
        "ip": "172.16.1.20"
    }

The query parameter is mandatory and reflect the name of the function you want to call in the
ipset class.

Example format of a *response* payload, sent back by this daemon :

    {
        "success": True,
        "mac": "ff:ff:ff:ff:ff"
    }

The success parameter is mandatory and is a boolean value.
If False, the only other value in the dict is the corresponding error message raised 
by the ipset class.

Note that this daemon needs to be executed on the same machine as the one that serves the pages because it needs to access the ARP tables to find the mac adresses of the hosts that are using the web server.

"""

net = Net(mark=config.mark)

# the 3 following helper functions were taken from https://stackoverflow.com/questions/17667903/python-socket-receive-large-amount-of-data

def _send(sock, data):
    pack = struct.pack('>I', len(data)) + data
    sock.sendall(pack)

def _recv_bytes(sock, size):
    data = b''
    while len(data) < size:
        r = sock.recv(size - len(data))
        if not r:
            return None
        data += r
    return data

def _recv(sock):
    data_length_r = _recv_bytes(sock, 4)

    if not data_length_r:
        return None

    data_length = struct.unpack('>I', data_length_r)[0]
    return _recv_bytes(sock, data_length)
    

def parse_query(p):
    response = {
        "success": True
    }

    try:

        if p["query"] == "connect_user":
            net.connect_user(p["mac"], p["name"].replace('"',''))
        elif p["query"] == "disconnect_user":
            net.disconnect_user(p["mac"])
        elif p["query"] == "get_user_info":
            response["info"] = net.get_user_info(p["mac"]).to_dict()
        elif p["query"] == "set_mark":
            net.set_vpn(p["mac"], p["mark"])
        elif p["query"] == "clear":
            net.clear()
        elif p["query"] == "destroy":
            net.delete()
        elif p["query"] == "get_ip":
            response["ip"] = get_ip(p["mac"])
        elif p["query"] == "get_mac":
            response["mac"] = get_mac(p["ip"])
        else:
            raise NotImplementedError

    except IpsetError as e:
        return {
            "success": False,
            "message": str(e)
        }

    else:
        return response

if os.path.exists(config.netcontrol_socket_file):
    os.remove(config.netcontrol_socket_file)

with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
    server.bind(config.netcontrol_socket_file)

    print("Listening on {}.".format(config.netcontrol_socket_file))

    while True:
        try:
            server.listen(1)
            client, address = server.accept()

            # TODO: authenticate packet
            q = pickle.loads(_recv(client))

            r = parse_query(q)

            _send(client, pickle.dumps(r))
            client.close()
        except Exception:
            traceback.print_exc()
