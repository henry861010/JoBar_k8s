# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class sale_order(models.Model):

	_inherit = 'sale.order'
    
    
	cancel_reason = fields.Char(string="取消的原因")
	cancel_remark = fields.Char(string="備註",required=False)
	state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),('req_to_cancel','Request to Cancel')
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')
	
class CancelSaleOrder(models.Model):

	_name = "sale.order.cancel"
	_description = "Object to get the request to the order"

	name = fields.Char(string='名稱')
	quote_date = fields.Date(string='訂購時間')
	current_date = fields.Date(string='現在時間')
	cancel_reason = fields.Char(string="=原因")
	cancel_remarks = fields.Char(string="備註",required=False)
	state = fields.Selection([('request_to_cancel','確定'),('cancel','取消')], string='State', default="request_to_cancel")
     
	def cancel(self):
		sale_order = self.env['sale.order'].search([('name','=',self.name)])
		journal = self.env['account.journal'].search([('type','=','sale')])
		sale_order.sudo().action_cancel()
		if sale_order.state == 'cancel':
			if sale_order.invoice_ids:
				sale_order.invoice_ids.button_cancel()
		for res in self:
			res.write({'state':'cancel'})

		sale_order.update({'cancel_reason':self.cancel_reason,
						   'cancel_remark':self.cancel_remarks})
