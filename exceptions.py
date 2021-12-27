class ProtocolException(Exception):
    pass

class NetException(Exception):
    pass

class NetInvalidAddress(NetException):
    pass

class NetInvalidParameter(NetException):
    pass

class NetNotFound(NetException):
    pass
