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

    def create(self, typ, timeout=None, counters=True, skbinfo=True, comment=False, **kwargs):
        args = [self.name, typ]
        if timeout:
            args += ["timeout", timeout]
        if counters:
            args += ["counters"]
        if comment:
            args += ["comment"]
        if skbinfo:
            args += ["skbinfo"]
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

    def add(self, entry):
        pass

    def delete(self, entry):
        pass

    def test(self, entry):
        pass

    def list(self):
        pass

    def save(self):
        pass

    def restore(self):
        pass

    def flush(self):
        pass

    def rename(self, name):
        pass

    def swap(self, other):
        pass

    def version():
        pass

    def real():
        return True
