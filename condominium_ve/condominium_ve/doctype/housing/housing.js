// Copyright (c) 2022, Armando Rojas and contributors
// For license information, please see license.txt

frappe.ui.form.on('Housing', {
	refresh: function (frm) {
		frm.add_custom_button(__('Generate Code'), () => {
			frappe.call({
				method: "condominium_ve.condominium_ve.doctype.housing.housing.generate_code",
				btn: $(".primary-action"),
				freeze: true,
				callback: (response) => {
					let data = response.data;
					console.log(data)
					frm.set_value('code', data.code)
					frm.refresh_fields();
				},
				error: (r) => {
					console.log(r)
				},
			});
		});
	}
});
