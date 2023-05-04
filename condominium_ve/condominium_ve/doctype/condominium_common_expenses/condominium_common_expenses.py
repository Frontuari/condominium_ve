# Copyright (c) 2022, Armando Rojas and contributors
# For license information, please see license.txt
import json
import frappe
from frappe.model.document import Document
from frappe.utils.response import build_response
from frappe.utils import add_to_date, now, add_days, password
from frappe.core.doctype.communication import email
from reportbro_integration.report_design.doctype.report_bro.report_bro import get_pdf_backend_api, get_pdf_backend_api_report
from reportbro_integration.utils.handler_extend import upload_file_report
from custom_ve.custom_ve.doctype.environment_variables.environment_variables import get_env
from condominium_ve.utils.utils import add_log


class CondominiumCommonExpenses(Document):
    
    def on_submit(self):
        doc = self.get_doc_before_save()
        
        excluded_sectors = []
        
        # obtengo los sectores que estan excluidos en este documento
        for es in doc.excluded_sectors:
            excluded_sectors.append({'territory':es.territory})

        # obtengo los sectores que si estan incluidos
        sectors = get_sectors(excluded_sectors)

        frappe.enqueue(
            'condominium_ve.condominium_ve.doctype.condominium_common_expenses.condominium_common_expenses.generate_process_sales_invoice', 
            obj=self, sectors=sectors)

    def generate_process(self, sector):
        doc = self.get_doc_before_save()

        total_details = self.get_total_ggc(doc.condominium_common_expenses_detail)
        total_ggc = total_details['total']

        doc_condo = frappe.get_doc('Condominium', doc.condominium)

        housings = frappe.db.get_list("Housing", fields=['*'], filters={
            'active': 1,
            'condominium': doc_condo.name,
            'sector': sector
        })


        # after_days = add_to_date(doc.posting_date, days=3, as_string=True)
        after_days = doc.posting_date

        array_exludes_sector = []

        # obtengo los sectores excluidos en el documento
        for es in doc.excluded_sectors:
            array_exludes_sector.append(es.territory)

        purchase_invoices_special = self.get_purchase_invoice_special(
            doc.condominium_common_expenses_invoices)
        
        for idx, house in enumerate(housings):
            try:
                if house.sector in array_exludes_sector:
                    continue

                # barra de progreso
                progress_percent = (idx+1) * 100 / len(housings)
                frappe.publish_progress(percent=progress_percent, 
                    title='Generando recibos del sector {0}'.format(sector), 
                    description='{0}/{1}. Vivienda {2}'.format(idx+1, len(housings),house.name))
            
                total_ggc_aux = total_ggc
                total_special = 0.0

                for p_invoice_special in purchase_invoices_special:
                    total_ggc_aux = total_ggc_aux - \
                        p_invoice_special['amount_total']

                    if house.sector in p_invoice_special['sector']:
                        total_special = p_invoice_special['amount_total_individual']

                total = total_ggc_aux / int(doc.active_units)
                total = total + total_special

                the_remarks = ' '
                if doc.is_remarks == 1:
                    the_remarks = doc.remarks

                # generar el recibo de cuota
                sales_invoice = frappe.get_doc(dict(
                    naming_series="RC-.YYYY..-.########",
                    doctype="Sales Invoice",
                    set_posting_time=1,
                    docstatus=0,
                    company=doc_condo.company,
                    customer=house.owner_customer,
                    posting_date=doc.posting_date,
                    due_date=after_days,
                    is_return=0,
                    disable_rounded_total=0,
                    cost_center=doc_condo.cost_center,
                    items=[
                        dict(
                            item_code='Cuota de Condominio',
                            item_name='Cuota de Condominio {0} {1} '.format(
                                get_month(doc.posting_date.month), doc.posting_date.year),
                            description='Cuota de Condominio {0} {1} '.format(
                                get_month(doc.posting_date.month), doc.posting_date.year),
                            qty=1,
                            stock_qty=0,
                            uom="Nos.",
                            conversion_factor=1,
                            base_rate=total,
                            rate=total,
                            base_amount=total,
                            amount=total,
                            income_account=doc_condo.account
                        )
                    ],
                    gc_condo=doc.name,
                    housing=house.housing,
                    select_print_heading="Recibo de Condominio",
                    remarks=the_remarks
                )).insert()
                sales_invoice.submit()
                
                # generar los recibos de fondos
                for fund in doc.funds:

                    cost_center_aux = ""
                    for res in doc_condo.reserve:
                        if res.account == fund.account:
                            cost_center_aux = res.cost_center

                    total_fund = float(fund.amount) * (float(house.aliquot) / 100)
                    sales_invoice_2 = frappe.get_doc(dict(
                        naming_series="RFC-.YYYY..-.########",
                        doctype="Sales Invoice",
                        set_posting_time=1,
                        cost_center=cost_center_aux,
                        docstatus=0,
                        company=doc_condo.company,
                        customer=house.owner_customer,
                        posting_date=doc.posting_date,
                        due_date=after_days,
                        is_return=0,
                        disable_rounded_total=0,
                        items=[
                            dict(
                                item_code='',
                                item_name='{2}  {0} {1} '.format(
                                    get_month(doc.posting_date.month), doc.posting_date.year, fund.concept),
                                description='{2}  {0} {1} '.format(
                                    get_month(doc.posting_date.month), doc.posting_date.year, fund.concept),
                                qty=1,
                                stock_qty=0,
                                uom="Nos.",
                                conversion_factor=1,
                                base_rate=total_fund,
                                rate=total_fund,
                                base_amount=total_fund,
                                amount=total_fund,
                                income_account=fund.account
                            )
                        ],
                        gc_condo=doc.name,
                        housing=house.housing,
                        select_print_heading="Recibo de Fondo de Condominio"
                    )).insert()

                    sales_invoice_2.submit()

                frappe.db.commit()
            except Exception as e:
                frappe.db.rollback()

                frappe.publish_realtime(
                    'msgprint', 'Error generando recibos para el cliente {0}: {1}'.format(
                        house.owner_customer, e
                        ))
                add_log(e, 'condominium_common_expenses.CondominiumCommonExpenses.generate_process', 
                        'Error generando recibos para el cliente {0}'
                        .format(house.owner_customer))

    def upgrade_purchase_invoice(self):
        doc = self
        try:
            for idx, invoice in enumerate(doc.condominium_common_expenses_invoices):
                # barra de progreso
                progress_percent = (idx+1) * 100 / len(doc.condominium_common_expenses_invoices)
                frappe.publish_progress(percent=progress_percent, 
                    title='Actualizando estatus de facturas de compras', 
                    description='{0}/{1}. {2}'.format(idx+1, 
                        len(doc.condominium_common_expenses_invoices),invoice.invoice))

                doc_invoice = frappe.get_doc(
                    'Purchase Invoice', invoice.invoice)
                doc_invoice.apply_process_condo = 1
                doc_invoice.save(ignore_permissions=True)

        except Exception as e:
            frappe.publish_realtime(
                'msgprint', 'Error actualizando status de facturas de compra:{0}'.format(e))
            
            add_log(e, 'condominium_common_expenses.CondominiumCommonExpenses.upgrade_purchase_invoice', 
                        'Error actualizando status de facturas de compra')

    def get_purchase_invoice_special(self, invoice_ids=[]):
        array_invoice_special = []
        for d in invoice_ids:
            doc_invoice = frappe.get_doc('Purchase Invoice', d.invoice)

            for item in doc_invoice.items:
                if item.is_single_sector == 1:
                    iva = 0.0
                    if item.item_tax_template:
                        if "16" in item.item_tax_template:
                            iva = 0.16

                    n_house = self.get_number_house_sector(item.sector)

                    array_invoice_special.append({
                        'invoice':  doc_invoice.name,
                        'total': doc_invoice.grand_total,
                        'sector': item.sector,
                        'amount': item.amount,
                        'amount_total': (item.amount + (item.amount * iva)),
                        'amount_total_individual': (item.amount + (item.amount * iva)) / n_house

                    })
        return array_invoice_special

    def get_number_house_sector(self, sector):

        sql = "SELECT count(sector) from tabHousing  where sector = '{0}' ".format(
            sector)

        resp = frappe.db.sql(sql)
        return resp[0][0]

    def get_total_ggc(self, ggc_table):
        total = 0.0
        total_per_unit = 0.0
        for ggc in ggc_table:
            total = total + ggc.amount
            total_per_unit += ggc.per_unit
        return {'total':total, 'total_per_unit':total_per_unit}

    def on_cancel(self):
        frappe.enqueue(
            'condominium_ve.condominium_ve.doctype.condominium_common_expenses.condominium_common_expenses.cancel_process_sales_invoice', obj=self)

    def cancel_process(self):
        doc = self.get_doc_before_save()

        sales_invoices = frappe.db.get_list("Sales Invoice", fields=['*'], filters={
            'gc_condo': doc.name,
            'docstatus' : 1
        })

        try:
            for idx, d in enumerate(sales_invoices):
                # barra de progreso
                progress_percent = (idx+1) * 100 / len(sales_invoices)
                frappe.publish_progress(percent=progress_percent, 
                    title='Cancelando recibos de condominio vinculados a {0}'.format(doc.name), 
                    description='{0}/{1}. {2}'.format(idx+1, len(sales_invoices), d.name))

                sales_invoice = frappe.get_doc('Sales Invoice', d.name)
                
                # antes
                #sales_invoice.cancel()

                # ahora
                if sales_invoice.docstatus == 1:
                    sales_invoice.cancel()

        except Exception as e:
            frappe.publish_realtime(
            'msgprint', 'Error Cancelando recibos de condominio: {0}'.format(e))

            add_log(e, 'condominium_common_expenses.CondominiumCommonExpenses.cancel_process', 
                        'Error Cancelando recibos de condominio')

        try:
            for idx, invoice in enumerate(doc.condominium_common_expenses_invoices):
                doc_invoice = frappe.get_doc(
                    'Purchase Invoice', invoice.invoice)
                doc_invoice.apply_process_condo = 0
                doc_invoice.save(ignore_permissions=True)

            frappe.publish_realtime(
                'msgprint', 'Estado de facturas de compra restaurado')

        except Exception as e:
            frappe.publish_realtime(
            'msgprint', 'Error actualizando estado de facturas de compra: {0}'.format(e))

            add_log(e, 'condominium_common_expenses.CondominiumCommonExpenses.cancel_process', 
                        'Error actualizando facturas de compra')

