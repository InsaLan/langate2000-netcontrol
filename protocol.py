import re
from marshmallow import fields, validate, Schema, post_load
from marshmallow_oneofschema import OneOfSchema

MacAddressField = fields.Str(validate=validate.Regexp(r'^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$'))

class ConnectUserMsg(Schema):
    name = fields.Str()
    mac = MacAddressField

    @post_load
    def process(self, data, **kwargs):
        net = self.context['net']
        net.connect_user(data['mac'], name=data['name'])

class DisconnectUserMsg(Schema):
    mac = MacAddressField

    @post_load
    def process(self, data, **kwargs):
        net = self.context['net']
        net.disconnect_user(data['mac'])

class GetUserInfoMsg(Schema):
    mac = MacAddressField

    @post_load
    def process(self, data, **kwargs):
        net = self.context['net']
        return net.get_user_info(data['mac'])

class SetMarkMsg(Schema):
    mac = MacAddressField
    mark = fields.Int()

    @post_load
    def process(self, data, **kwargs):
        net = self.context['net']
        net.set_mark(data['mac'], data['mark'])


class QueryMsg(OneOfSchema):
    type_field = "query"
    type_schemas = {
        "connect_user": ConnectUserMsg, 
        "disconnect_user": DisconnectUserMsg,
        "get_user_info": GetUserInfoMsg,
        "set_mark": SetMarkMsg,
        #"clear": _NoParamsMsg,
        #"destroy": _NoParamsMsg,
        #"get_ip": _MacMsg,
        #"get_mac": _IpMsg 
    }
