# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_round
from datetime import timedelta, time


class Product(models.Model):
    _inherit = "product.template"

    product_keywords = fields.Char(string='商品關鍵字', required=True)

    _sql_constraints = [
        ('name_uniq', 'CHECK (sale_ok = False AND product_keywords IS UNIQUE)', '商品關鍵字請勿重複!'),
    ]

    pickup_date = fields.Date(string='取貨日期', required=True, readonly=False, index=True
                              , default=lambda self: fields.datetime.today())
    sale_start_date = fields.Datetime(string='銷售開始日', required=True, readonly=False, index=True
                                      , default=lambda self: fields.datetime.today())
    sale_end_date = fields.Datetime(string='銷售結束日', required=True, readonly=False, index=True
                                    , default=lambda self: fields.datetime.today())
    already_sale = fields.Integer(string='期間售出', compute='_compute_already_sale')

    amount_limit = fields.Integer(string='數量限制', required=True, readonly=False, index=True, default=999)

    def _check_sale_ok(self):
        products = self.env['product.template'].search([])
        for product in products:
            if product.sale_end_date < fields.datetime.today():
                product.write({'sale_ok': False})
            if product.sale_start_date == fields.datetime.today():
                product.write({'sale_ok': True})

    def _check_sale_amount(self):
        products = self.env['product.template'].search([])
        for product in products:
            if int(self.amount_limit * 0.9) < self.already_sale:
                product.write({'sale_ok': False})

    def _compute_already_sale(self):
        self.already_sale = 0
        product_id = self.env['product.product'].search([('product_tmpl_id', 'in', self.ids)])
        order_line_records = self.env['sale.order.line'].search([('state', 'in', ['sale', 'done']),
                                                                 ('product_id', '=', product_id[0].id),
                                                                 ('write_date', '>=', self.sale_start_date),
                                                                 ('write_date', '<=', self.sale_end_date)])
        for rec in order_line_records:
            self.already_sale += int(rec.product_uom_qty)
