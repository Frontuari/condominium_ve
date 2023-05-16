alert()

frappe.init_client_script = () => {
    try {
        frappe.web_form.set_value("customer", '')

        // document.querySelector('button.btn:nth-child(4)').remove()
        document.querySelector('a.text-muted').remove()
        document.querySelector('.footer-logo-extension').remove()
        document.querySelector("button.btn:nth-child(4)").remove()
        document.querySelector("button.btn-xs:nth-child(1)").remove()
        document.querySelector('.grid-row-check').remove()

        frappe.web_form.on('buscar', (field, value) => {
            if (value.length > 8) {

                frappe.call({
                    method: "condominium_ve.api.query_code_housing",
                    args: {
                        code: value
                    },
                    callback: (response) => {
                        let data = response.data

                        frappe.web_form.set_value("customer", data.customer[0])
                        frappe.web_form.set_value("balance", data.saldo)

                        if (frappe.web_form.doc['invoices']) {


                            for (let i = 0; i <= frappe.web_form.doc['invoices'].length + 1; i++) {


                                console.log("borrar")

                                frappe.web_form.doc['invoices'].pop()
                                frappe.web_form.refresh()
                            }


                        }


                        data.invoices.forEach(e => {

                            console.log(e)

                            let me = frappe.web_form;
                            let field = me.get_field('invoices');
                            let row = field.grid.add_new_row(null, null, true)

                            grid_rows = field.grid.grid_rows

                            row_name = grid_rows[grid_rows.length - 1].doc.name;

                            frappe.model.set_value(field.grid.doctype, row_name, "posting_date", "2022-01-01");


                            row_number = (grid_rows.length - 1)

                            frappe.web_form.doc['invoices'] = frappe.web_form.get_value('invoices')

                            frappe.web_form.doc['invoices'][row_number].posting_date = e.posting_date
                            frappe.web_form.doc['invoices'][row_number].invoice = `${e.name}`
                            frappe.web_form.doc['invoices'][row_number].btn = `<a href='${url_sales_invoice(e.name)}' > ${e.name} </a>`
                            frappe.web_form.doc['invoices'][row_number].total = e.grand_total


                            frappe.web_form.doc['invoices'][row_number].balance = e.outstanding_amount

                            if (document.querySelector('.btn-open-row'))
                                document.querySelector('.btn-open-row').remove();




                            frappe.web_form.refresh()
                            document.querySelector('.grid-row-check').remove()
                            document.querySelector('.grid-row-check').remove()

                            $("#descargar").click(() => {

                                alert()

                            })

                        })
                    },
                    error: (r) => {
                        console.log(r)
                    },
                });

            }
        });

        frappe.web_form.the_callback = function () {
            window.location.href = frappe.web_form.success_url
        }



        function url_sales_invoice(name) {


            return `/printview?doctype=Sales%20Invoice&name=${name}&format=Recibo%20de%20Condominio&no_letterhead=0&letterhead=Casa%20de%20Campo&settings=%7B%7D&_lang=es-VE`
            // return `/printview?doctype=Sales%Invoice&name=${name}&format=Standard&no_letterhead=0&letterhead=Casa%20de%20Campo&settings=%7B%7D&_lang=es-VE`;
        }

        function print(name) {

            let args = {}
            args["name"] = name;
            open_url_post(
                "/printview",
                args,
                true
            );

        }






    } catch (e) {
        console.error('Error in web form client script');
        console.error(e);
    }
}



frappe.ready(function () {
    // bind events here
})