def generate_process_sales_invoice(obj, sectors):
    try:
        frappe.publish_realtime(
            'msgprint', 'Inicio de proceso de generar recibos de condominio')

        for sector in sectors:
            obj.generate_process(sector['sector'])

        frappe.enqueue(
                'condominium_ve.condominium_ve.doctype.condominium_common_expenses.condominium_common_expenses.generate_upgrade_purchase_invoice', 
                obj=obj)

    except Exception as e:
        add_log(e, 'condominium_common_expenses.generate_process_sales_invoice', 
                        '')

def generate_upgrade_purchase_invoice(obj):
    obj.upgrade_purchase_invoice()

def cancel_process_sales_invoice(obj):
    frappe.publish_realtime(
        'msgprint', 'Inicio de proceso de cancelar recibos de condominio')
    
    obj.cancel_process()

def get_emails(owner):
    emails = ""

    results = frappe.db.sql(
        "select email_id  from `tabContact Email` tce where parent like '%-{0}' ".format(owner.name))

    for r in results:
        emails = emails + r[0] + ","

    return emails

def get_emails_condo(sector):

    sql2 = """
        SELECT
        tce.email_id as email, tc.name as customer, tc.customer_name, th.code, th.name as house
        from
            `tabCustomer` tc
        join `tabContact Email` tce ON tce.parent = tc.customer_primary_contact
        join `tabHousing` th ON th.owner_customer = tc.name
        where
            tce.email_id is not null
            and  tc.customer_primary_contact is not null
            and  th.sector = '{0}'

    """.format(sector)

    data = frappe.db.sql(sql2, as_dict=True)

    return data

