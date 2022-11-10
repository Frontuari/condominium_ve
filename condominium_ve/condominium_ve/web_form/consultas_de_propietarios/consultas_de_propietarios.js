frappe.provide("frappe.ui");
frappe.provide("frappe.web_form");

frappe.ready(function () {

	if (frappe.utils.get_url_arg('subject')) {
		$('[name="subject"]').val(frappe.utils.get_url_arg('subject'));
	}

	$('#consultar').off("click").on("click", function () {
		alert()
	})

	$(document).ready(function () {
		setTimeout(() => {
			$(".web-form-actions").html("")
			$(".web-form-footer").html("")

			frappe.web_form.doc.condominium_receipt = []


			$('#consultar').off("click").on("click", function () {

				frappe.call({
					method: "condominium_ve.www.consultas.query_code",
					args: {
						code: frappe.web_form.get_field('code').value,
					},

					btn: $(".primary-action"),

					freeze: true,
					callback: (response) => {
						let data = response.data
						console.log(frappe.web_form.doc)
						console.log(this)
						console.log(data.customer.customer_name)
						$(".customer-name").html(data.customer.customer_name)
						$(".customer-name").css("display", "")
						let indice = 0

						data.sales_invoices.forEach(sales_invoice => {
							indice++; 
							frappe.web_form.doc.condominium_receipt.push({
								posting_date: sales_invoice.posting_date,
								voucher: sales_invoice.name ,
								name: `row ${indice}` ,
								idx: indice 
							});
							
							
						})

						
						



					},
					error: (r) => {
						console.log(r)
					},
				});

			})



		}, 500)

	})

	$('.btn-send').off("click").on("click", function () {
		var email = $('[name="email"]').val();
		var message = $('[name="message"]').val();

		if (!(email && message)) {
			frappe.msgprint('{{ _("Please enter both your email and message so that we can get back to you. Thanks!") }}');
			return false;
		}

		if (!validate_email(email)) {
			frappe.msgprint('{{ _("You seem to have written your name instead of your email. Please enter a valid email address so that we can get back.") }}');
			$('[name="email"]').focus();
			return false;
		}

		$("#contact-alert").toggle(false);
		frappe.send_message({
			subject: $('[name="subject"]').val(),
			sender: email,
			message: message,
			callback: function (r) {
				if (r.message === "okay") {
					frappe.msgprint('{{ _("Thank you for your message") }}');
				} else {
					frappe.msgprint('{{ _("There were errors") }}');
					console.log(r.exc);
				}
				$(':input').val('');
			}
		}, this);
		return false;
	});

});

var msgprint = function (txt) {
	if (txt) $("#contact-alert").html(txt).toggle(true);
}





