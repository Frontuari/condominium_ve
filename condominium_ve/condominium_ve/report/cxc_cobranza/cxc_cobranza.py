# Copyright (c) 2023, Armando Rojas and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.pdf import get_pdf
from frappe import _
from frappe.core.doctype.communication import email
from frappe.utils import date_diff
from custom_ve.custom_ve.doctype.environment_variables.environment_variables import get_env
import json
import os
import datetime

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
			'label': _('Dias Vencido'),
			'fieldtype': 'Data',
			'width':100
		},
		{
			'fieldname': 'customer',
			'label': _('Cliente'),
			'fieldtype': 'Link',
			'options': 'Customer',
			'width':150
		},

		{
			'fieldname': 'name',
			'label': _('Comprobante'),
			'fieldtype': 'Link',
			'options':'Sales Invoice',
			'width':150
		},
		{
			'fieldname': 'grand_total',
			'label': _('Cantidad Facturada'),
			'fieldtype': 'Data',
			'width':150
		},
		{
			'fieldname': 'cantidad_pagada',
			'label': _('Cantidad Pagada'),
			'fieldtype': 'Data',
			'width':150
		},
		{
			'fieldname': 'outstanding_amount',
			'label': _('Cantidad Pendiente'),
			'fieldtype': 'Data',
			'width':150
		},
		{
			'fieldname': 'territory',
			'label': _('Sector'),
			'fieldtype': 'Data',
			'width':150
		}
	]

def get_data(filters):
	agrupar_por_cliente = False
	try:
		if filters['group_by_party']:
			agrupar_por_cliente = True
			del filters['group_by_party']
	except:
		pass

	filters = delFilters(filters,['group_by_party','report_date','ageing_based_on','range1','range2','range3','range4'])

	invoices = frappe.db.get_all('Sales Invoice', filters=filters, fields=['posting_date', 'due_date', 'customer', 'name', 'grand_total', 'outstanding_amount', 'territory'])
	
	
	ventas = []

	if not agrupar_por_cliente:
		total_facturado = 0
		total_pagado = 0
		total_pendiente = 0

		for invoice in invoices[::-1]:
			cantidad_pagada = invoice.grand_total - invoice.outstanding_amount
			
			total_facturado += invoice.grand_total
			total_pagado += cantidad_pagada
			total_pendiente += invoice.outstanding_amount
			
			dias_vencido = datetime.date.today() - invoice.due_date
			ventas.append({
					"posting_date": invoice.posting_date,
					"due_date": dias_vencido.days,
					"customer": invoice.customer,
					"name": invoice.name,
					"grand_total": frappe.format(invoice.grand_total, {'fieldtype': 'Currency'}),
					"cantidad_pagada":frappe.format(cantidad_pagada, {'fieldtype': 'Currency'}),
					"outstanding_amount": frappe.format(invoice.outstanding_amount, {'fieldtype': 'Currency'}),
					"territory": invoice.territory
				})

		ventas.append({
					"posting_date": "",
					"due_date": "",
					"customer": "",
					"name": '<b>'+_('Total')+'</b>',
					"grand_total": '<b>'+frappe.format(total_facturado, {'fieldtype': 'Currency'})+'</b>',
					"cantidad_pagada": '<b>'+frappe.format(total_pagado, {'fieldtype': 'Currency'})+'</b>',
					"outstanding_amount": '<b>'+frappe.format(total_pendiente, {'fieldtype': 'Currency'})+'</b>',
					"territory": ""
				})
	else:
		total_facturado = 0
		total_pagado = 0
		total_pendiente = 0

		invoice_clientes = {}
		total_clientes = {}
		for invoice in invoices[::-1]:
			cantidad_pagada = invoice.grand_total - invoice.outstanding_amount
			
			total_facturado += invoice.grand_total
			total_pagado += cantidad_pagada
			total_pendiente += invoice.outstanding_amount

			if not invoice.customer in invoice_clientes:
				invoice_clientes[invoice.customer] = []
				total_clientes[invoice.customer] = {'grand_total': "", 'cantidad_pagada': "", 'outstanding_amount': 0}

			dias_vencido = datetime.date.today() - invoice.due_date
			invoice_clientes[invoice.customer].append({
					"posting_date": invoice.posting_date,
					"due_date": dias_vencido,
					"customer": invoice.customer,
					"name": invoice.name,
					"grand_total": frappe.format(invoice.grand_total, {'fieldtype': 'Currency'}),
					"cantidad_pagada":frappe.format(cantidad_pagada, {'fieldtype': 'Currency'}),
					"outstanding_amount": frappe.format(invoice.outstanding_amount, {'fieldtype': 'Currency'}),
					"territory": invoice.territory
				})

			#total_clientes[invoice.customer]['grand_total'] += invoice.grand_total
			#total_clientes[invoice.customer]['cantidad_pagada'] += cantidad_pagada
			total_clientes[invoice.customer]['outstanding_amount'] += invoice.outstanding_amount

		# saco el total por cliente y lo agrego a la lista de ventas
		for cliente in invoice_clientes:
			for invoice in invoice_clientes[cliente]:
				ventas.append(invoice)

			ventas.append({
					"posting_date": "",
					"due_date": "",
					"customer": "",
					"name": '<b>'+_('Total')+'</b>',
					"grand_total": '<b>'+frappe.format(total_clientes[cliente]['grand_total'], {'fieldtype': 'Currency'})+'</b>',
					"cantidad_pagada": '<b>'+frappe.format(total_clientes[cliente]['cantidad_pagada'], {'fieldtype': 'Currency'})+'</b>',
					"outstanding_amount": '<b>'+frappe.format(total_clientes[cliente]['outstanding_amount'], {'fieldtype': 'Currency'})+'</b>',
					"territory": ""
				})


		ventas.append({
					"posting_date": "",
					"due_date": "",
					"customer": "",
					"name": '<b>'+_('Total General')+'</b>',
					"grand_total": '<b>'+frappe.format(total_facturado, {'fieldtype': 'Currency'})+'</b>',
					"cantidad_pagada": '<b>'+frappe.format(total_pagado, {'fieldtype': 'Currency'})+'</b>',
					"outstanding_amount": '<b>'+frappe.format(total_pendiente, {'fieldtype': 'Currency'})+'</b>',
					"territory": ""
				})

	return ventas	