def send_email(emails, name, description=""):
    return email.make(recipients=emails,
                      subject="Recibo de Condominio: " + name,
                      content="<div class='ql-editor read-mode'> {0} <p><br></p></div>".format(
                          description),
                      doctype="Sales Invoice",
                      name=name,
                      send_email="1",
                      print_html="",
                      send_me_a_copy=0,
                      print_format="Standard",
                      attachments=[],
                      _lang="es",
                      read_receipt=0,
                      print_letterhead=1)

@frappe.whitelist()
def send_email_condo(emails, name, description="", attachments=[]):
    return email.make(recipients=emails,
                      subject="Recibo de Condominio: " + name,
                      content="<div class='ql-editor read-mode'> {0} <p><br></p></div>".format(
                          description),
                      # doctype="Sales Invoice",
                      # name=name,
                      send_email="1",
                      print_html="",
                      send_me_a_copy=0,
                      # print_format="Standard",
                      attachments=attachments,
                      _lang="es-VE",
                      read_receipt=0,
                      print_letterhead=1)

def create_attachment(filename='', path=None):
	if not path:
		root_directory = frappe.db.get_value('Environment Variables', 'ROOT_DIRECTORY', 'value')
		file = frappe.get_doc("File",filename)
		path = root_directory+'/'+frappe.get_site_path(file.file_url)  
		fname = file.file_name
	else:
		fname = os.path.basename(path)

	with open(path, "rb") as fileobj:
		filedata = fileobj.read() 
	#frappe.publish_realtime('msgprint', f'enviando correo a {fname}')
	out = {
		"fname": fname,
		"fcontent": filedata
	}
	return out 

