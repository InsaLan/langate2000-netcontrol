#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from subprocess import run, PIPE, TimeoutExpired
from xmltodict import parse as parsexml

# timeout
# errorcode

class IpsetError(RuntimeError):
    """ipset returned an error"""

def _run_cmd(command, args=[], stdin=None):
    result = run(["ipset", command, "-output", "xml"] + args, stdout=PIPE, stderr=PIPE, timeout=2)
    success = result.returncode == 0
    out = result.stdout.decode("UTF-8")
    err = result.stderr.decode("UTF-8")
    if out:
        return (success, parsexml(out), err or None)
    else:
        return (success, None, err or None)

class Ipset:
    def __init__(self, name):
        self.name = name

    def create(self, typ, timeout=None, counters=True, skbinfo=True, comment=False, exist=True, **kwargs):
        args = [self.name, typ]
        if timeout:
            args += ["timeout", timeout]
        if counters:
            args += ["counters"]
        if comment:
            args += ["comment"]
        if skbinfo:
            args += ["skbinfo"]
        if exist:
            args += ["-exist"]
        for k,v in [(k, kwargs[k]) for k in kwargs]:
            if type(v)==bool or v==None:
                if v:
                    args += [k]
            else:
                args += [k, v]

        success, _, err = _run_cmd("create", args)

        if not success:
            raise IpsetError(err)

    def destroy(self):
        success, _, err = _run_cmd("destroy", [self.name])

        if not success:
            raise IpsetError(err)

    def add(self, entry, nomatch=False, exist=True):
        if type(entry) is Entry:
            args = [self.name] + entry.to_cmd()
        else:
            args = [self.name, entry]
        if nomatch:
            args += ["nomatch"]
        if exist:
            args += ["-exist"]

        success, _, err = _run_cmd("add", args)

        if not success:
            raise IpsetError(err)

    def delete(self, entry, exist=True):
        if type(entry) is Entry:
            args = [self.name, entry.elem]
        else:
            args = [self.name, entry]
        if exist:
            args += ["-exist"]

        success, _, err = _run_cmd("del", args)

        if not success:
            raise IpsetError(err)

    def test(self, entry):
        if type(entry) is Entry:
            args = [entry.elem]
        else:
            args = [entry]

        success, _, err = _run_cmd("del", args)

        if success:
            return True
        if "is NOT in set" in err:
            return False
        raise IpsetError(err)

    def list(self):
        success, res, err = _run_cmd("list", [self.name])
        if not success:
            raise IpsetError(err)
        return Set.from_dict(res["ipsets"]["ipset"])

    def flush(self):
        success, _, err = _run_cmd("flush", [self.name])

        if not success:
            raise IpsetError(err)

    def rename(self, name):
        success, _, err = _run_cmd("flush", [self.name, name])

        if not success:
            raise IpsetError(err)
        self.name = name

    def swap(self, other):
        success, _, err = _run_cmd("swap", [self.name, other.name])

        if not success:
            raise IpsetError(err)
        self.name,other.name = other.name,self.name

    def real():
        return True


class Set:
    def __init__(self, name, typ, header, entries):
        self.name = name #string
        self.type = typ #string
        self.header = header #dict
        self.entries = entries #list of entries

    def from_dict(data):
        if data["members"] is None:
            entries = []
        elif type(data["members"]["member"]) is list:
            entries = [Entry(**e) for e in data["members"]["member"]]
        else:
            entries = [Entry(**data["members"]["member"])]
        return Set(data["@name"], data["type"], dict(data["header"]), entries)

class Entry:
    def __init__(self, elem, timeout=None, packets=None, bytes=None, comment=None, skbmark=None, skbprio=None, skbqueue=None):
        self.elem = elem
        self.comment = comment
        self.timeout = int(timeout) if timeout is not None else None
        self.packets = int(packets) if packets is not None else None
        self.bytes = int(bytes) if bytes is not None else None
        self.skbqueue = int(skbqueue) if skbqueue is not None else None
        if skbmark is None:
            self.skbmark = None
        elif type(skbmark) is int:
            self.skbmark = (skbmark, 2**32-1)
        elif type(skbmark) is tuple:
            self.skbmark = skbmark
        else:
            if "/" in skbmark:
                mark,mask = skbmark.split("/")
                self.skbmark = (int(mark, 16), int(mask,16))
            else:
                self.skbmark = (int(skbmark, 16), 2**32-1)

        if skbprio is None:
            self.skbprio = None
        elif type(skbprio) is tuple:
            self.skbprio = skbprio
        else:
            maj,min = skbprio.split(":")
            self.skbprio = (int(maj), int(min))

    def to_cmd(self):
        res = [self.elem]
        if self.comment is not None:
            res += ["comment", self.comment]
        if self.timeout is not None:
            res += ["timeout", str(self.timeout)]
        if self.packets is not None:
            res += ["packets", str(self.packets)]
        if self.bytes is not None:
            res += ["bytes", str(self.bytes)]
        if self.skbqueue is not None:
            res += ["skbqueue", str(self.skbqueue)]
        if self.skbmark is not None:
            res += ["skbmark", '0x{:x}/0x{:x}'.format(*self.skbmark)]
        if self.skbprio is not None:
            res += ["skbprio", '{}:{}'.format(*self.skbprio)]
        return res
