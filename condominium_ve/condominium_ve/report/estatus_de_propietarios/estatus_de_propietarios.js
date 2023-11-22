// Copyright (c) 2023, Armando Rojas and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Estatus de Propietarios"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname":"report_date",
			"label": __("Posting Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname":"ageing_based_on",
			"label": __("Ageing Based On"),
			"fieldtype": "Select",
			"options": 'Posting Date\nDue Date',
			"default": "Due Date"
		},
		{
			"fieldname":"customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"options": "Customer"
		},
		{
			"fieldname":"territory",
			"label": __("Territory"),
			"fieldtype": "Link",
			"options": "Territory"
		},
		{
			"fieldname":"balance_type",
			"label": __("Balance Type"),
			"fieldtype": "Select",
			"options": '\nCon deuda\nSin deuda\nSaldo a favor',
			"default": "Con deuda"
		},
	],

	onload: function(report) {
		report.page.add_inner_button(__("Accounts Receivable"), function() {
			var filters = report.get_values();
			frappe.set_route('query-report', 'CxC Cobranza', { company: filters.company });
		});
	},

	"formatter":function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		// cambia el href al indicado
		if (column.id == "origin_commission"){
			if (data.is_invoice){
				value = value.replace("Item Group",'Sales Invoice');
				value = value.replace("item-group",'sales-invoice');
			}else{
				value = value.replace("Sales Invoice",'Item Group');
				value = value.replace("sales-invoice",'item-group');
			}
		}

		if (column.id == 'party' ){
			//console.log(value);
			if (data.indent == 0 || data.party == 'Total')
				value = "<span style='font-weight:bold'>" + value + "</span>";
		}
		

		return value;
	},
	"tree": true,
	"initial_depth": 2,
	onload: function(report) {
		let titulo_e = $(report.page.parent).find('h3[title="'+report.page.title+'"]');
		titulo_e.text("Estatus de Propietarios");
	}
};