def send_email_condo_queue(ggc, excluded_sectors):#  , sector):
    ####
    attachments = []
    
    # obtengo el primer pdf
    try:    
        file = get_pdf_backend_api(report_name='Relacion de Gastos',
                        doctype="Condominium Common Expenses", name=ggc, as_download=True)
       
        out = {
            "fname": "relacion_de_gastos.pdf",
            "fcontent": file.content
        }
        attachments.append(out)

        # obtengo el segundo pdf
    
        file = get_pdf_backend_api(report_name='Reporte de Gastos Comunes',
                doctype="Condominium Common Expenses", name=ggc, as_download=True)
        out = {
            "fname": "reporte_de_gastos_comunes.pdf",
            "fcontent": file.content
        }
        attachments.append(out)

    except Exception as e:
        frappe.publish_realtime(
            'msgprint', 'Error generando pdf a enviar: {0}'.format(e))
        add_log(e, 'condominium_common_expenses.send_email_condo_queue', 'generando reportes de pdf')
        return
 

    sectors = get_sectors(excluded_sectors)

    # recorro las casas por sectores y obtengo los emails de los propietarios
    for s in sectors:
        sector = s['sector']
        try:
            data_emails = get_emails_condo(sector)

            doc_ggc = frappe.get_doc("Condominium Common Expenses", ggc)
            
            description_email_text = doc_ggc.send_text if doc_ggc.send_text else "Estimado Propietario {0}, Su recibo de condomnio del mes"
            #invoice_aux = ""

            for idx, d in enumerate(data_emails):
                # barra de progreso
                progress_percent = (idx+1) * 100 / len(data_emails)
                frappe.publish_progress(percent=progress_percent, 
                    title='Agregando emails del sector {0} a cola de correos'.format(sector), 
                    description='{0}/{1}. Vivienda: {2}, Correo: {3}'.format(idx+1,
                     len(data_emails),d['house'],d['email']))

                new_attachments = attachments

                #invoice_aux = d['invoice']
                # agrego el nombre del propietario al mensaje del correo
                email_content_text = description_email_text.format(d['customer_name'])

                extra_message = ''
                if d['code']:
                    url_code = get_env('URL_AUTOGESTION') + d['code']
                    extra_message = "<br><br><br>  <p> Su codigo para consulta y realizar pagos en el sistema de autogestion es: \
                        {0}</p>  <br>  <a href='{1}' > \
                        Click aqui para ir a la autogestion </a>".format(d['code'], url_code)

                if get_env('MOD_DEV') == 'False':
                    send_email_condo(emails=d['email'], name=ggc,
                        description=email_content_text + extra_message, attachments=new_attachments) #
                else:
                    send_email_condo(emails=get_env('EMAIL_DEV'), name=ggc,
                        description=email_content_text + extra_message, attachments=new_attachments)
                        
        except Exception as e:
            frappe.publish_realtime(
                'msgprint', 'Error enviando correos para el sector {0}: {1}'.format(sector, e))

            add_log(e, 'condominium_common_expenses.send_email_condo_queue', 'enviando correos para el sector {0}'.format(sector))
            

    # envio el email a la administracion del condominio
    email_condo = get_env('EMAIL_CONDO')
    descripcion_email_condo = "Copia de correo electronico enviado a propietarios"
    if len(email_condo) > 0:
        send_email_condo(emails=email_condo, name=ggc,
                description=descripcion_email_condo, attachments=attachments) 

@frappe.whitelist()
def send_email_test(ggc, excluded_sectors):
    frappe.enqueue(
        'condominium_ve.condominium_ve.doctype.condominium_common_expenses.condominium_common_expenses.send_email_condo_queue',
        queue='short',
        is_async=True,
        ggc=ggc,
        excluded_sectors=excluded_sectors)# , sector=s['sector'])
        
@frappe.whitelist()
def is_invoices_generated(ggc, excluded_sectors):
    num_invoices = frappe.db.count('Sales Invoice', 
        filters={'gc_condo':ggc, 'select_print_heading':"Recibo de Condominio"})

    sectores = get_sectors(excluded_sectors)

    num_active_houses = 0
    for sector in sectores:
        num_active_houses += frappe.db.count('Housing', 
                filters={'active':1, 'sector':sector['sector']})

    frappe.local.response.update({"data": num_invoices < num_active_houses})
    
    return build_response("json")

@frappe.whitelist()
def gen_missing_invoices(ggc, excluded_sectors):
    
    sectores = get_sectors(excluded_sectors)
    frappe.enqueue(
        'condominium_ve.condominium_ve.doctype.condominium_common_expenses.condominium_common_expenses.gen_missing_invoice_queue',
        queue='short',
        is_async=True,
        ggc=ggc,
        sectors=sectores)

def gen_missing_invoice_queue(ggc, sectors):
    missing_customers = []
    try:
        for sector in sectors:
            invoices_dict = frappe.get_all('Sales Invoice', 
                filters={'gc_condo': ggc, 'territory': sector['sector'], 
                'docstatus':1, 'select_print_heading':"Recibo de Condominio"},
                fields=['customer'])

            invoices = [d['customer'] for d in invoices_dict]

            customers_dict = frappe.get_all('Housing', 
                filters={'sector': sector['sector']},
                fields=['owner_customer'])

            customers = [d['owner_customer'] for d in customers_dict]

            # clientes que faltan por factura
            for customer in customers:
                if customer not in invoices:
                    missing_customers.append(customer)

        gen_missing_invoice(ggc, missing_customers)

    except Exception as e:
        frappe.publish_realtime(
                'msgprint', 
                'Error buscando propietarios: {0}'.format(e) )
        add_log(e, 'condominium_common_expenses.gen_missing_invoice_queue', 'Error buscando propietarios')
  

