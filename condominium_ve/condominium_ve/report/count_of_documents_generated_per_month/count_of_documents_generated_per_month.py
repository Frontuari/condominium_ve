# Copyright (c) 2023, Armando Rojas and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import datetime

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
	periodo =  meses.index(filters.period.strip())+1
	year = datetime.date.today().year
	
	response = frappe.db.get_all('Sales Invoice', filters={'docstatus':1}, fields=['posting_date', 'customer'])
	
	count = {}
	for res in response:
		if res.posting_date.month == periodo and res.posting_date.year == year:
			if res.customer not in count:
				count[res.customer] = 0
			count[res.customer] += 1
	
	data_aux = {}
	response = frappe.db.get_all('Customer', fields=['name', 'territory'])
	for res in response:
		if res.name in count:
			if res.territory not in data_aux:
				data_aux[res.territory] = []
				data_aux[res.territory].append({
       				'customer': '<b>'+res.territory+'</b>', 
           			'total_facturas':''})
    
			data_aux[res.territory].append({
       				'customer': res.name, 
           			'total_facturas': frappe.format(count[res.name], {'fieldtype':'Int'})})
	
	data = []
	for d in data_aux:
		data += data_aux[d]
	
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