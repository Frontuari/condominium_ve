# Copyright (c) 2023, Armando Rojas and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.pdf import get_pdf
from frappe import _
from frappe.core.doctype.communication import email
import json
import os

def execute(filters=None):
	return get_columns(), get_data(filters)

def get_columns():
	return [
		{
			'fieldname': 'posting_date',
			'label': _('Fecha'),
			'fieldtype': 'Date',
			'width':100
		},
		{
			'fieldname': 'due_date',
			'label': _('Fecha de Vencimiento'),
			'fieldtype': 'Date',
			'width':150
		},
		{
			'fieldname': 'customer',
			'label': _('Cliente'),
			'fieldtype': 'Data',
			'width':150
		},

		{
			'fieldname': 'name',
			'label': _('Comprobante'),
			'fieldtype': 'Link',
			'options':'Sales Invoice',
			'width':200
		},
		{
			'fieldname': 'grand_total',
			'label': _('Cantidad Facturada'),
			'fieldtype': 'Currency',
			'width':150
		},
		{
			'fieldname': 'cantidad_pagada',
			'label': _('Cantidad Pagada'),
			'fieldtype': 'Currency',
			'width':150
		},
		{
			'fieldname': 'outstanding_amount',
			'label': _('Cantidad Pendiente'),
			'fieldtype': 'Currency',
			'width':150
		}
	]

def get_data(filters):
	agrupar_por_cliente = False
	if filters['group_by_party']:
		agrupar_por_cliente = True
		del filters['group_by_party']
		
	del filters['report_date'], filters['ageing_based_on'], filters['range1'], filters['range2'], filters['range3'], filters['range4']

	invoices = frappe.db.get_all('Sales Invoice', filters=filters, fields=['posting_date', 'due_date', 'customer', 'name', 'grand_total', 'outstanding_amount'])
	
	
	ventas = []
	for invoice in invoices[::-1]:
		cantidad_pagada = invoice.grand_total - invoice.outstanding_amount
		ventas.append({
				"posting_date": invoice.posting_date,
				"due_date": invoice.due_date,
				"customer": invoice.customer,
				"name": invoice.name,
				"grand_total": invoice.grand_total,
				"cantidad_pagada":cantidad_pagada,
				"outstanding_amount": invoice.outstanding_amount
			})
	
	return ventas	


@frappe.whitelist()
def send_email(filters):
	data = get_data(json.loads(filters))
	
	data_clientes = {}
	for d in data:
		customer = d['customer']
		#'posting_date', 'due_date', 'customer', 'name', 'grand_total', 'outstanding_amount'
		if not customer in data_clientes:
			data_clientes[customer] = []

		del d['customer']
		data_clientes[customer].append(d)
	
	frappe.publish_realtime(
        'msgprint', 'Inicio de proceso de envio de correos')
	for customer in data_clientes:
		send_email_queue(customer, data_clientes[customer])
		#frappe.enqueue(
        #    'condominium_ve.condominium_ve.report.cxc_cobranza.cxc_cobranza.send_email_queue', customer=customer, data_clientes=data_clientes[customer])

def send_email_queue(customer, data_clientes):
	total = {'grand_total':0, 'cantidad_pagada':0, 'outstanding_amount':0}
	for i in range(len(data_clientes)):
		total['grand_total'] += data_clientes[i]['grand_total']
		total['cantidad_pagada'] += data_clientes[i]['cantidad_pagada']
		total['outstanding_amount'] += data_clientes[i]['outstanding_amount']

	pdf = generate_pdf(data=data_clientes, customer=customer, total=total)
		
	email = frappe.db.get_all('Sales Invoice', filters={'customer':customer}, fields=['contact_email'])
	email_to = email[0]['contact_email']

	new_attachments = []
	ret = frappe.get_doc({
        "doctype": "File",
        "folder": "Home",
        "file_name": "estado_de_cuenta_"+customer+".pdf",
        "is_private": 1,
        "content": pdf,
	})
	ret.save(ignore_permissions=True)
	new_attachments.append(create_attachment(ret.name))#{"file_url":frappe.get_site_path(ret.file_url)})

	style = '*{font-family:Sans-Serif;}'
	description = f'<style>{style}</style><p>Propietario <strong>{customer}</strong>,</p> <p>Adjuntamos al siguiente correo su estado de cuenta</p>'
	send_email_condo([email_to], customer, description, new_attachments)


def generate_pdf(data, customer, total):
	cart = data

	html = '<h4>Estimado Propietario, '+customer+', Su estado de cuenta.</h4>'

    # Add items to PDF HTML
	html += '<style>*{font-family:Sans-Serif;} th, td{border: 1px solid black;}</style>\
			<table style="border: 1px solid black; border-collapse: collapse; width: 100%;"> \
  			<thead style="background-color: #CCC; text-align: center; box-shadow: 0px 2px 2px #888888;">\
    			<tr>\
			      <th scope="col">'+_('Fecha de Contabilizacion')+'</th>\
			      <th scope="col">'+_('Fecha de Vencimiento')+'</th>\
			      <th scope="col">'+_('Comprobante')+'</th>\
			      <th scope="col">'+_('Cantidad Facturada')+'</th>\
			      <th scope="col">'+_('Cantidad Pagada')+'</th>\
			      <th scope="col">'+_('Cantidad Pendiente')+'</th>\
			    </tr>\
  			</thead>\
  			<tbody style="border: 1px solid black; text-align: center;">'
    
  

	for row in cart:
		html += '<tr>\
			      <td class="text-center">'+row['posting_date'].strftime('%d-%m-%Y')+'</td>\
			      <td class="text-center">'+row['due_date'].strftime('%d-%m-%Y')+'</td>\
			      <td class="text-center">'+row['name']+'</td>\
			      <td class="text-center">'+frappe.format(row['grand_total'], {'fieldtype': 'Currency'})+'</td>\
			      <td class="text-center">'+frappe.format(row['cantidad_pagada'], {'fieldtype': 'Currency'})+'</td>\
			      <td class="text-center">'+frappe.format(row['outstanding_amount'], {'fieldtype': 'Currency'})+'</td>\
			    </tr>'

	html += '<tr>\
			      <td></td>\
			      <td></td>\
			      <td class="text-center"><b>'+_('TOTAL')+'</b></td>\
			      <td class="text-center"><b>'+frappe.format(total['grand_total'], {'fieldtype': 'Currency'})+'</b></td>\
			      <td class="text-center"><b>'+frappe.format(total['cantidad_pagada'], {'fieldtype': 'Currency'})+'</b></td>\
			      <td class="text-center"><b>'+frappe.format(total['outstanding_amount'], {'fieldtype': 'Currency'})+'</b></td>\
			    </tr>'
	html += '</tbody>\
			</table>'

    # Attaching PDF to response
	return get_pdf(html)
	

def send_email_condo(emails, name, description="", attachments=[]):
	return frappe.sendmail(
		recipients=emails,
		subject="Estado de cuenta condominio: " + name,
		message="<div class='ql-editor read-mode'> {0} <p><br></p></div>".format(description),
		attachments=attachments)

def create_attachment(filename):
	root_directory = frappe.db.get_value('Environment Variables', 'ROOT_DIRECTORY', 'value')
	file = frappe.get_doc("File",filename)
	path = root_directory+'/'+frappe.get_site_path(file.file_url)  

	with open(path, "rb") as fileobj:
		filedata = fileobj.read() 

	out = {
		"fname": file.file_name,
		"fcontent": filedata
	}
	return out 