def gen_missing_invoice(ggc, customers):
    doc = frappe.get_doc('Condominium Common Expenses', ggc)

    total_details = get_total_ggc_detail(doc.condominium_common_expenses_detail)
    total_ggc = total_details['total']
    #total_ggc_per_unit = total_details['total_per_unit']

    doc_condo = frappe.get_doc('Condominium', doc.condominium)
  
    housings = frappe.db.get_list("Housing", fields=['*'], filters={
        'active': 1,
        'condominium': doc_condo.name
    })

    after_days = doc.posting_date

    
    purchase_invoices_special = get_purchase_invoice_special_(
        doc.condominium_common_expenses_invoices)
   
    
    idx = 0
    for house in housings:
        try:
            # sino esta en la lista de facturas pendientes salta al siguiente indice
            if house.owner_customer not in customers:
                continue


            # barra de progreso
            progress_percent = (idx+1) * 100 / len(customers)
            frappe.publish_progress(percent=progress_percent, 
                title='Generando Recibos Faltantes', 
                description='{0}/{1}. Vivienda {2} Sector {3}'.format(idx+1, len(customers),
                    house.name, house.sector))

        
            total_ggc_aux = total_ggc
            #aliquot_house = (float(house.aliquot) / 100)
            total_special = 0.0

            for p_invoice_special in purchase_invoices_special:
                total_ggc_aux = total_ggc_aux - \
                    p_invoice_special['amount_total']

                if house.sector in p_invoice_special['sector']:
                    total_special = p_invoice_special['amount_total_individual']

            total = total_ggc_aux / int(doc.active_units)
            total = total + total_special

            the_remarks = ' '
            if doc.is_remarks == 1:
                the_remarks = doc.remarks


            sales_invoice = frappe.get_doc(dict(
                naming_series="RC-.YYYY..-.########",
                doctype="Sales Invoice",
                set_posting_time=1,
                docstatus=0,
                company=doc_condo.company,
                customer=house.owner_customer,
                posting_date=doc.posting_date,
                due_date=after_days,
                is_return=0,
                disable_rounded_total=0,
                cost_center=doc_condo.cost_center,
                items=[
                    dict(
                        item_code='Cuota de Condominio',
                        item_name='Cuota de Condominio {0} {1} '.format(
                            get_month(doc.posting_date.month), doc.posting_date.year),
                        description='Cuota de Condominio {0} {1} '.format(
                            get_month(doc.posting_date.month), doc.posting_date.year),
                        qty=1,
                        stock_qty=0,
                        uom="Nos.",
                        conversion_factor=1,
                        base_rate=total,
                        rate=total,
                        base_amount=total,
                        amount=total,
                        income_account=doc_condo.account
                    )
                ],
                gc_condo=doc.name,
                housing=house.housing,
                select_print_heading="Recibo de Condominio",
                remarks=the_remarks
            )).insert()
            # sales_invoice.queue_action('submit')
            sales_invoice.submit()

            for fund in doc.funds:
                
                cost_center_aux = ""
                for res in doc_condo.reserve:
                    if res.account == fund.account:
                        cost_center_aux = res.cost_center

                total_fund = float(fund.amount) * (float(house.aliquot) / 100)
                sales_invoice_2 = frappe.get_doc(dict(
                    naming_series="RFC-.YYYY..-.########",
                    doctype="Sales Invoice",
                    set_posting_time=1,
                    cost_center=cost_center_aux,
                    docstatus=0,
                    company=doc_condo.company,
                    customer=house.owner_customer,
                    posting_date=doc.posting_date,
                    due_date=after_days,
                    is_return=0,
                    disable_rounded_total=0,
                    items=[
                        dict(
                            item_code='',
                            item_name='{2}  {0} {1} '.format(
                                get_month(doc.posting_date.month), doc.posting_date.year, fund.concept),
                            description='{2}  {0} {1} '.format(
                                get_month(doc.posting_date.month), doc.posting_date.year, fund.concept),
                            qty=1,
                            stock_qty=0,
                            uom="Nos.",
                            conversion_factor=1,
                            base_rate=total_fund,
                            rate=total_fund,
                            base_amount=total_fund,
                            amount=total_fund,
                            income_account=fund.account
                        )
                    ],
                    gc_condo=doc.name,
                    housing=house.housing,
                    select_print_heading="Recibo de Fondo de Condominio"
                )).insert()
                # sales_invoice_2.queue_action('submit')
                sales_invoice_2.submit()

            frappe.db.commit()

            idx += 1
        except Exception as e:
            frappe.db.rollback()

            frappe.publish_realtime(
                'msgprint', 'Error Generando recibos faltantes: {0}'.format(e))

            add_log(e, 'condominium_common_expenses.gen_missing_invoice_queue', 'Error Generando recibos faltantes')

