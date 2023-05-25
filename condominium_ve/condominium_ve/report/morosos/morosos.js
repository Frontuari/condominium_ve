// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.query_reports["Morosos"] = {
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
		/*{
			"fieldname":"finance_book",
			"label": __("Finance Book"),
			"fieldtype": "Link",
			"options": "Finance Book"
		},
		{
			"fieldname":"cost_center",
			"label": __("Cost Center"),
			"fieldtype": "Link",
			"options": "Cost Center",
			get_query: () => {
				var company = frappe.query_report.get_filter_value('company');
				return {
					filters: {
						'company': company
					}
				}
			}
		},*/
		{
			"fieldname":"customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"options": "Customer"
		},
		/*{
			"fieldname":"customer_group",
			"label": __("Customer Group"),
			"fieldtype": "Link",
			"options": "Customer Group"
		},
		{
			"fieldname":"payment_terms_template",
			"label": __("Payment Terms Template"),
			"fieldtype": "Link",
			"options": "Payment Terms Template"
		},*/
		{
			"fieldname":"territory",
			"label": __("Territory"),
			"fieldtype": "Link",
			"options": "Territory"
		},
		/*{
			"fieldname":"sales_partner",
			"label": __("Sales Partner"),
			"fieldtype": "Link",
			"options": "Sales Partner"
		},
		{
			"fieldname":"sales_person",
			"label": __("Sales Person"),
			"fieldtype": "Link",
			"options": "Sales Person"
		},
		{
			"fieldname":"based_on_payment_terms",
			"label": __("Based On Payment Terms"),
			"fieldtype": "Check",
		},
		{
			"fieldname":"show_future_payments",
			"label": __("Show Future Payments"),
			"fieldtype": "Check",
		},
		{
			"fieldname":"show_gl_balance",
			"label": __("Show GL Balance"),
			"fieldtype": "Check",
		},*/
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
	"initial_depth": 2
}

erpnext.utils.add_dimensions('Accounts Receivable Summary', 9);
