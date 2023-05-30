# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

#replace this file in addons/auth_oauth/models/res_users.py

import json

import requests
import werkzeug.http

from odoo import api, fields, models
from odoo.exceptions import AccessDenied, UserError
from odoo.addons.auth_signup.models.res_users import SignupError

from odoo.addons import base
base.models.res_users.USER_PRIVATE_FIELDS.append('oauth_access_token')

class ResUsers(models.Model):
    _inherit = 'res.users'

    oauth_provider_id = fields.Many2one('auth.oauth.provider', string='OAuth Provider')
    oauth_uid = fields.Char(string='OAuth User ID', help="Oauth Provider user_id", copy=False)
    oauth_access_token = fields.Char(string='OAuth Access Token', readonly=True, copy=False)

    _sql_constraints = [
        ('uniq_users_oauth_provider_oauth_uid', 'unique(oauth_provider_id, oauth_uid)', 'OAuth UID must be unique per provider'),
    ]

    def _auth_oauth_rpc(self, endpoint, access_token):
        if self.env['ir.config_parameter'].sudo().get_param('auth_oauth.authorization_header'):
            response = requests.get(endpoint, headers={'Authorization': 'Bearer %s' % access_token}, timeout=10)
        else:
            response = requests.get(endpoint, params={'access_token': access_token}, timeout=10)

        if response.ok: # nb: could be a successful failure
            return response.json()

        auth_challenge = werkzeug.http.parse_www_authenticate_header(
            response.headers.get('WWW-Authenticate'))
        if auth_challenge.type == 'bearer' and 'error' in auth_challenge:
            return dict(auth_challenge)

        return {'error': 'invalid_request'}

    @api.model
    def _auth_oauth_validate(self, provider, access_token):
        """ return the validation data corresponding to the access token """
        oauth_provider = self.env['auth.oauth.provider'].browse(provider)
        validation = self._auth_oauth_rpc(oauth_provider.validation_endpoint, access_token)
        if validation.get("error"):
            raise Exception(validation['error'])
        if oauth_provider.data_endpoint:
            data = self._auth_oauth_rpc(oauth_provider.data_endpoint, access_token)
            validation.update(data)
        # unify subject key, pop all possible and get most sensible. When this
        # is reworked, BC should be dropped and only the `sub` key should be
        # used (here, in _generate_signup_values, and in _auth_oauth_signin)
        subject = next(filter(None, [
            validation.pop(key, None)
            for key in [
                'sub', # standard
                'id', # google v1 userinfo, facebook opengraph
                'user_id', # google tokeninfo, odoo (tokeninfo)
            ]
        ]), None)
        if not subject:
            raise AccessDenied('Missing subject identity')
        validation['user_id'] = subject

        return validation

    @api.model
    def _generate_signup_values(self, provider, validation, params):
        oauth_uid = validation['user_id']
        try:
            email = validation['email']
        except:
            email = validation.get('email', 'provider_%s_user_%s' % (provider, oauth_uid))
        name = validation.get('name', email)
        return {
            'name': name,
            'login': email,
            'email': email,
            'oauth_provider_id': provider,
            'oauth_uid': oauth_uid,
            'oauth_access_token': params['access_token'],
            'active': True,
        }

    @api.model
    def _auth_oauth_signin(self, provider, validation, params):
        """ retrieve and sign in the user corresponding to provider and validated access token
            :param provider: oauth provider id (int)
            :param validation: result of validation of access token (dict)
            :param params: oauth parameters (dict)
            :return: user login (str)
            :raise: AccessDenied if signin failed

            This method can be overridden to add alternative signin methods.
        """
        oauth_uid = validation['user_id']
        try:
            oauth_user = self.search([("oauth_uid", "=", oauth_uid), ('oauth_provider_id', '=', provider)])
            if not oauth_user:
                raise AccessDenied()
            assert len(oauth_user) == 1
            oauth_user.write({'oauth_access_token': params['access_token']})
            return oauth_user.login
        except AccessDenied as access_denied_exception:
            if self.env.context.get('no_user_creation'):
                return None
            state = json.loads(params['state'])
            token = state.get('t')
            values = self._generate_signup_values(provider, validation, params)
            try:
                login, _ = self.signup(values, token)
                return login
            except (SignupError, UserError):
                raise access_denied_exception

    @api.model
    def auth_oauth(self, provider, params):
        oauth_provider = self.env['auth.oauth.provider'].browse(provider)
        access_token = ""
        print("Accesstoken:{}".format(access_token))
        if oauth_provider.name.find("Line") == 0:
            client_secret = "a512b710507d682c5dd847b7b49bca89"
            callback = "http://manage.jobar.shop/auth_oauth/signin"

            line_headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            token_line_params = {
                "grant_type": "authorization_code",
                "client_id": "1661139702",
                "client_secret": client_secret,
                "code": params['code'],
                "redirect_uri": callback
            }

            response_token = requests.post("https://api.line.me/oauth2/v2.1/token", data=token_line_params, headers=line_headers)
            load = response_token.json()
            access_token = load.get("access_token")
            id_token = load.get("id_token")
            profile_line_params = {
                "id_token": id_token,
                "client_id": "1661139702",
            }

            validation = requests.post("https://api.line.me/oauth2/v2.1/verify", data=profile_line_params, headers=line_headers)
            validation = validation.json()
            validation['user_id'] = validation['sub']

            params["access_token"] = access_token
            params["id_token"] = id_token
            params['token_type'] = load.get("token_type")
            params['expires_in'] = load.get("expires_in")

            validation['access_token'] = access_token
            validation['refresh_token'] = load.get("refresh_token")
            validation['expires_in'] = load.get("expires_in")
            validation['scope'] = load.get("scope")
            validation['id_token'] = load.get("id_token")
        else:
            access_token = params.get('access_token')
            validation = self._auth_oauth_validate(provider, access_token)


        if not validation.get('user_id'):
            if validation.get('id'):
                validation['user_id'] = validation['id']
            elif validation.get('username'):
                validation['user_id'] = validation['username']
            elif validation.get('sub'):
                validation['user_id'] = validation['sub']
            else:
                raise AccessDenied()

        login = self._auth_oauth_signin(provider, validation, params)
        if not login:
            raise AccessDenied()

        return (self.env.cr.dbname, login, access_token)

    def _check_credentials(self, password, env):
        try:
            return super(ResUsers, self)._check_credentials(password, env)
        except AccessDenied:
            passwd_allowed = env['interactive'] or not self.env.user._rpc_api_keys_only()
            if passwd_allowed and self.env.user.active:
                res = self.sudo().search([('id', '=', self.env.uid), ('oauth_access_token', '=', password)])
                if res:
                    return
            raise

    def _get_session_token_fields(self):
        return super(ResUsers, self)._get_session_token_fields() | {'oauth_access_token'}