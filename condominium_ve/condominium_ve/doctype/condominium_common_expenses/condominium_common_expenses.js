// Copyright (c) 2022, Armando Rojas and contributors
// For license information, please see license.txt

frappe.ui.form.on('Condominium Common Expenses', {
	refresh: function(frm) {
		if(!frm.doc.docstatus || frm.doc.docstatus == 0){
			frm.add_custom_button(__('Search'), () => {


			if(frm.doc.posting_date &&  frm.doc.condominium){

				frappe.call({
					method: "condominium_ve.condominium_ve.doctype.condominium_common_expenses.condominium_common_expenses.get_invoice_condo",
					args: {
						condo: frm.doc.condominium,
						date: frm.doc.posting_date,
					},
					// disable the button until the request is completed
					btn: $(".primary-action"),
					// freeze the screen until the request is completed
					freeze: true,
					callback: (response) => {
					  let data = response.data;

					  console.log(data)

					  frm.set_value('condominium_common_expenses_invoices', [])
					  frm.set_value('condominium_common_expenses_detail', [])


					  frm.doc.total_per_unit =  data.total_per_unit
					  frm.doc.total =  data.total
					 frm.doc.active_units =  data.active_units

			

					 data.invoices.forEach(e => {

						frm.add_child('condominium_common_expenses_invoices', {
						  invoice: e.invoice ,
						  date : e.date ,
						  supplier : e.supplier ,
						  amount : e.amount  ,

						});


					  });

					  data.detail.forEach(e => {

						frm.add_child('condominium_common_expenses_detail', {
							concept: e.concept ,
							supplier : e.supplier ,
							per_unit : e.per_unit ,
							amount : e.amount  ,
							tax : e.tax  ,
							net : e.net  ,

						});


					  });


					  frm.refresh_field('condominium_common_expenses_invoices');
					  frm.refresh_field('condominium_common_expenses_detail');
					  
					  frm.refresh_field('total_per_unit');
					  frm.refresh_field('total');
					  frm.refresh_field('active_units');
					},





					error: (r) => {
					 console.log(r)
					},
				  });

			}


			});
		  }else{
			frm.remove_custom_button(__('Search'))
		  }
	 }
});
