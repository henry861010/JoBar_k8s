import base64
import json
from odoo import http
from odoo.http import request, route
from odoo.addons.portal.controllers.portal import CustomerPortal
from datetime import timedelta, datetime as dt
from werkzeug.exceptions import BadRequest
from odoo import registry as registry_get
from odoo import api, http, SUPERUSER_ID, _
import werkzeug.urls

import functools
def fragment_to_query_string(func):
    @functools.wraps(func)
    def wrapper(self, *a, **kw):
        kw.pop('debug', False)
        if not kw:
            return """<html><head><script>
                var l = window.location;
                var q = l.hash.substring(1);
                var r = l.pathname + l.search;
                if(q.length !== 0) {
                    var s = l.search ? (l.search === '?' ? '' : '&') : '?';
                    r = l.pathname + l.search + s + q;
                }
                if (r == l.pathname) {
                    r = '/';
                }
                window.location = r;
            </script></head><body></body></html>"""
        return func(self, *a, **kw)
    return wrapper
    

class ValidateFacebookAccount(http.Controller):
    @http.route('/my/validate', auth='user', website=True)
    def list(self, **kwargs):
        
        #Customer ID
        partner_id = request.env.user.partner_id.id
        id = "C"+str(partner_id).zfill(6)
        
        #get data 
        obj = http.request.env['res.partner'].sudo()
        objs = obj.search([['id','=',partner_id],['is_enroll','=','true']])#,'and',['partner_id','=',partner_id])['page_id','=','197']
        
        #get data 
        partner = http.request.env['res.partner'].sudo()
        partners = partner.search([['id','=',partner_id]])
        
        #get data 
        enroll = http.request.env['res.users'].sudo()
        enrolls = enroll.search([['partner_id','=',partner_id]])
        
        check_filled_id = True
        try:
            if len(partners.fb_app_id) < 15:
                check_filled_id = False
        except:
            check_filled_id = False#如果未填寫就是False
               
        return http.request.render(
            'facebook_manage.account_validate',{'objs': objs, 'id': id, 'partners': partners, 'enrolls': enrolls, 'check_filled_ids': check_filled_id})
            
            
class OAuthController(http.Controller):
    @http.route('/auth/facebook', type='http', auth='user')
    @fragment_to_query_string
    def signin(self, **kw):
        state = json.loads(kw['state'])
        dbname = state['d']
        if not http.db_filter([dbname]):
            return BadRequest()
        provider = state['p']
        context = state.get('c', {})
        registry = registry_get(dbname)
        with registry.cursor() as cr:
            try:
                env = api.Environment(cr, SUPERUSER_ID, context)
                fb_app_id = env['res.users'].sudo().auth_facebook(provider, kw)
                request.env.user.partner_id.write({'fb_app_id':fb_app_id})
                request.redirect('/my/account')
            except:
                pass
        return werkzeug.utils.redirect('/my/account')