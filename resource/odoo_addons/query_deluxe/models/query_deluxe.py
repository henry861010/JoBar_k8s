from odoo import api, fields, models, _
from odoo.exceptions import UserError


class QueryDeluxe(models.Model):
    _name = "querydeluxe"
    _description = "Postgres queries from Odoo interface"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    rowcount = fields.Text(string='Rowcount')
    html = fields.Html(string='HTML')

    name = fields.Char(string='資料庫語法(忽略即可)')
    valid_query_name = fields.Char()

    note = fields.Text(string="備註")

    def print_result(self):
        return {
            'name': _("選擇列印格式"),
            'view_mode': 'form',
            'res_model': 'pdforientation',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_query_name': self.valid_query_name
            },
        }

    def copy_query(self):
        if self.tips:
            self.name = self.tips.name

    def execute(self):
        self.show_raw_output = False
        self.raw_output = ''

        self.rowcount = ''
        self.html = '<br></br>'

        self.valid_query_name = ''

        if self.name:

            headers = []
            datas = []

            try:
                self.env.cr.execute(self.name)
            except Exception as e:
                raise UserError(e)

            try:
                no_fetching = ['update', 'delete', 'create', 'insert', 'alter', 'drop']
                max_n = len(max(no_fetching))

                is_insides = [(o in self.name.lower().strip()[:max_n]) for o in no_fetching]
                if True not in is_insides:
                    headers = [d[0] for d in self.env.cr.description]
                    datas = self.env.cr.fetchall()
            except Exception as e:
                raise UserError(e)

            rowcount = self.env.cr.rowcount
            self.rowcount = "{0} row{1} processed".format(rowcount, 's' if 1 < rowcount else '')

            if headers and datas:
                self.valid_query_name = self.name
                self.raw_output = datas

                header_html = "".join(["<th style='border: 1px solid'>" + str(header) + "</th>" for header in headers])
                header_html = "<tr>" + "<th style='background-color:white !important'/>" + header_html + "</tr>"

                body_html = ""
                i = 0
                for data in datas:
                    i += 1
                    body_line = "<tr>" + "<td style='border-right: 3px double; border-bottom: 1px solid; background-color: black'>{0}</td>".format(
                        i)
                    for value in data:
                        body_line += "<td style='border: 1px solid; background-color: {0}'>{1}</td>".format(
                            'iron' if i % 2 == 0 else 'grey', str(value) if (value is not None) else '')

                    body_line += "</tr>"
                    body_html += body_line

                self.html = """
                            <table style="text-align: center">
                              <thead style="background-color: black">
                                {0}
                              </thead>
                            
                              <tbody>
                                {1}
                              </tbody>
                            </table>
                            """.format(header_html, body_html)


