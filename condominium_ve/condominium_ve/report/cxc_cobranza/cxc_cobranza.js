//"json": "{\"columns\":[{\"label\":\"Posting Date\",\"fieldname\":\"posting_date\",\"fieldtype\":\"Date\",\"options\":null,\"width\":90,\"id\":\"posting_date\",\"name\":\"Fecha de Contabilizaci\u00f3n\",\"editable\":false},{\"label\":\"Due Date\",\"fieldname\":\"due_date\",\"fieldtype\":\"Date\",\"options\":null,\"width\":90,\"id\":\"due_date\",\"name\":\"Fecha de vencimiento\",\"editable\":false},{\"label\":\"Receivable Account\",\"fieldname\":\"party_account\",\"fieldtype\":\"Link\",\"options\":\"Account\",\"width\":180,\"id\":\"party_account\",\"name\":\"Cuenta por cobrar\",\"editable\":false,\"compareValue\":null},{\"label\":\"Comprobante No.\",\"fieldname\":\"voucher_no\",\"fieldtype\":\"Dynamic Link\",\"options\":\"voucher_type\",\"width\":180,\"id\":\"voucher_no\",\"name\":\"Comprobante No.\",\"editable\":false,\"compareValue\":null},{\"label\":\"Cantidad facturada\",\"fieldname\":\"invoiced\",\"fieldtype\":\"Currency\",\"options\":\"currency\",\"width\":120,\"id\":\"invoiced\",\"name\":\"Cantidad facturada\",\"editable\":false,\"compareValue\":null},{\"label\":\"Cantidad Pagada\",\"fieldname\":\"paid\",\"fieldtype\":\"Currency\",\"options\":\"currency\",\"width\":120,\"id\":\"paid\",\"name\":\"Cantidad Pagada\",\"editable\":false,\"compareValue\":null},{\"label\":\"Nota de cr\u00e9dito\",\"fieldname\":\"credit_note\",\"fieldtype\":\"Currency\",\"options\":\"currency\",\"width\":120,\"id\":\"credit_note\",\"name\":\"Nota de cr\u00e9dito\",\"editable\":false,\"compareValue\":null},{\"label\":\"Monto pendiente\",\"fieldname\":\"outstanding\",\"fieldtype\":\"Currency\",\"options\":\"currency\",\"width\":120,\"id\":\"outstanding\",\"name\":\"Monto pendiente\",\"editable\":false,\"compareValue\":null},{\"label\":\"Centro de costos\",\"fieldname\":\"cost_center\",\"fieldtype\":\"Data\",\"options\":null,\"width\":120,\"id\":\"cost_center\",\"name\":\"Centro de costos\",\"editable\":false,\"compareValue\":null},{\"label\":\"Tipo de Comprobante\",\"fieldname\":\"voucher_type\",\"fieldtype\":\"Data\",\"options\":null,\"width\":120,\"id\":\"voucher_type\",\"name\":\"Tipo de Comprobante\",\"editable\":false,\"compareValue\":null},{\"label\":\"Contacto del Cliente\",\"fieldname\":\"customer_primary_contact\",\"fieldtype\":\"Link\",\"options\":\"Contact\",\"width\":120,\"id\":\"customer_primary_contact\",\"name\":\"Contacto del Cliente\",\"editable\":false,\"compareValue\":null},{\"label\":\"Cliente\",\"fieldname\":\"party\",\"fieldtype\":\"Link\",\"options\":\"Customer\",\"width\":180,\"id\":\"party\",\"name\":\"Cliente\",\"editable\":false,\"compareValue\":null},{\"label\":\"D\u00edas de Vencimiento\",\"fieldname\":\"age\",\"fieldtype\":\"Int\",\"options\":null,\"width\":80,\"id\":\"age\",\"name\":\"D\u00edas de Vencimiento\",\"editable\":false,\"compareValue\":null},{\"label\":\"0-30\",\"fieldname\":\"range1\",\"fieldtype\":\"Currency\",\"options\":\"currency\",\"width\":120,\"id\":\"range1\",\"name\":\"0-30\",\"editable\":false,\"compareValue\":null},{\"label\":\"31-60\",\"fieldname\":\"range2\",\"fieldtype\":\"Currency\",\"options\":\"currency\",\"width\":120,\"id\":\"range2\",\"name\":\"31-60\",\"editable\":false,\"compareValue\":null},{\"label\":\"61-90\",\"fieldname\":\"range3\",\"fieldtype\":\"Currency\",\"options\":\"currency\",\"width\":120,\"id\":\"range3\",\"name\":\"61-90\",\"editable\":false,\"compareValue\":null},{\"label\":\"91-120\",\"fieldname\":\"range4\",\"fieldtype\":\"Currency\",\"options\":\"currency\",\"width\":120,\"id\":\"range4\",\"name\":\"91-120\",\"editable\":false,\"compareValue\":null},{\"label\":\"121-Arriba\",\"fieldname\":\"range5\",\"fieldtype\":\"Currency\",\"options\":\"currency\",\"width\":120,\"id\":\"range5\",\"name\":\"121-Arriba\",\"editable\":false,\"compareValue\":null},{\"label\":\"Divisa / Moneda\",\"fieldname\":\"currency\",\"fieldtype\":\"Link\",\"options\":\"Currency\",\"width\":80,\"id\":\"currency\",\"name\":\"Divisa / Moneda\",\"editable\":false,\"compareValue\":null},{\"label\":\"Cliente LPO\",\"fieldname\":\"po_no\",\"fieldtype\":\"Data\",\"options\":null,\"width\":120,\"id\":\"po_no\",\"name\":\"Cliente LPO\",\"editable\":false,\"compareValue\":null},{\"label\":\"Territorio o Sector\",\"fieldname\":\"territory\",\"fieldtype\":\"Link\",\"options\":\"Territory\",\"width\":120,\"id\":\"territory\",\"name\":\"Territorio o Sector\",\"editable\":false,\"compareValue\":null},{\"label\":\"Categor\u00eda de Cliente\",\"fieldname\":\"customer_group\",\"fieldtype\":\"Link\",\"options\":\"Customer Group\",\"width\":120,\"id\":\"customer_group\",\"name\":\"Categor\u00eda de Cliente\",\"editable\":false,\"compareValue\":null}]}",
 
