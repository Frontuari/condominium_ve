// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

frappe.ready(function () {

	if (frappe.utils.get_url_arg('subject')) {
		$('[name="subject"]').val(frappe.utils.get_url_arg('subject'));
	}

	$('#consultar').off("click").on("click", function () {
		frappe.call({
			method: "condominium_ve.api.query_code",
			args: {
				code: $('[name="code"]').val(),
			},

			btn: $(".primary-action"),

			freeze: true,
			callback: (response) => {
				console.log(response)
			},
			error: (r) => {
				console.log(r)
			},
		});

	})



});

var msgprint = function (txt) {
	if (txt) $("#contact-alert").html(txt).toggle(true);
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