class QueryPickup(models.Model):
    _name = 'querypickup'
    _description = "Query For Pickup Order"
    _order = 'create_date desc, id'

    name = fields.Char(string='Query', required=True, default=" select * from sale_order")
    pickup_id = fields.Integer(string="取貨編號")
    pickup_date = fields.Date(string="取貨日期", default=fields.Date.today())
    pickup_area = fields.Many2one('res.pickup_area', string="取貨區域")
    discount_lock = fields.Boolean(string="已扣除購物金", default=False)
    update_lock = fields.Boolean(string="鎖定更新", default=False)
    note = fields.Text(string="備註")
    html = fields.Html(string='HTML')
    valid_query_name = fields.Char()
    rowcount = fields.Text(string='Rowcount')
    show_discount = fields.Integer(string='剩餘購物金')
    discount_amount = fields.Integer(string='購物金折抵')
    amount_total = fields.Integer(string='取貨總金額')

    def _show_user_discount(self):
        rec = self.env['res.partner'].sudo().search([('id', '=', self.pickup_id)])
        for item in rec:
            self.show_discount = item.user_discount

    def minus_user_discount(self):
        if self.discount_amount <= self.show_discount and self.discount_lock == False:
            self.amount_total = self.amount_total - self.discount_amount
            rec = self.env['res.partner'].sudo().search([('id', '=', self.pickup_id)])
            for item in rec:
                item.write({'user_discount': self.show_discount - self.discount_amount})
            self.discount_lock = True

    def execute(self):
        self._show_user_discount()
        self.discount_lock = False
        self.show_raw_output = False
        self.update_lock = False
        self.raw_output = ''

        self.html = '<br></br>'

        self.name = '''SELECT customerid as 編號,customername as 客戶名稱, 
                        phone as 連絡電話, pickup_area as 取貨區域,
                        product as 產品, price as 價格, SUM(amount) as 數量, state as 狀態,
                        string_agg(input.total::text, ',') as 訂單金額請忽略,
                        string_agg(saleorder,',') as 訂單編號請忽略
                        FROM (SELECT res_partner.id as customerid,
                        res_partner.name as customername,
                        res_partner.phone as phone,
                        res_pickup_area.name as pickup_area,
                        sale_order_line.name as product,
                        sale_order_line.price_unit as price,
                        sale_order_line.product_uom_qty as amount,
                        (sale_order.amount_total) as total ,
                        sale_order.pickup_date,
                        sale_order.state,
                        sale_order.name as saleorder FROM sale_order 
                        INNER JOIN res_partner ON sale_order.partner_id = res_partner.id 
                        INNER JOIN sale_order_line ON sale_order.id = sale_order_line.order_id 
                        INNER JOIN res_pickup_area ON sale_order.pickup_area = res_pickup_area.id 
                        WHERE pickup_date = '{}') as input 
                        WHERE input.customerid = {} and input.pickup_area = '{}' 
                        and input.amount != 0
                        and input.state in ('done', 'sale') 
                        GROUP BY product, customerid,price,customername,phone,pickup_area,state'''.format(
            self.pickup_date, self.pickup_id, self.pickup_area.name)
        self.executesql()

    def update_state(self):
        if not self.update_lock:#avoid multiple click
            # update state
            rec = self.env['sale.order'].sudo().search(
                [('partner_id', '=', self.pickup_id), ('pickup_date', '=', self.pickup_date),
                 ('pickup_area', '=', self.pickup_area.id)])
            for item in rec:
                item.sudo().write({'state': 'done'})

            # record discount
            if int(self.show_discount) > 0:
                self.env['discount.manage'].sudo().create({'partner_id': self.pickup_id,
                                                           'order_id': rec[0].id,
                                                           'origin_rewards':self.show_discount,
                                                           'discount_rewards': self.discount_amount,
                                                           'left_rewards': str(int(self.show_discount)-int(self.discount_amount)),
                                                           })
            # commit
            self.env.cr.commit()

            # reshow the data
            self.name = '''SELECT * FROM sale_order where partner_id = {} and pickup_date = '{}';'''.format(self.pickup_id,
                                                                                                            self.pickup_date)

            discount_amount = self.amount_total
            self.executesql()
            self.execute()
            self.amount_total = discount_amount
        self.update_lock = True

    def executesql(self):
        self.valid_query_name = ''
        self.amount_total = 0
        if self.name:

            headers = []
            datas = []

            try:
                self.env.cr.execute(self.name)

            except Exception as e:
                raise UserError(e)

            try:
                no_fetching = ['delete', 'create', 'insert', 'alter', 'drop']
                max_n = len(max(no_fetching))

                is_insides = [(o in self.name.lower().strip()[:max_n]) for o in no_fetching]
                if True not in is_insides:
                    headers = [d[0] for d in self.env.cr.description]
                    datas = self.env.cr.fetchall()
            except Exception as e:
                raise UserError(e)

            rowcount = self.env.cr.rowcount
            self.rowcount = "{0} row{1} processed".format(rowcount, 's' if 1 < rowcount else '')

            if headers and datas and self.name.find("SELECT") < 10:
                self.valid_query_name = self.name
                self.raw_output = datas

                header_html = "".join(["<th style='border: 1px solid'>" + str(header) + "</th>" for header in headers])
                header_html = "<tr>" + "<th style='background-color:white !important'/>" + header_html + "</tr>"

                body_html = ""
                i = 0
                order_list_record = []
                for data in datas:
                    try:
                        order_list = data[9].split(',')
                        amount_temp = data[8].split(',')
                    except:
                        order_list = []
                        amount_temp = []

                    for index in range(len(order_list)):
                        if order_list[index] not in order_list_record:
                            self.amount_total += int(amount_temp[index])
                            order_list_record.append(order_list[index])

                    i += 1
                    body_line = "<tr>" + "<td style='border-right: 3px double; border-bottom: 1px solid; background-color: black'>{0}</td>".format(
                        i)
                    for value in data:
                        value = '未取貨' if (str(value).find('sale') >= 0) else value
                        value = '完成' if (str(value).find('done') >= 0) else value
                        body_line += "<td style='border: 1px solid; background-color: {0}'>{1}</td>".format(
                            'iron' if i % 2 == 0 else 'grey', str(value) if (value is not None) else '')
                    body_line += "</tr>"
                    body_html += body_line

                self.html = """
                            <table style="text-align: center">
                              <thead style="background-color: black">
                                {0}
                              </thead>
                            
                              <tbody>
                                {1}
                              </tbody>
                            </table>
                            """.format(header_html, body_html)
