# langate2000-netcontrol

## Summary

This deamon provides a high level interface to handle device access on the LAN-party network to the internet. This component, which runs with `NET_ADMIN` capability on the gateway, is queried via a UNIX socket by the [https://github.com/InsaLan/langate2000](langate2000) captive portal to connect or disconnect users devices once they are authenticated. It also provides a way, for the captive portal needs to resolve the MAC address of a given IP address and the reverse.

## Implementation

Currently the backend used to control device access relies on an *ipset* that contains all devices authorized to access internet and an iptable rule that allows only packets from devices in the *ipset* to reach the internet. Thus, the currently used `IPSetNet` backend uses [https://pyroute2.org](pyroute2) to add and remove devices to an *ipset* storing `hash:mac` couples. The necessary iptable rule that filters out unauthorized packets is not (yet) added by this daemon.

The IP to MAC and MAC to IP lookup is currently done by reading the ARP tables of the gateway.

## How to run

Ensure you have all the packages in `requirements.txt` installed.

`PYTHONPATH=$(pwd):$PYTHONPATH python3 netcontrol.py`

## How to run tests

`PYTHONPATH=$(pwd):$PYTHONPATH pytest ./tests/.`

Some tests of the network backends require the `NET_ADMIN` capability or root privileges. They will instanciate *ipsets* and talk using netlink to the kernel.