def delFilters(filters, toDel):
	for filter_del in toDel:
		try:
			del filters[filter_del]
		except:
			pass

	return filters
	
@frappe.whitelist()
def send_email(filters):
	filters = delFilters(json.loads(filters), ['group_by_party','report_date','ageing_based_on','range1','range2','range3','range4'])
	


	data = frappe.db.get_all('Sales Invoice', filters=filters, fields=['posting_date', 'due_date', 'customer', 'name', 'grand_total', 'outstanding_amount', 'territory'])
	
	# agrupo la data por cliente
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
        #	'condominium_ve.condominium_ve.report.cxc_cobranza.cxc_cobranza.send_email_queue', customer=customer, data_clientes=data_clientes[customer])

# formatea el correo
def send_email_queue(customer, data_clientes):
	total = {'grand_total':0, 'cantidad_pagada':0, 'outstanding_amount':0}
	for i in range(len(data_clientes)):
		data_clientes[i]['cantidad_pagada'] = data_clientes[i]['grand_total'] - data_clientes[i]['outstanding_amount']

		total['grand_total'] += data_clientes[i]['grand_total']
		total['cantidad_pagada'] += data_clientes[i]['grand_total'] - data_clientes[i]['outstanding_amount']
		total['outstanding_amount'] += data_clientes[i]['outstanding_amount']

	# informacion para formatear el correo
	propietario = frappe.db.get_all('Sales Invoice', filters={'customer':customer}, fields=['contact_email', 'territory', 'company', 'customer_name'])
	customer_name = propietario[0]['customer_name']
	email_to = propietario[0]['contact_email']
	sector = propietario[0]['territory']
	condominio = propietario[0]['company']

	pdf = generate_pdf(data=data_clientes, customer=customer_name, total=total, condominio=condominio, sector=sector)
		
	formato_email = frappe.db.get_all('formato email condominio', filters={'name':'cxc cobranza'}, fields=['subject', 'body'])
	
	# formatear variables del email
	subject = formato_email[0]['subject'].replace('{{propietario}}', customer_name)
	subject = subject.replace('{{sector}}', sector)
	subject = subject.replace('{{condominio}}', condominio)

	body = formato_email[0]['body'].replace('{{propietario}}', customer_name)
	body = body.replace('{{sector}}', sector)
	body = body.replace('{{condominio}}', condominio)

	# obtengo el archivo adjunto
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

	style = '<style>*{font-family:Sans-Serif;}</style>'

	if get_env('MOD_DEV') == 'False':
		send_email_condo(emails=[email_to], subject=subject, body=style+body, attachments=new_attachments)
	else:
		print('email dev ', get_env('EMAIL_DEV'))
		send_email_condo(emails=[get_env('EMAIL_DEV')], subject=subject, body=style+body, attachments=new_attachments)