def get_total_ggc_detail(ggc_table):
    total = 0.0
    total_per_unit = 0.0
    for ggc in ggc_table:
        total = total + ggc.amount
        total_per_unit += ggc.per_unit
    return {'total':total, 'total_per_unit':total_per_unit}

def get_purchase_invoice_special_(invoice_ids=[]):
    array_invoice_special = []
    for d in invoice_ids:
        doc_invoice = frappe.get_doc('Purchase Invoice', d.invoice)

        for item in doc_invoice.items:
            if item.is_single_sector == 1:
                iva = 0.0
                if item.item_tax_template:
                    if "16" in item.item_tax_template:
                        iva = 0.16

                n_house = frappe.db.count('Housing', 
                            filters={'active':1, 'sector':sector['sector']})

                array_invoice_special.append({
                    'invoice':  doc_invoice.name,
                    'total': doc_invoice.grand_total,
                    'sector': item.sector,
                    'amount': item.amount,
                    'amount_total': (item.amount + (item.amount * iva)),
                    'amount_total_individual': (item.amount + (item.amount * iva)) / n_house

                })
    return array_invoice_special

def get_month(number):

    months = {

        1: "Enero",
        2: "Febrero",
        3: "Marzo",
        4: "Abril",
        5: "Mayo",
        6: "Junio",
        7: "Julio",
        8: "Agosto",
        9: "Septiembre",
        10: "Octubre",
        11: "Noviembre",
        12: "Diciembre"
    }

    return months[number]

# por revisar
@frappe.whitelist()
def send(name):
    cce_doc = frappe.db.get_doc("Condominium Common Expenses")

    invoices_list = frappe.db.get_list("Sales Invoice", fields=['*'], filters={
        'name': cce_doc.name,
    })

    for invoice in invoices_list:
        customer = frappe.get("Customer", invoice.customer)
        pass

def is_fund(cost_center):
    if cost_center != "Gastos Comunes Variables":
        cc = frappe.get_doc("Cost Center", cost_center)
        parent_cc = frappe.get_doc("Cost Center", cc.parent_cost_center)
        return parent_cc.is_reserve
    return 0

def get_previous_funds(condo, date):
    previous_funds = 0.0
    gcc_list = frappe.db.get_list("Condominium Common Expenses",  filters={

        "posting_date": ["<=", date],
        "docstatus": 1,
        "condominium": condo
    }, fields=['*'], order_by='posting_date DESC')

    if gcc_list:
        gcc = gcc_list[0]
        if gcc:
            if gcc.funds_current:
                previous_funds = gcc.funds_current

    return previous_funds

def get_previous_name(condo, date):
    previous_funds = None
    gcc_list = frappe.db.get_list("Condominium Common Expenses",  filters={

        "posting_date": ["<=", date],
        "docstatus": 1,
        "condominium": condo
    }, fields=['*'], order_by='posting_date DESC')

    if gcc_list:
        gcc = gcc_list[0]
        if gcc:
            if gcc.name:
                previous_funds = gcc.name

    return previous_funds

def get_previous_date(condo, date):
    previous_funds = "2022-01-01"
    gcc_list = frappe.db.get_list("Condominium Common Expenses",  filters={

        "posting_date": ["<=", date],
        "docstatus": 1,
        "condominium": condo
    }, fields=['*'], order_by='posting_date DESC')

    if gcc_list:
        gcc = gcc_list[0]
        if gcc:
            if gcc.posting_date:
                previous_funds = gcc.posting_date

    return previous_funds

def entry_funds_detail(from_date, to_date, company, cost_center_parent):
    return frappe.db.sql("""
        SELECT
        	tpi.name ,
        	tpe.posting_date ,
        	tpi.grand_total ,
        	tpi.grand_total  - tpi.outstanding_amount 	 as payment,
        	tpi.cost_center ,
        	tcc.parent_cost_center
        from
        	`tabSales Invoice`  tpi
        join `tabCost Center` tcc ON tcc.name  = tpi.cost_center
        join `tabPayment Entry Reference` tper on tper.reference_name  = tpi.name
        join  `tabPayment Entry` tpe on tpe.name = tper.parent and tpe.docstatus = 1
         where  tpe.posting_date >= '{0}' and tpe.posting_date <= '{1}' and (tcc.parent_cost_center = '{2}' or  tcc.name = '{2}'   ) and tpi.company = '{3}' and tpi.docstatus = 1   """.format(from_date, to_date, cost_center_parent, company))

