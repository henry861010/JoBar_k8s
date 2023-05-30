# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class Contacts(models.Model):
    _inherit = "res.partner"

    birthdays = fields.Date(string='生日', readonly=False, index=True, default=lambda self: fields.datetime.today())
    note = fields.Text(string='描述備註')
    pickup_area = fields.Many2one('res.pickup_area', string='取貨區域',ondelete='set null')
    fb_app_id = fields.Char(string='FB應用程式編號', default=None)
    user_discount = fields.Integer(string='購物金', default=50, readonly=False, index=True,)
    
    _sql_constraints = [
        ('name_uniq', 'unique (fb_app_id)', '請填寫自己的FB應用程式編號!'),
    ]
    
class PickupArea(models.Model):
    _name = 'res.pickup_area'
    _description = "Pickup Order Area"
    _order = 'id'

    name = fields.Char(string='區域與時間', required=True)
    code = fields.Text(string="區域代號")
    area_name = fields.Char(string='區域名稱')
    pickup_time = fields.Char(string='取貨時段')
    address = fields.Char(string='取貨地址')
    
    