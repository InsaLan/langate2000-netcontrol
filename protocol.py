import re
from marshmallow import fields, validate, Schema, post_load
from marshmallow_oneofschema import OneOfSchema

MacAddressField = fields.Str(required=True, validate=validate.Regexp(r'^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$'))

class ConnectUserMsg(Schema):
    name = fields.Str(required=True)
    mac = MacAddressField

    @post_load
    def process(self, data, **kwargs):
        net = self.context['net']
        net.connect_device(data['mac'], name=data['name'])

class DisconnectUserMsg(Schema):
    mac = MacAddressField

    @post_load
    def process(self, data, **kwargs):
        net = self.context['net']
        net.disconnect_device(data['mac'])

class GetUserInfoMsg(Schema):
    mac = MacAddressField

    @post_load
    def process(self, data, **kwargs):
        net = self.context['net']
        return { 'info': net.get_device_info(data['mac']) }

class SetMarkMsg(Schema):
    mac = MacAddressField
    mark = fields.Int(required=True)

    @post_load
    def process(self, data, **kwargs):
        net = self.context['net']
        net.set_mark(data['mac'], data['mark'])

#class ClearMsg(Schema):
#
#    @post_load
#    def process(self, data, **kwargs):
#        net = self.context['net']
#        net.clear()

class GetIpMsg(Schema):
    mac = MacAddressField
 
    @post_load
    def process(self, data, **kwargs):
        net = self.context['net']
        return { 'ip': net.get_ip(data['mac']) }

class GetMacMsg(Schema):
    ip = fields.IPv4(required=True)

    @post_load
    def process(self, data, **kwargs):
        net = self.context['net']
        return { 'mac': net.get_mac(str(data['ip'])) }


class QueryMsg(OneOfSchema):
    type_field = "query"
    type_schemas = {
        "connect_device": ConnectUserMsg, 
        "disconnect_device": DisconnectUserMsg,
        "get_device_info": GetUserInfoMsg,
        "set_mark": SetMarkMsg,
        #"clear": ClearMsg,
        "get_ip": GetIpMsg,
        "get_mac": GetMacMsg 
    }
