from odoo import api, fields, models, _


class DiscountManage(models.Model):
    _name = "discount.manage"
    _description = "record the discount"
    _order = 'id desc, discount_date desc'

    # 客戶編號, 訂單編號, 購物金原始金額, 折抵金額, 該筆訂單折抵後金額, 折抵日期
    partner_id = fields.Many2one('res.partner', string="客戶名稱", required=True)
    order_id = fields.Many2one('sale.order', string="訂單編號")
    origin_rewards = fields.Integer(string='購物金原始金額', required=True, index=True)
    discount_rewards = fields.Integer(string='折抵金額', index=True)
    left_rewards = fields.Integer(string='折抵後金額', required=True, index=True)
    discount_date = fields.Datetime(string='折抵日期', default=fields.Datetime.now)
