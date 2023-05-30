from odoo import api, fields, models, _
from odoo.exceptions import UserError


class FacebookManage(models.Model):
    _name = "facebookmanage"
    _description = "manage the page"
    _order = 'is_valid desc, id desc'
        
    @api.onchange('site')
    def _getPageID(self):
        for rec in self:
            try:
                filter = str(rec.site)[len("https://www.facebook.com/groups/"):]
                try:  
                    group,page = str(filter).split("/permalink/")
                except:
                    group,page = str(filter).split("/posts/")
                    
                if(str(page).find("/")):
                    page = page[:-1]#濾掉/
                    
                self.page_id = group+ "_" + page
            except:
                self.page_id = "請務必填寫正確的網址"
                
            
    is_valid = fields.Boolean(string='是否擷取貼文', default=True)
    message_content = fields.Text(string='貼文內容(簡介)', required=True, index=True)
    page_id = fields.Char(string='貼文編號', index=True, default = _getPageID)
    site = fields.Char(string='網址', required=True, index=True)
    note = fields.Text(string='備註')
    comment_line = fields.One2many('facebookcomment', 'page_id', string='留言')
    update_time = fields.Char(string='更新時間', index=True)
    

   

class CommentManage(models.Model):
    _name = 'facebookcomment'
    _description = 'manage the commet of the page'
    _order = 'create_time desc, comment_id, id'
    
    @api.depends('comment_id')
    def _getlink_to_comment(self):
        for rec in self:
            for item in rec.page_id:
                for line in rec.comment_id:
                    try:
                        group,post = str(item.page_id).split('_')
                        rec.comment_link = "https://www.facebook.com/groups/"+group+'/posts/'+post+'/comments/'+rec.comment_id
                    except:
                        pass
        
    partner_id = fields.Many2one('res.partner',required=True)
    page_id = fields.Many2one('facebookmanage', string='貼文編號')
    create_time = fields.Datetime(string='留言時間', required=True, index=True)
    comment_id = fields.Char(string='留言編號', required=True, index=True)
    comment_content = fields.Text(string='留言內容', required=True, index=True)
    #state = fields.Selection([('incomplete', "未完成"), ('done', "完成"), ('error', "錯誤")], string="留言確認狀態", default='incomplete')
    state = fields.Char(string='留言狀態')
    comment_link = fields.Char(string="貼文連結", compute=_getlink_to_comment)
    
    
        
    
        
    
    
class FacebookConfig(models.Model):
    _name = 'facebookconfig'
    _description = 'commit the config detail'
    
    app_id = fields.Char(string='應用程式ID', index=True)
    app_secret = fields.Char(string='應用程式SECRET', index=True)
    accesstoken = fields.Char(string='ACCESSTOKEN', index=True)
    
    
    
class AuthFacebookUsers(models.Model):
    _inherit = 'res.users'
   
        
    @api.model
    def auth_facebook(self, provider, params):
        oauth_provider = self.env['auth.oauth.provider'].browse(provider)
        access_token = ""
        
        access_token = params.get('access_token')
        validation = self._auth_oauth_validate(provider, access_token)
        
        # required check
        if not validation.get('user_id'):
            # Workaround: facebook does not send 'user_id' in Open Graph Api
            if validation.get('id'):
                validation['user_id'] = validation['id']
            elif validation.get('username'):
                validation['user_id'] = validation['username']
            elif validation.get('sub'):
                validation['user_id'] = validation['sub']
            else:
                raise AccessDenied() 

        return validation['user_id']