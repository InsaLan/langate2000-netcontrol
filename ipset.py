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

    def add(self, entry, timeout=None, packets=None, bytes=None, comment=None,
            skbmark=None, skbprio=None, skbqueue=None, nomatch=False, exist=True):
        args = [self.name, entry]
        if timeout:
            args += ["timeout", timeout]
        if packets:
            args += ["packets", packets]
        if bytes:
            args += ["bytes", bytes]
        if comment:
            args += ["comment", comment]
        if skbmark:
            args += ["skbmark", skbmark]
        if skbprio:
            args += ["skbprio", skbprio]
        if skbqueue:
            args += ["skbqueue", skbqueue]
        if nomatch:
            args += ["namatch"]
        if exist:
            args += ["-exist"]

        success, _, err = _run_cmd("add", args)

        if not success:
            raise IpsetError(err)

    def delete(self, entry, exist=True):
        args = [self.name, entry]
        if exist:
            args += ["-exist"]

        success, _, err = _run_cmd("del", args)

        if not success:
            raise IpsetError(err)

    def test(self, entry):
        success, _, err = _run_cmd("del", [entry])
        if success:
            return True
        if "is NOT in set" in err:
            return False
        raise IpsetError(err)

    def list(self):
        pass

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
