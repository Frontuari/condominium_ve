// Copyright (c) 2022, Armando Rojas and contributors
// For license information, please see license.txt

frappe.ui.form.on('Tenant Consultations', {
	 refresh: function(frm) {
		document.querySelector(`button[data-label='Guardar']`).remove()
	 },
	
	search: function(frm){

		


		frappe.call({
			method: "condominium_ve.condominium_ve.doctype.tenant_consultations.tenant_consultations.query_code",
			args: {
				code: frm.doc.code
			},

			btn: $(".primary-action"),
			freeze: true,
			callback: (response) => {
				let data = response.data

				frm.set_value('condominium_receipt', [])
				frm.set_value('payments_made', [])
				frm.set_value('condominium_common_expenses', [])


			
				data.sales_invoices.forEach(sales_invoice => {
					
					frm.add_child('condominium_receipt', {
						posting_date: sales_invoice.posting_date,
						voucher: sales_invoice.name ,
						amount: sales_invoice.rounded_total ,
						balance:  sales_invoice.outstanding_amount
					});
				})

				data.payments.forEach(payment => {
					
					frm.add_child('payments_made', {
						posting_date: payment.due_date,
						payment: payment.parent ,
						amount: payment.allocated_amount 
						
					});
				})

				data.cc_condo.forEach(cc => {
					
					frm.add_child('condominium_common_expenses', {
						posting_date: cc.posting_date,
						payment: cc.name ,
						amount: cc.total ,
						per_unit_amount: cc.total_per_unit
					});
				})


				
				frm.refresh_field('condominium_receipt');
				frm.refresh_field('payments_made');
				frm.refresh_field('condominium_common_expenses');



			},
			error: (r) => {
				console.log(r)
			},
		});
	}
});
