odoo.define('website_cancel_order_app.cancel_order',function(require){
"use strict";
	$(document).ready(function() {
		var ajax=require('web.ajax');
		var core=require('web.core');
		var _t=core._t;
		var quote_ids;
		var order_ids;
		
		$(".js_cancel_quote").click(function(){
			quote_ids = $(this).attr('id')
			$('#modalcancelquote').modal('show');
		});
		$(".submit_btn").click(function(){
			var quote_reason = $("#reason").val()
			var quote_remarks = $("#remarks").val()
			var dataitem={
                reason: quote_reason,
                remarks: quote_remarks,
            };
            if (quote_reason && quote_remarks){
				$.ajax({
	                url: '/my/quotes/'+quote_ids+'/cancel_quote',
	                type: "GET",
	                datatype: 'http',
	                data: dataitem,
	            	success: function () 
	                {
	                    window.location.href="/my/quotes";
	                }
	        	});
        	}    
		});
		
		$(".js_cancel_order").on('click', function () {
			order_ids = $(this).attr('id')
			$('#modalcancelorder').modal('show');
		});
		
		$(".submit_order").click(function(){
			var order_reason = $("#order_reason").val()
			var order_remarks = $("#order_remarks").val()
			var dataitem={
                reason: order_reason,
                remarks: order_remarks,
            };
            if (order_reason && order_remarks){
				$.ajax({
	                url: '/my/orders/'+order_ids+'/cancel_order',
	                type: 'GET',
	                dataType: 'http',
	                data: dataitem,
	            	success: function () 
	                {
	                    window.location.href="/my/orders";
	                }
	        	}); 
        	}
		});
	});
});