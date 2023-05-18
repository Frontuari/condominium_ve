window.open_url_post = function open_url_post(URL, PARAMS, new_window) {
	if (window.cordova) {
		let url = URL + 'api/method/' + PARAMS.cmd + frappe.utils.make_query_string(PARAMS, false);
		window.location.href = url;
	} else {
		// call a url as POST
		var temp=document.createElement("form");
		temp.action=URL;
		temp.method="POST";
		temp.style.display="none";
		if(new_window){
			temp.target = '_blank';
		}
		PARAMS["csrf_token"] = frappe.csrf_token;
		for(var x in PARAMS) {
			var opt=document.createElement("textarea");
			opt.name=x;
			var val = PARAMS[x];
			if(typeof val!='string')
				val = JSON.stringify(val);
			opt.value=val;
			temp.appendChild(opt);
		}
		document.body.appendChild(temp);
		temp.submit();
		return temp;
	}
};



frappe.ready(function(){frappe.web_form.after_load = () => {
	frappe.web_form.set_value("customer", '')
	frappe.web_form.set_value("posting_date", frappe.datetime.now_date())
	let params = get_params_url()

	console.log(params)
	console.log("consultas 3")

	if(params['code']){

		frappe.web_form.set_value("buscar", params['code']);
		frappe.web_form.doc['buscar'] = frappe.web_form.get_value('buscar')
		frappe.web_form.refresh()
		//searchCustomer('code', params['code']);
	}


	// document.querySelector('button.btn:nth-child(4)').remove()
	if(document.querySelector('a.text-muted'))
		document.querySelector('a.text-muted').remove();


	document.querySelector('.footer-logo-extension').remove()
	document.querySelector("button.btn:nth-child(4)").remove()
	document.querySelector("button.btn-xs:nth-child(1)").remove()
	document.querySelector('.grid-row-check').remove()

	frappe.web_form.on('buscar', (field, value) => {
		searchCustomer(field , value)
	});

	frappe.web_form.the_callback = function () {
		window.location.href = frappe.web_form.success_url
	}

	function url_sales_invoice(name) {
		return `/printview?doctype=Sales%20Invoice&name=${name}&format=Recibo%20de%20Condominio&no_letterhead=0&letterhead=Casa%20de%20Campo&settings=%7B%7D&_lang=es-VE`
		// return `/printview?doctype=Sales%Invoice&name=${name}&format=Standard&no_letterhead=0&letterhead=Casa%20de%20Campo&settings=%7B%7D&_lang=es-VE`;
	}

	function print(name) {

		window.open(url_sales_invoice(name), '_blank');

		/*let args = {}
		args["name"] = name;
		args["doctype"] = "Sales Invoice";
		args["format"] = "Recibo de Condominio";
		args["no_letterhead"] = "0";
		args["letterhead"] = "Casa de Campo";
		args["settings"] = "%7B%7D";
		args["_lang"] = "es-VE";

		open_url_post(
			"/api/method/frappe.utils.print_format.download_pdf/",
			args,
			true
		);*/

	}


	function get_params_url(url) {

		// get query string from url (optional) or window
		var queryString = url ? url.split('?')[1] : window.location.search.slice(1);

		// we'll store the parameters here
		var obj = {};

		// if query string exists
		if (queryString) {

		  // stuff after # is not part of query string, so get rid of it
		  queryString = queryString.split('#')[0];

		  // split our query string into its component parts
		  var arr = queryString.split('&');

		  for (var i = 0; i < arr.length; i++) {
			// separate the keys and the values
			var a = arr[i].split('=');

			// set parameter name and value (use 'true' if empty)
			var paramName = a[0];
			var paramValue = typeof (a[1]) === 'undefined' ? true : a[1];

			// (optional) keep case consistent
			paramName = paramName.toLowerCase();
			if (typeof paramValue === 'string') paramValue = paramValue.toLowerCase();

			// if the paramName ends with square brackets, e.g. colors[] or colors[2]
			if (paramName.match(/\[(\d+)?\]$/)) {

			  // create key if it doesn't exist
			  var key = paramName.replace(/\[(\d+)?\]/, '');
			  if (!obj[key]) obj[key] = [];

			  // if it's an indexed array e.g. colors[2]
			  if (paramName.match(/\[\d+\]$/)) {
				// get the index value and add the entry at the appropriate position
				var index = /\[(\d+)\]/.exec(paramName)[1];
				obj[key][index] = paramValue;
			  } else {
				// otherwise add the value to the end of the array
				obj[key].push(paramValue);
			  }
			} else {
			  // we're dealing with a string
			  if (!obj[paramName]) {
				// if it doesn't exist, create property
				obj[paramName] = paramValue;
			  } else if (obj[paramName] && typeof obj[paramName] === 'string'){
				// if property does exist and it's a string, convert it to an array
				obj[paramName] = [obj[paramName]];
				obj[paramName].push(paramValue);
			  } else {
				// otherwise add the property
				obj[paramName].push(paramValue);
			  }
			}
		  }
		}

		return obj;
	}


	  function clearTable(){

			if (frappe.web_form.doc['invoices']) {

				let len = frappe.web_form.doc['invoices'].length

				for (let i = 0; i <= len; i++) {
					if(frappe.web_form.doc['invoices']){
						frappe.web_form.doc['invoices'].pop()
						frappe.web_form.refresh()
					}
				}

			}

	  }


	  function unique_sales_invoice(arr){

			let uniqueIds = []

			const unique = arr.filter(element => {
				const isDuplicate = uniqueIds.includes(element.name);

					if (!isDuplicate && !element.owner) {
						uniqueIds.push(element.name);

						return true;
					}

					return false;
				});

				return unique

	  }

	  function searchCustomer(field , value){

			clearTable();
			clearTable();


			if (value.length > 8) {

				clearTable()
				clearTable()

				frappe.call({
					method: "condominium_ve.api.query_code_housing",
					args: {
						code: value
					},
					callback: (response) => {
						let data = response.data

						frappe.web_form.set_value("customer", data.customer[0]);
						frappe.web_form.set_value("balance", data.saldo);
						frappe.web_form.set_value("credit", data.credito);
						frappe.web_form.set_value("debit_balance", data.credito+data.saldo);



						data.invoices.forEach(e => {

								if(!e.label){

									let me = frappe.web_form;
									let field = me.get_field('invoices');
									let row = field.grid.add_new_row(null, null, true);

									grid_rows = field.grid.grid_rows;

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
									if(document.querySelector('.grid-row-check'))
										document.querySelector('.grid-row-check').remove()
									if(document.querySelector('.grid-row-check'))
										document.querySelector('.grid-row-check').remove()


									if($("div.grid-row:nth-child(3) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > span:nth-child(2) > button:nth-child(1)"))
										$("div.grid-row:nth-child(3) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > span:nth-child(2) > button:nth-child(1)").trigger('click');

									$("#descargar").click(() => {
									
										if(!frappe.web_form.doc['invoices']) return ;

										frappe.web_form.doc['invoices'].forEach(si =>{
											print(si.invoice)
										})
										
									})


								}
							})
						frappe.web_form.doc['invoices'] = unique_sales_invoice(frappe.web_form.doc['invoices'])
						$("select[data-fieldname='mode_of_payment']").val('Transferencia Bancaria')

						//$('div[data-fieldname="invoice"]').click(e =>{  
						//	if(e.target.innerText != "Factura" && e.target.innerText != 'Factura`' )
						//		print(e.target.innerText);  
						//
						//})
					},
					error: (r) => {
						console.log(r)
					},
				});

			}

	  }

}})