def expedition_funds_detail(from_date, to_date, company, cost_center_parent):
    return frappe.db.sql("""
        SELECT
        	tpi.name ,
        	tpi.posting_date ,
        	tpi.grand_total ,
        	tpi.grand_total  - tpi.outstanding_amount 	 as payment,
        	tpi.cost_center ,
        	tcc.parent_cost_center
        from
        	`tabSales Invoice`  tpi
         join `tabCost Center` tcc ON tcc.name  = tpi.cost_center
        left join `tabPayment Entry Reference` tper on tper.reference_name  = tpi.name
        left join  `tabPayment Entry` tpe on tpe.name = tper.parent and tpe.docstatus = 1

         where  tpe.posting_date >= '{0}' and tpe.posting_date <= '{1}' and (tcc.parent_cost_center = '{2}' or  tcc.name = '{2}'   ) and tpi.company = '{3}'  and tpi.docstatus = 1 """.format(from_date, to_date,  cost_center_parent, company))

def entry_funds(from_date, to_date, company, cost_center_parent):
    sql = """
        SELECT
           COALESCE( sum(tpi.grand_total  - tpi.outstanding_amount)  , 0.0)	 as payment
        from
            `tabSales Invoice`  tpi
        join `tabCost Center` tcc ON tcc.name  = tpi.cost_center
        join `tabPayment Entry Reference` tper on tper.reference_name  = tpi.name
        join  `tabPayment Entry` tpe on tpe.name = tper.parent and tpe.docstatus = 1
        where  tpe.posting_date >= '{0}' and tpe.posting_date <= '{1}' and (tcc.parent_cost_center = '{2}' or  tcc.name = '{2}'   ) and tpi.company = '{3}' and tpi.docstatus = 1  """.format(from_date, to_date, cost_center_parent, company)

    data = frappe.db.sql(sql)

    return data[0][0]

def expedition_funds(from_date, to_date, company, cost_center_parent):
    sql = """
        SELECT
            COALESCE(sum(tpi.grand_total )  , 0.0	) as payment
        from
        `tabPurchase Invoice`  tpi
        join `tabCost Center` tcc ON tcc.name  = tpi.cost_center
        left join `tabPayment Entry Reference` tper on tper.reference_name  = tpi.name
        left join  `tabPayment Entry` tpe on tpe.name = tper.parent and tpe.docstatus = 1
        where  tpi.posting_date >= '{0}' and tpi.posting_date <= '{1}' and (tcc.parent_cost_center = '{2}' or  tcc.name = '{2}'   ) and tpi.company = '{3}' and tpi.docstatus = 1 """.format(from_date, to_date,   cost_center_parent, company)
    data = frappe.db.sql(sql)

    print(sql)
    return data[0][0]

def get_sectors(excluded_sectors=[]):
    sectors = frappe.db.sql(
            "SELECT DISTINCT  sector  from tabHousing ", as_dict=True)
    
    if excluded_sectors != []:
        if isinstance(excluded_sectors, str):
            excluded_sectors = json.loads(excluded_sectors)
        for excluded_sector in excluded_sectors:
            territory = excluded_sector['territory']
            
            for i in range(len(sectors)):
                if sectors[i]['sector'] == territory:
                    sectors.pop(i)
                    break

    return sectors

@frappe.whitelist()
def get_active_house_sectors(excluded_sectors=[]):
    sectores = get_sectors(excluded_sectors)

    total_active_units = 0
    for sector in sectores:
        houses = frappe.db.get_all('Housing', filters={'sector':sector['sector'], 'active': 1})
        total_active_units += len(houses)
        
    frappe.local.response.update({"data": total_active_units})
    
    return build_response("json")    

