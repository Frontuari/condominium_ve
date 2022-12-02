// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

frappe.ready(function () {
  if (frappe.utils.get_url_arg("subject")) {
    $('[name="subject"]').val(frappe.utils.get_url_arg("subject"));
  }

  $("#consultar")
    .off("click")
    .on("click", function () {
      frappe.call({
        method: "condominium_ve.api.query_code",
        args: {
          code: $('[name="code"]').val(),
        },

        btn: $(".primary-action"),

        freeze: true,
        callback: (response) => {
          let data = response.data;
          $("#condo").html("");
          $("#payments").html("");

          data.cc_condo.forEach((e) => {
            $("#condo").append(
              `<li> <a target="_blank" href='${url_condo(
                e.name
              )}' >  Gasto Comun de Condominio No. ${e.name}, fecha: ${
                e.posting_date
              }, total: ${e.total} </a>  </li>`
            );
          });

          data.payments.forEach((e) => {
            $("#payments").append(
              `<li> <a target="_blank" href='${url_payment(
                e.name
              )}' >  Pago confirmado No. ${e.name}, fecha: ${
                e.posting_date
              }, total: ${e.received_amount} </a>  </li>`
            );
          });

          $("#balance").val(data.balance[0][0]);
        },
        error: (r) => {
          console.log(r);
        },
      });
    });
});

var msgprint = function (txt) {
  if (txt) $("#contact-alert").html(txt).toggle(true);
};

function url_condo(name) {
  return `/api/method/condominium_ve.api.pdf_2?report_name=Prueba%20Gastos%20Comunes%20de%20Condominio%20copia%202&doctype=Condominium Common Expenses&name=${name}`;
}

function url_payment(name) {
  return `/printview?doctype=Payment%20Entry&name=${name}&format=Recibo%20de%20Cobranza&no_letterhead=0&letterhead=Casa%20de%20Campo&settings=%7B%7D&_lang=es-VE`;
}
/*


frappe.ui.form.on("Consultas", {
	refresh(frm) {
		frm.set_query('link_doctype', "links", function() {
			return {
				query: "frappe.contacts.address_and_contact.filter_dynamic_link_doctypes",
				filters: {
					fieldtype: ["in", ["HTML", "Text Editor"]],
					fieldname: ["in", ["contact_html", "company_description"]],
				}
			};
		});
		frm.refresh_field("links");
	}
});*/