# genera pdf en base a un html
def generate_pdf(data, customer, total, condominio="", sector=""):
	cart = data
	hora_actual = datetime.datetime.now().strftime("%I:%M %p")
	html = '<style>th,td{padding:4px 1px;}.info-cabecera{float: left; width:50%;}*{font-family:Sans-Serif;} th, td{border: 1px solid black;}</style>'
	html += '<p style="text-align:right;">'+datetime.date.today().strftime('%d-%m-%Y')+'<br>'+hora_actual+'</p>'
	html += '<p style="text-align:left;"><strong>'+condominio.upper()+'</strong><br>Sector: '+sector.upper()+'</p>'
	
	html += '<br><h4 style="text-align:center">Cuentas por Cobrar</h3>'
	html += '<p>'+customer.upper()+'</p>'

    # Add items to PDF HTML
	html += '<table style="border: 1px solid black; border-collapse: collapse; width: 100%;"> \
  			<thead style="background-color: #CCC; text-align: center; box-shadow: 0px 2px 2px #888888;">\
    			<tr>\
    			<th scope="col">'+_('Comprobante')+'</th>\
			      <th scope="col" width="50px">'+_('Fecha')+'</th>\
			      <th scope="col">'+_('Dias de Vencimiento')+'</th>\
			      <th scope="col">'+_('Cantidad Facturada')+'</th>\
			      <th scope="col">'+_('Cantidad Pagada')+'</th>\
			      <th scope="col">'+_('Cantidad Pendiente')+'</th>\
			    </tr>\
  			</thead>\
  			<tbody style="border: 1px solid black; text-align: center;">'
    
  

	for row in cart:
		dias_vencido = datetime.date.today() - row['due_date']
		html += '<tr>\
			      <td class="text-center">'+row['name']+'</td>\
			      <td class="text-center">'+row['posting_date'].strftime('%d-%m-%Y')+'</td>\
			      <td class="text-center">'+str(dias_vencido.days)+'</td>\
			      <td class="text-center">'+frappe.format(row['grand_total'], {'fieldtype': 'Currency'})+'</td>\
			      <td class="text-center">'+frappe.format(row['cantidad_pagada'], {'fieldtype': 'Currency'})+'</td>\
			      <td class="text-center">'+frappe.format(row['outstanding_amount'], {'fieldtype': 'Currency'})+'</td>\
			    </tr>'

	html += '<tr>\
			      <td></td>\
			      <td></td>\
			      <td class="text-center"><b>'+_('TOTAL')+'</b></td>\
			      <td class="text-center"></td>\
			      <td class="text-center"></td>\
			      <td class="text-center"><b>'+frappe.format(total['outstanding_amount'], {'fieldtype': 'Currency'})+'</b></td>\
			    </tr>'
	html += '</tbody>\
			</table>'

	return get_pdf(html)
	
# envia emails
def send_email_condo(emails, subject, body="", attachments=[]):
	return frappe.sendmail(
		recipients=emails,
		subject=subject,
		message="<div class='ql-editor read-mode'> {0} <p><br></p></div>".format(body),
		attachments=attachments)

# obtiene un archivo en bytes para poder ser insertado como adjunto a un correo
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