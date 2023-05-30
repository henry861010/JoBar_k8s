from odoo import api, fields, models, _


class PdfOrientation(models.TransientModel):
    _name = 'pdforientation'
    _description = "Select the orientation of the pdf"

    def orientation_choices(self):
        return [('landscape', _('橫式列印')), ('portrait', _('直式列印'))]

    orientation = fields.Selection(string="PDF格式", selection=orientation_choices, default='landscape')
    query_name = fields.Char(string="資料庫語法")

    def print_pdf(self):
        self.env.cr.execute(self.query_name)
        headers = [d[0] for d in self.env.cr.description]
        bodies = self.env.cr.fetchall()

        action_print_pdf = self.env.ref('query_deluxe.action_print_pdf')

        if self.orientation == 'landscape':
            action_print_pdf.paperformat_id = self.env.ref('query_deluxe.paperformat_landscape').id
        elif self.orientation == 'portrait':
            action_print_pdf.paperformat_id = self.env.ref('query_deluxe.paperformat_portrait').id

        action_print_pdf.name = self.query_name

        append_data = {
            'headers': headers,
            'bodies': bodies
        }
        return action_print_pdf.report_action(self, data=append_data)
