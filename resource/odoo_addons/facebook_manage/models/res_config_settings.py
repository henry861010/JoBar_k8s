from odoo import fields, models


class FacebookManageSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    getComment_freq = fields.Integer(string="貼文更新頻率（預設15min)", default=15)
    facebook_status = fields.Char(string="臉書目前狀態", default='無異常狀況')

    def set_values(self):
        super(FacebookManageSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('facebookconfig.facebook_status', self.facebook_status)
        self.env['ir.config_parameter'].sudo().set_param('facebookconfig.renew_freq', self.getComment_freq)

    def get_values(self):
        res = super(FacebookManageSettings, self).get_values()

        renew_freq_temp = self.env['ir.config_parameter'].sudo().get_param("facebookconfig.renew_freq")
        facebook_status_temp = self.env['ir.config_parameter'].sudo().get_param("facebookconfig.facebook_status")

        res.update(
                   getComment_freq=int(renew_freq_temp),
                   facebook_status=facebook_status_temp,
                   )
        return res
