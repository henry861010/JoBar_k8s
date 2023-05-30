import base64
from odoo import http
from odoo.http import request, route
from odoo.addons.portal.controllers.portal import CustomerPortal
from datetime import timedelta, datetime as dt



class CustomerProfile(CustomerPortal):
    CustomerPortal.MANDATORY_BILLING_FIELDS.remove("street")
    CustomerPortal.OPTIONAL_BILLING_FIELDS.append("street")
    CustomerPortal.MANDATORY_BILLING_FIELDS.remove("city")
    CustomerPortal.OPTIONAL_BILLING_FIELDS.append("city")
    
    CustomerPortal.MANDATORY_BILLING_FIELDS.append("pickup_area")
    CustomerPortal.MANDATORY_BILLING_FIELDS.append("birthdays")
    
    CustomerPortal.OPTIONAL_BILLING_FIELDS.append("fb_app_id")


    @route(['/my/account'], type='http', auth='user', website=True)
    def account(self, redirect=None, **post):

        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        values.update({
            'error': {},
            'error_message': [],
        })

        if post and request.httprequest.method == 'POST':
            error, error_message = self.details_form_validate(post)
            values.update({'error': error, 'error_message': error_message})
            values.update(post)
            if not error:
                values = {key: post[key] for key in self.MANDATORY_BILLING_FIELDS}
                values.update({key: post[key]
                               for key in self.OPTIONAL_BILLING_FIELDS if key in post})
                values.update({'country_id': int(values.pop('country_id', 0))})
                values.update({'pickup_area': int(values.pop('pickup_area', 0))})
                values.update({'zip': values.pop('zipcode', '')})
                try:
                    #get order with date
                    app_id = int(values.pop('fb_app_id', 0))
                    obj = http.request.env['res.partner']
                    objs = obj.search([['fb_app_id','=',app_id]])
                    if not objs:
                        values.update({'fb_app_id': app_id})
                except:
                    pass
                if values.get('state_id') == '':
                    values.update({'state_id': False})
                partner.sudo().write(values)
                if redirect:
                    return request.redirect(redirect)
                return request.redirect('/my/home')

        countries = request.env['res.country'].sudo().search([])
        states = request.env['res.country.state'].sudo().search([])
        pickup = request.env['res.pickup_area'].sudo().search([])

        values.update({
            'partner': partner,
            'countries': countries,
            'states': states,
            'pickup': pickup,
            'has_check_vat': hasattr(request.env['res.partner'], 'check_vat'),
            'redirect': redirect,
            'page_name': 'my_details',
        })

        response = request.render("portal.portal_my_details", values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response


class DemoOdoo(http.Controller):
    @http.route('/my/searchorder', auth='user', website=True)
    def list(self, **kwargs):
        
        #Customer ID
        ids = request.env.user.partner_id.id
        id = "C"+str(ids).zfill(6)
        
        #get pickup date
        today = dt.now().date()-timedelta(1)
        t_year, t_week, t_weekday = today.isocalendar()
        if t_weekday >= 5:
            pd_year, pd_week, pd_weekday = (today + timedelta(days=7)).isocalendar()
            pickup_date = dt.fromisocalendar(pd_year, pd_week, 2).date().isoformat()
        elif t_weekday < 2:
            pickup_date = dt.fromisocalendar(t_year, t_week, 2).date().isoformat()
        else:
            pickup_date = dt.fromisocalendar(t_year, t_week, 5).date().isoformat()
        
        #get order with date
        obj = http.request.env['sale.order'].sudo()
        objs = obj.search([['pickup_date','=',pickup_date],['partner_id','=',ids]])
        
        #get total amount
        sum_amount = 0
        for order in objs: 
           sum_amount += int(order.amount_total)
        
        #區域ID替換
        area=["000","富岡(16:00-20:00)","楊梅(18:30-19:30)","湖口(16:00-20:00)"]
            
           
        return http.request.render(
            'jt_update_profiles.demo_odoo_template',{'objs': objs, 'id': id, 'total': sum_amount, 'date': pickup_date, "area": area})
            
       