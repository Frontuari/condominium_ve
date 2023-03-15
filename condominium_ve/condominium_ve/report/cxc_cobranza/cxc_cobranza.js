//"json": "{\"columns\":[{\"label\":\"Posting Date\",\"fieldname\":\"posting_date\",\"fieldtype\":\"Date\",\"options\":null,\"width\":90,\"id\":\"posting_date\",\"name\":\"Fecha de Contabilizaci\u00f3n\",\"editable\":false},{\"label\":\"Due Date\",\"fieldname\":\"due_date\",\"fieldtype\":\"Date\",\"options\":null,\"width\":90,\"id\":\"due_date\",\"name\":\"Fecha de vencimiento\",\"editable\":false},{\"label\":\"Receivable Account\",\"fieldname\":\"party_account\",\"fieldtype\":\"Link\",\"options\":\"Account\",\"width\":180,\"id\":\"party_account\",\"name\":\"Cuenta por cobrar\",\"editable\":false,\"compareValue\":null},{\"label\":\"Comprobante No.\",\"fieldname\":\"voucher_no\",\"fieldtype\":\"Dynamic Link\",\"options\":\"voucher_type\",\"width\":180,\"id\":\"voucher_no\",\"name\":\"Comprobante No.\",\"editable\":false,\"compareValue\":null},{\"label\":\"Cantidad facturada\",\"fieldname\":\"invoiced\",\"fieldtype\":\"Currency\",\"options\":\"currency\",\"width\":120,\"id\":\"invoiced\",\"name\":\"Cantidad facturada\",\"editable\":false,\"compareValue\":null},{\"label\":\"Cantidad Pagada\",\"fieldname\":\"paid\",\"fieldtype\":\"Currency\",\"options\":\"currency\",\"width\":120,\"id\":\"paid\",\"name\":\"Cantidad Pagada\",\"editable\":false,\"compareValue\":null},{\"label\":\"Nota de cr\u00e9dito\",\"fieldname\":\"credit_note\",\"fieldtype\":\"Currency\",\"options\":\"currency\",\"width\":120,\"id\":\"credit_note\",\"name\":\"Nota de cr\u00e9dito\",\"editable\":false,\"compareValue\":null},{\"label\":\"Monto pendiente\",\"fieldname\":\"outstanding\",\"fieldtype\":\"Currency\",\"options\":\"currency\",\"width\":120,\"id\":\"outstanding\",\"name\":\"Monto pendiente\",\"editable\":false,\"compareValue\":null},{\"label\":\"Centro de costos\",\"fieldname\":\"cost_center\",\"fieldtype\":\"Data\",\"options\":null,\"width\":120,\"id\":\"cost_center\",\"name\":\"Centro de costos\",\"editable\":false,\"compareValue\":null},{\"label\":\"Tipo de Comprobante\",\"fieldname\":\"voucher_type\",\"fieldtype\":\"Data\",\"options\":null,\"width\":120,\"id\":\"voucher_type\",\"name\":\"Tipo de Comprobante\",\"editable\":false,\"compareValue\":null},{\"label\":\"Contacto del Cliente\",\"fieldname\":\"customer_primary_contact\",\"fieldtype\":\"Link\",\"options\":\"Contact\",\"width\":120,\"id\":\"customer_primary_contact\",\"name\":\"Contacto del Cliente\",\"editable\":false,\"compareValue\":null},{\"label\":\"Cliente\",\"fieldname\":\"party\",\"fieldtype\":\"Link\",\"options\":\"Customer\",\"width\":180,\"id\":\"party\",\"name\":\"Cliente\",\"editable\":false,\"compareValue\":null},{\"label\":\"D\u00edas de Vencimiento\",\"fieldname\":\"age\",\"fieldtype\":\"Int\",\"options\":null,\"width\":80,\"id\":\"age\",\"name\":\"D\u00edas de Vencimiento\",\"editable\":false,\"compareValue\":null},{\"label\":\"0-30\",\"fieldname\":\"range1\",\"fieldtype\":\"Currency\",\"options\":\"currency\",\"width\":120,\"id\":\"range1\",\"name\":\"0-30\",\"editable\":false,\"compareValue\":null},{\"label\":\"31-60\",\"fieldname\":\"range2\",\"fieldtype\":\"Currency\",\"options\":\"currency\",\"width\":120,\"id\":\"range2\",\"name\":\"31-60\",\"editable\":false,\"compareValue\":null},{\"label\":\"61-90\",\"fieldname\":\"range3\",\"fieldtype\":\"Currency\",\"options\":\"currency\",\"width\":120,\"id\":\"range3\",\"name\":\"61-90\",\"editable\":false,\"compareValue\":null},{\"label\":\"91-120\",\"fieldname\":\"range4\",\"fieldtype\":\"Currency\",\"options\":\"currency\",\"width\":120,\"id\":\"range4\",\"name\":\"91-120\",\"editable\":false,\"compareValue\":null},{\"label\":\"121-Arriba\",\"fieldname\":\"range5\",\"fieldtype\":\"Currency\",\"options\":\"currency\",\"width\":120,\"id\":\"range5\",\"name\":\"121-Arriba\",\"editable\":false,\"compareValue\":null},{\"label\":\"Divisa / Moneda\",\"fieldname\":\"currency\",\"fieldtype\":\"Link\",\"options\":\"Currency\",\"width\":80,\"id\":\"currency\",\"name\":\"Divisa / Moneda\",\"editable\":false,\"compareValue\":null},{\"label\":\"Cliente LPO\",\"fieldname\":\"po_no\",\"fieldtype\":\"Data\",\"options\":null,\"width\":120,\"id\":\"po_no\",\"name\":\"Cliente LPO\",\"editable\":false,\"compareValue\":null},{\"label\":\"Territorio o Sector\",\"fieldname\":\"territory\",\"fieldtype\":\"Link\",\"options\":\"Territory\",\"width\":120,\"id\":\"territory\",\"name\":\"Territorio o Sector\",\"editable\":false,\"compareValue\":null},{\"label\":\"Categor\u00eda de Cliente\",\"fieldname\":\"customer_group\",\"fieldtype\":\"Link\",\"options\":\"Customer Group\",\"width\":120,\"id\":\"customer_group\",\"name\":\"Categor\u00eda de Cliente\",\"editable\":false,\"compareValue\":null}]}",
 
