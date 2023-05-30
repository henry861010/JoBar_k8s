# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class SaleOrder(models.Model):
    _inherit = "sale.order"
    pickup_date = fields.Date(string='取貨日期', required=True, readonly=False, index=True
                                , default=lambda self: fields.datetime.today())
    pickup_area = fields.Many2one('res.pickup_area', string='取貨區域',ondelete='set null')
    sale_description = fields.Char(string='銷售說明備註')
    mail_check = fields.Boolean(string='寄出形式發票',default='False')
    
    @api.onchange('partner_id')
    def onchange_partner_id_pickuparea(self):     
        if self.partner_id:
            #query = "select pickup_area from res_partner where id = " + str(self.partner_id.id)
            self.update({'pickup_area': self.partner_id.pickup_area})
            

           