@frappe.whitelist()
def get_invoice_condo(condo, date):

    funds = []
    total = 0
    total_per_unit = 0

    previous_funds = get_previous_funds(condo, date)
    previous_date = get_previous_date(condo, date)
    previous_name = get_previous_name(condo, date)

    funds_receive_total = 0.0
    funds_expenditure_total = 0.0
    funds_current_total = 0.0

    previus_day = add_days(date, -28)

    purchase_invoice_list = frappe.db.get_list("Purchase Invoice",  filters=[
        ["is_for_condominium", "=", 1],
        ["apply_process_condo", "=", 0],
        ["docstatus", "=", 1],
        ["is_return", "=", 0],
        ["condominium", "=", condo],
        ["status", "in", ["Overdue", "Unpaid", "Partly Paid", "Paid"]],
        ["posting_date", '>=', previus_day],
        ["posting_date", '<=', date]
    ], order_by='cost_center ASC')

    doc_condo = frappe.get_doc('Condominium', condo)

    data_invoice = []
    data_item = []
    data_cost_center = {}

    active_units = doc_condo.n_houses_active
    parent_cost_center = ""

    for purchase_invoice_data in purchase_invoice_list:

        invoice = frappe.get_doc(
            "Purchase Invoice", purchase_invoice_data.name)

        is_for_fund = 0

        cost_center_aux = invoice.cost_center

        if not invoice.cost_center:
            parent_cost_center = "Gastos Comunes Variables"
            invoice.cost_center = "Gastos Comunes Variables"
            invoice.description = "Gastos Comunes Variables"
        else:
            cost_center_doc = frappe.get_doc(
                'Cost Center', invoice.cost_center)

            parent_cost_center_doc = frappe.get_doc(
                'Cost Center', cost_center_doc.parent_cost_center)

            parent_cost_center = parent_cost_center_doc.cost_center_name

            if not invoice.description:
                invoice.description = invoice.remarks

            is_for_fund = parent_cost_center_doc.is_reserve

        if not (invoice.description + invoice.supplier) in data_cost_center.keys():
            data_cost_center[invoice.description + invoice.supplier] = {
                'amount': 0,
                'concept': invoice.description,
                'per_unit': 0,
                'parent_cost_center': parent_cost_center,
                'supplier': invoice.supplier_name,
                'is_for_fund': is_for_fund

            }

        element = data_cost_center[invoice.description + invoice.supplier]

        element['amount'] = element['amount'] + invoice.total
        element['per_unit'] = element['per_unit'] + \
            (invoice.total / doc_condo.n_houses_active)
        element['supplier'] = element['supplier']

        data_cost_center[invoice.description + invoice.supplier] = element

        data_invoice.append({
            'date': invoice.posting_date,
            'invoice': invoice.name,
            'supplier': invoice.supplier,
            'amount': invoice.total
        })
        if is_fund(invoice.cost_center) == 0:
            total = total + invoice.total
            total_per_unit = total_per_unit + \
                (invoice.total / doc_condo.n_houses_active)

    data_cost_center_copy = data_cost_center
    data_cost_center = []
    data_cost_center_fund = []

    keys_reserve = []
    fund_total_reserve = []

    for fund in doc_condo.reserve:
        if fund.active == 0:
            continue
        keys_reserve.append(fund.cost_center_name)

    for dd in data_cost_center_copy.keys():

        if data_cost_center_copy[dd]['is_for_fund'] == 0:
            data_cost_center.append(data_cost_center_copy[dd])
        else:
            data_cost_center_fund.append(data_cost_center_copy[dd])

    for fund in doc_condo.reserve:

        if fund.active == 0:
            continue

        funds.append({'concept': fund.description, 'amount': fund.amount,
                      'amount_per_unit': fund.amount / doc_condo.n_houses_active,  'account': fund.account})
        
        total = total + fund.amount
        total_per_unit = total_per_unit + fund.amount / doc_condo.n_houses_active

    detail_funds_use = []
    previous_gcc = None
    if previous_name:
        previous_gcc = frappe.get_doc(
            'Condominium Common Expenses', previous_name)

    for reserve in doc_condo.reserve:

        if reserve.active == 0:
            continue

        entry = entry_funds(previous_date, date,
                            doc_condo.company, reserve.parent_cost_center)
        exp = expedition_funds(previous_date, date,
                               doc_condo.company, reserve.parent_cost_center)

        funds_receive_total = funds_receive_total + entry
        funds_expenditure_total = funds_expenditure_total + exp
        previous_funds_aux = 0.0

        if previous_gcc:
            previous_gcc.detail_funds
            for pre in previous_gcc.detail_funds:

                if pre.concept == reserve.description:
                    previous_funds_aux = pre.funds_current

        detail_funds_use.append({
            'concept': reserve.description,
            'funds_receive': entry,
            'funds_expenditure': exp,
            'funds_current': entry + previous_funds_aux - exp,
            'previous_funds': previous_funds_aux
        })

    funds_current_total = funds_receive_total + \
        previous_funds - funds_expenditure_total

    # fecha de creacion de fondos
    creacion_fondos = frappe.db.get_all('Condominium Reserve Fund', fields=['creation', 'description'])

    frappe.local.response.update({"data": {
        'invoices': data_invoice,
        'detail': data_cost_center,
        'detail_2': data_item,
        'active_units': active_units,
        'total': total,
        'total_per_unit': total_per_unit,
        'funds': funds,
        'expense_funds': data_cost_center_fund,
        'previous_funds': previous_funds,
        'funds_receive_total': funds_receive_total,
        'funds_expenditure_total': funds_expenditure_total,
        'funds_current_total': funds_current_total,
        'detail_funds_use': detail_funds_use,
        'creation_funds_date': creacion_fondos
    }})

    return build_response("json")