frappe.query_reports["CxC Cobranza"] = {
	"treeView": true,
	"name_field": "name",
	"parent_field": "name",
	"initial_depth": 1,			//The level to which the initial rendering will expand to
	
	onload: function(report) {
		// dropdown for links to other financial statements
		//erpnext.financial_statements.filters = get_filters()

		//let fiscal_year = frappe.defaults.get_user_default("fiscal_year")
		/*
		frappe.model.with_doc("Fiscal Year", fiscal_year, function(r) {
			var fy = frappe.model.get_doc("Fiscal Year", fiscal_year);
			frappe.query_report.set_filter_value({
				period_start_date: fy.year_start_date,
				period_end_date: fy.year_end_date
			});
		});
		*/
		//console.log(report.get_values());
		report.page.add_inner_button(__('Enviar Correos'), () => {
			//console.log(report.get_values());
		  let filtros = report.get_values();
		  console.log(filtros);
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
		
	},
	

	"filters": [
		{
			fieldname: "company",
			label: "Empresa",
			fieldtype: "Link",
			reqd: 1,
			options: 'Company'
			//default: (frappe.user.has_role("Administrator") || frappe.user.has_role("System Manager")) ? "" : frappe.user.name,
			
		},
		{
			fieldname: "report_date",
			label: "Fecha de contabilizacion",
			fieldtype: "Date",
			reqd: 1
			//default: (frappe.user.has_role("Administrator") || frappe.user.has_role("System Manager")) ? "" : frappe.user.name,
			
		},
		{
			fieldname: "customer",
			label: "Cliente",
			fieldtype: "Link",
			options: 'Customer'
			//default: (frappe.user.has_role("Administrator") || frappe.user.has_role("System Manager")) ? "" : frappe.user.name,
			
		},
		{
			fieldname: "territory",
			label: "Sector",
			fieldtype: "Link",
			options: 'Territory'
			//default: (frappe.user.has_role("Administrator") || frappe.user.has_role("System Manager")) ? "" : frappe.user.name,
			
		},
		{
			fieldname: "group_by_party",
			label: "Agrupar por Cliente",
			fieldtype: "Check"
			//default: (frappe.user.has_role("Administrator") || frappe.user.has_role("System Manager")) ? "" : frappe.user.name,
			
		}

		
	]
};

function EnviarCorreos(filtros){
	console.log(filtros);
}