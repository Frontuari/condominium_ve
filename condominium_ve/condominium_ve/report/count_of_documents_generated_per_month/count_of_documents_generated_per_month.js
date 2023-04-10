// Copyright (c) 2023, Armando Rojas and contributors
// For license information, please see license.txt
/* eslint-disable */
const meses = [
	'Enero',
	'Febrero',
	'Marzo',
	'Abril',
	'Mayo',
	'Junio',
	'Julio',
	'Agosto',
	'Septiembre',
	'Octubre',
	'Noviembre',
	'Diciembre'
  ];
  
const fechaActual = new Date();
const mesActual = meses[fechaActual.getMonth()];

frappe.query_reports["Count of Documents Generated Per Month"] = {
	"filters": [
		{
			"fieldname":"period",
			"label": __("Periodo"),
			"fieldtype": "Select",
			"options": `Enero
					Febrero
					Marzo
					Abril
					Mayo
					Junio
					Julio
					Agosto
					Septiembre
					Octubre
					Noviembre
					Diciembre`,
			"reqd": 1
		}
	],


};
