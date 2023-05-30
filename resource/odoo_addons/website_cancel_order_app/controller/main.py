# -*- coding: utf-8 -*-

from odoo import fields, http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from datetime import datetime, timedelta, date

class CustomerPortal(CustomerPortal):

	def _prepare_portal_layout_values(self):
		values = super(CustomerPortal, self)._prepare_portal_layout_values()
		partner = request.env.user.partner_id

		SaleOrder = request.env['sale.order']
		quotation_count = SaleOrder.search_count([
			('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
			('state', 'in', ['sent', 'cancel','req_to_cancel'])
		])
		order_count = SaleOrder.search_count([
			('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
			('state', 'in', ['sale', 'done','req_to_cancel'])
		])

		values.update({
			'quotation_count': quotation_count,
			'order_count': order_count,

		})
		return values

	@http.route(['/my/quotes', '/my/quotes/page/<int:page>'], type='http', auth="user", website=True)
	def portal_my_quotes(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
		values = self._prepare_portal_layout_values()
		partner = request.env.user.partner_id
		SaleOrder = request.env['sale.order']
		domain = [
			('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
			('state', 'in', ['sent', 'cancel','req_to_cancel'])
		]

		searchbar_sortings = {
			'date': {'label': _('Order Date'), 'order': 'date_order desc'},
			'name': {'label': _('Reference'), 'order': 'name'},
			'stage': {'label': _('Stage'), 'order': 'state'},
		}

		# default sortby order
		if not sortby:
			sortby = 'date'
		sort_order = searchbar_sortings[sortby]['order']

		archive_groups = self._get_archive_groups('sale.order', domain)
		if date_begin and date_end:
			domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

		# count for pager
		quotation_count = SaleOrder.search_count(domain)
		# make pager
		pager = portal_pager(
			url="/my/quotes",
			url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
			total=quotation_count,
			page=page,
			step=self._items_per_page
		)
		# search the count to display, according to the pager data
		quotations = SaleOrder.search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
		request.session['my_quotations_history'] = quotations.ids[:100]
		values.update({
			'date': date_begin,
			'quotations': quotations.sudo(),
			'page_name': 'quote',
			'pager': pager,
			'archive_groups': archive_groups,
			'default_url': '/my/quotes',
			'searchbar_sortings': searchbar_sortings,
			'sortby': sortby,
		})
		return request.render("sale.portal_my_quotations", values)

	@http.route(['/my/orders', '/my/orders/page/<int:page>'], type='http', auth="user", website=True)
	def portal_my_orders(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
		values = self._prepare_portal_layout_values()
		partner = request.env.user.partner_id
		SaleOrder = request.env['sale.order']

		domain = [
			('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
			('state', 'in', ['sale', 'done','req_to_cancel'])
		]

		searchbar_sortings = {
			'date': {'label': _('Order Date'), 'order': 'date_order desc'},
			'name': {'label': _('Reference'), 'order': 'name'},
			'stage': {'label': _('Stage'), 'order': 'state'},
		}
		# default sortby order
		if not sortby:
			sortby = 'date'
		sort_order = searchbar_sortings[sortby]['order']

		archive_groups = self._get_archive_groups('sale.order', domain)
		if date_begin and date_end:
			domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

		# count for pager
		order_count = SaleOrder.search_count(domain)
		# pager
		pager = portal_pager(
			url="/my/orders",
			url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
			total=order_count,
			page=page,
			step=self._items_per_page
		)
		# content according to pager and archive selected
		orders = SaleOrder.search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
		request.session['my_orders_history'] = orders.ids[:100]
		values.update({
			'date': date_begin,
			'orders': orders.sudo(),
			'page_name': 'order',
			'pager': pager,
			'archive_groups': archive_groups,
			'default_url': '/my/orders',
			'searchbar_sortings': searchbar_sortings,
			'sortby': sortby,
		})
		return request.render("sale.portal_my_orders", values)

	@http.route(['/my/quotes/<int:order_id>/cancel_quote'], type='http', auth="public", methods=['GET'], website=True)
	def request_to_cancel_quote(self, order_id, **kw):
		sale_order = request.env['sale.order'].browse(order_id)
		sale_order_cancel = request.env['sale.order.cancel']

		sale_order_cancel.create({'name':sale_order.name,
								'quote_date':sale_order.date_order,
								'current_date':date.today(),
								'cancel_reason': kw.get('reason'),
						  		'cancel_remarks': kw.get('remarks'),
								})

		for res in sale_order_cancel:
			res.write({'state':'request_to_cancel'})

		sale_order.write({'state':'req_to_cancel'})

		return []

	@http.route(['/my/orders/<int:order_id>/cancel_order'], type='http', auth="public", methods=['GET'], website=True)
	def request_to_cancel_order(self, order_id, **kw):
		sale_order = request.env['sale.order'].browse(order_id)
		sale_order_cancel = request.env['sale.order.cancel']

		sale_order_cancel.create({'name':sale_order.name,
								'quote_date':sale_order.date_order,
								'current_date':date.today(),
								'cancel_reason': kw.get('reason'),
						  		'cancel_remarks': kw.get('remarks'),
								})

		for res in sale_order_cancel:
			res.write({'state':'request_to_cancel'})

		sale_order.sudo().write({'state':'req_to_cancel'})

		return []