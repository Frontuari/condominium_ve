# Copyright (c) 2023, Armando Rojas and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from datetime import date, datetime

meses = [
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
]

def execute(filters=None):
	

	

	return get_columns(), get_data(filters)

def get_data(filters):
	periodo =  meses.index(filters.period.strip())
	year = date.today().year

	sql = """
		SELECT 
			tc.territory, tc.name as customer, COUNT(tsi.name) as total_facturas
			FROM `tabSales Invoice` tsi 
			JOIN tabCustomer tc ON tc.name = tsi.customer
			WHERE MONTH(tsi.posting_date) = {0} AND YEAR(tsi.posting_date) = {1}

			GROUP BY tc.name, tc.territory
		
		ORDER BY tc.territory ASC
		
	""".format(periodo, year)
	result = frappe.db.sql(sql, as_dict=True)

	territorios = []
	data = []
	for row in result:
		if row.territory not in territorios:
			territorios.append(row.territory)
			data.append({'customer': '<b>'+row.territory+'</b>', 'total_facturas': ''})
		else:
			data.append({'customer': row.customer,
				'total_facturas': frappe.format(row.total_facturas, {'fieldtype':'Int'})})
	return data
      

def get_columns():
    return [
        {
			"fieldname":"customer",
			"label": _("Propietario"),
			"fieldtype": "Link",
			'options': 'Customer',
			'width': 400
		},
		{
			"fieldname":"total_facturas",
			"label": _("Nro. Facturas"),
			"fieldtype": "Data"
		}

    ]