frappe.query_reports["CxC Cobranza"] = {
	"treeView": true,
	"name_field": "name",
	"parent_field": "name",
	"initial_depth": 1,			//The level to which the initial rendering will expand to
	
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1,
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname": "report_date",
			"label": __("Posting Date"),
			"fieldtype": "Date"
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "finance_book",
			"label": __("Finance Book"),
			"fieldtype": "Link",
			"options": "Finance Book"
		},
		{
			"fieldname": "cost_center",
			"label": __("Cost Center"),
			"fieldtype": "Link",
			"options": "Cost Center",
			get_query: () => {
				var company = frappe.query_report.get_filter_value('company');
				return {
					filters: {
						'company': company
					}
				};
			}
		},
		{
			"fieldname": "customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"options": "Customer",
			on_change: () => {
				var customer = frappe.query_report.get_filter_value('customer');
				var company = frappe.query_report.get_filter_value('company');
				if (customer) {
					frappe.db.get_value('Customer', customer, ["tax_id", "customer_name", "payment_terms"], function(value) {
						frappe.query_report.set_filter_value('tax_id', value["tax_id"]);
						frappe.query_report.set_filter_value('customer_name', value["customer_name"]);
						frappe.query_report.set_filter_value('payment_terms', value["payment_terms"]);
					});

					frappe.db.get_value('Customer Credit Limit', {'parent': customer, 'company': company},
						["credit_limit"], function(value) {
						if (value) {
							frappe.query_report.set_filter_value('credit_limit', value["credit_limit"]);
						}
					}, "Customer");
				} else {
					frappe.query_report.set_filter_value('tax_id', "");
					frappe.query_report.set_filter_value('customer_name', "");
					frappe.query_report.set_filter_value('credit_limit', "");
					frappe.query_report.set_filter_value('payment_terms', "");
				}
			}
		},
		{
			"fieldname": "party_account",
			"label": __("Receivable Account"),
			"fieldtype": "Link",
			"options": "Account",
			get_query: () => {
				var company = frappe.query_report.get_filter_value('company');
				return {
					filters: {
						'company': company,
						'account_type': 'Receivable',
						'is_group': 0
					}
				};
			}
		},
		{
			"fieldname": "ageing_based_on",
			"label": __("Ageing Based On"),
			"fieldtype": "Select",
			"options": 'Posting Date\nDue Date',
			"default": "Due Date"
		},
		{
			"fieldname": "range1",
			"label": __("Ageing Range 1"),
			"fieldtype": "Int",
			"default": "30",
			"reqd": 1
		},
		{
			"fieldname": "range2",
			"label": __("Ageing Range 2"),
			"fieldtype": "Int",
			"default": "60",
			"reqd": 1
		},
		{
			"fieldname": "range3",
			"label": __("Ageing Range 3"),
			"fieldtype": "Int",
			"default": "90",
			"reqd": 1
		},
		{
			"fieldname": "range4",
			"label": __("Ageing Range 4"),
			"fieldtype": "Int",
			"default": "120",
			"reqd": 1
		},
		{
			"fieldname": "customer_group",
			"label": __("Customer Group"),
			"fieldtype": "Link",
			"options": "Customer Group"
		},
		{
			"fieldname": "payment_terms_template",
			"label": __("Payment Terms Template"),
			"fieldtype": "Link",
			"options": "Payment Terms Template"
		},
		{
			"fieldname": "sales_partner",
			"label": __("Sales Partner"),
			"fieldtype": "Link",
			"options": "Sales Partner"
		},
		{
			"fieldname": "sales_person",
			"label": __("Sales Person"),
			"fieldtype": "Link",
			"options": "Sales Person"
		},
		{
			"fieldname": "territory",
			"label": __("Territory"),
			"fieldtype": "Link",
			"options": "Territory"
		},
		{
			"fieldname": "group_by_party",
			"label": __("Group By Customer"),
			"fieldtype": "Check"
		},
		{
			"fieldname": "based_on_payment_terms",
			"label": __("Based On Payment Terms"),
			"fieldtype": "Check",
		},
		{
			"fieldname": "show_future_payments",
			"label": __("Show Future Payments"),
			"fieldtype": "Check",
		},
		{
			"fieldname": "show_delivery_notes",
			"label": __("Show Linked Delivery Notes"),
			"fieldtype": "Check",
		},
		{
			"fieldname": "show_sales_person",
			"label": __("Show Sales Person"),
			"fieldtype": "Check",
		},
		{
			"fieldname": "show_remarks",
			"label": __("Show Remarks"),
			"fieldtype": "Check",
		},
		{
			"fieldname": "tax_id",
			"label": __("Tax Id"),
			"fieldtype": "Data",
			"hidden": 1
		},
		{
			"fieldname": "customer_name",
			"label": __("Customer Name"),
			"fieldtype": "Data",
			"hidden": 1
		},
		{
			"fieldname": "payment_terms",
			"label": __("Payment Tems"),
			"fieldtype": "Data",
			"hidden": 1
		},
		{
			"fieldname": "credit_limit",
			"label": __("Credit Limit"),
			"fieldtype": "Currency",
			"hidden": 1
		}
	],
	/*
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && data.bold) {
			value = value.bold();

		}
		return value;
	},*/

	onload: function(report) {
		console.log(report.get_values());
		//report.filters.report_date = frappe.datetime.get_today()
		//console.log(frappe.datetime.get_today());

		//console.log(report.get_values());
		report.page.add_inner_button(__('Enviar Correos'), () => {
			//console.log(report.get_values());
		  let filtros = report.get_values();
		  
		  filtros['docstatus'] = 1;

          frappe.call({
            method:
              "condominium_ve.condominium_ve.report.cxc_cobranza.cxc_cobranza.send_email",
            args: {
              filters: filtros
            },

            btn: $(".primary-action"),

            freeze: true,
            callback: (response) => {

            },

            error: (r) => {
              console.log(r);
            },
          });

      });
		
	}
	

	
}

//erpnext.utils.add_dimensions('Accounts Receivable', 9);