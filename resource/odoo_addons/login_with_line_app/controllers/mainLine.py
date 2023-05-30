# -*- coding: utf-8 -*-

import functools
import logging

import json

import werkzeug.urls
import werkzeug.utils

from odoo.http import request

from odoo.addons.auth_signup.controllers.main import AuthSignupHome as Home
from odoo.addons.auth_oauth.controllers.main import OAuthLogin as login

_logger = logging.getLogger(__name__)


class OAuthLogin(Home):

    def list_providers(self):
        try:
            providers = request.env['auth.oauth.provider'].sudo().search_read([('enabled', '=', True)])
        except Exception:
            providers = []
        for provider in providers:
            return_url = request.httprequest.url_root + 'auth_oauth/signin'
            state = self.get_state(provider)
            if provider.get('name').find("Line") != -1:
                params = dict(
                    response_type='code',
                    client_id=provider['client_id'],
                    redirect_uri=return_url,
                    scope=provider['scope'],
                    state=json.dumps(state),
                )
            else:
                params = dict(
                    response_type='token',
                    client_id=provider['client_id'],
                    redirect_uri=return_url,
                    scope=provider['scope'],
                    state=json.dumps(state),
		    bot_prompt='normal',
                )
            provider['auth_link'] = "%s?%s" % (provider['auth_endpoint'], werkzeug.urls.url_encode(params))
            print("pro", provider)
        return providers


class LineOAuthLogin(login):
    def get_state(self, provider):
        redirect = request.params.get('redirect') or 'web'
        if not redirect.startswith(('//', 'http://', 'https://')):
            redirect = '%s%s' % (request.httprequest.url_root, redirect[1:] if redirect[0] == '/' else redirect)
        state = dict(
            d=request.session.db,
            p=provider['id'],
            r=werkzeug.urls.url_quote_plus(redirect),
        )
        token = request.params.get('token')
        if token:
            state['t'] = token
        code = request.params.get('code')
        if code:
            state['t'] = code
        return state
