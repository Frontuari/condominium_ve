# Copyright (c) 2022, Armando Rojas and contributors
# For license information, please see license.txt
import json
import frappe
from frappe.model.document import Document
from frappe.utils.response import build_response
from datetime import datetime  # from python std library
from frappe.utils import add_to_date
from frappe.core.doctype.communication import email
from custom_reports.report_design.doctype.report_bro.report_bro import get_pdf_backend_api, get_pdf_backend_api_report
from custom_reports.utils.handler_extend import upload_file_report
from custom_ve.custom_ve.doctype.environment_variables.environment_variables import get_env


class CondominiumCommonExpenses(Document):

    def on_submit(self):
        # self.generate_process()
        frappe.enqueue(
            'condominium_ve.condominium_ve.doctype.condominium_common_expenses.condominium_common_expenses.generate_process_sales_invoice', obj=self)

    def generate_process(self):
        doc = self.get_doc_before_save()

        total_ggc = self.get_total_ggc(doc.condominium_common_expenses_detail)

        doc_condo = frappe.get_doc('Condominium', doc.condominium)

        housings = frappe.db.get_list("Housing", fields=['*'], filters={
            'active': 1,
            'condominium': doc_condo.name,
        })

        # after_days = add_to_date(doc.posting_date, days=3, as_string=True)
        after_days = doc.posting_date

        for house in housings:
            total = total_ggc * (float(house.aliquot) / 100)

            # owner = frappe.get_doc('Customer', house.owner_customer)

            # emails = get_emails(owner)

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
                select_print_heading="Recibo de Condominio"
            )).insert()
            # sales_invoice.queue_action('submit')
            sales_invoice.submit()
            print("Factura no. " + sales_invoice.name)

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

            # if len(emails) > 0:
            #    send_email(emails, sales_invoice.name, description='Cuota de Condominio {0} {1} '.format(
            #        get_month(doc.posting_date.month), doc.posting_date.year))

        for invoice in doc.condominium_common_expenses_invoices:
            doc_invoice = frappe.get_doc(
                'Purchase Invoice', invoice.invoice)
            doc_invoice.apply_process_condo = 1
            doc_invoice.save(ignore_permissions=True)

    def get_total_ggc(self, ggc_table):
        total = 0.0
        for ggc in ggc_table:
            total = total + ggc.amount

        return total

    def on_cancel(self):
        # self.cancel_process()
        frappe.enqueue(
            'condominium_ve.condominium_ve.doctype.condominium_common_expenses.condominium_common_expenses.cancel_process_sales_invoice', obj=self)

    def cancel_process(self):
        doc = self.get_doc_before_save()

        sales_invoices = frappe.db.get_list("Sales Invoice", fields=['*'], filters={
            'gc_condo': doc.name,
        })

        for d in sales_invoices:
            sales_invoice = frappe.get_doc('Sales Invoice', d.name)
            sales_invoice.queue_action('cancel')

        for invoice in doc.condominium_common_expenses_invoices:
            doc_invoice = frappe.get_doc(
                'Purchase Invoice', invoice.invoice)
            doc_invoice.apply_process_condo = 0
            doc_invoice.save(ignore_permissions=True)


def get_emails(owner):
    emails = ""

    results = frappe.db.sql(
        "select email_id  from `tabContact Email` tce where parent like '%-{0}' ".format(owner.name))

    for r in results:
        emails = emails + r[0] + ","

    return emails


def get_emails_condo(gcc):
    sql = """
        SELECT
        tce.email_id as email, tsi.name as invoice, tsi.customer , tsi.housing , tsi.code
        from
            `tabSales Invoice` tsi
        join tabCustomer tc ON  tsi.customer = tc.name
        join `tabContact Email` tce ON tce.parent like concat('%-' , tc.name )
        where
            tsi.docstatus in (0 , 1)
            and gc_condo = '{0}'
            and select_print_heading = 'Recibo de Condominio'
            and tc.email_id is not null

            order by tsi.housing ASC
    """.format(gcc)

    data = frappe.db.sql(sql, as_dict=True)

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


def generate_process_sales_invoice(obj):
    frappe.publish_realtime(
        'msgprint', 'Inicio de proceso de generar recibos de condominio')
    print("Inicio del proceso")

    obj.generate_process()

    print("Fin del proceso")
    frappe.publish_realtime(
        'msgprint', 'Finalizacion de proceso de generar recibos de condominio')


def cancel_process_sales_invoice(obj):
    frappe.publish_realtime(
        'msgprint', 'Inicio de proceso de cancelar recibos de condominio')
    print("Inicio del proceso")
    obj.cancel_process()
    print("Fin del proceso")
    frappe.publish_realtime(
        'msgprint', 'Finalizacion de proceso de cancelar recibos de condominio')


def send_email_condo_queue(ggc):
    frappe.publish_realtime(
        'msgprint', 'Inicio de proceso de envio de correos')
    print("Encolar proceso")
    data_emails = get_emails_condo(ggc)

    doc_ggc = frappe.get_doc("Condominium Common Expenses", ggc)

    file = get_pdf_backend_api(report_name='Relacion de Gastos',
                               doctype="Condominium Common Expenses", name=ggc, as_download=True)

    ret = frappe.get_doc({
        "doctype": "File",
        "folder": "Home",
        "file_name": "relacion_de_gastos.pdf",
        "is_private": 1,
        "content": file.content,
    })
    ret.save(ignore_permissions=True)

    attachments = [ret.name]
    attachments_simp = [ret.name]

    file = get_pdf_backend_api(report_name='Reporte de Gastos Comunes',
                               doctype="Condominium Common Expenses", name=ggc, as_download=True)
    ret = frappe.get_doc({
        "doctype": "File",
        "folder": "Home",
        "file_name": "reporte_de_gastos_comunes.pdf",
        "is_private": 1,
        "content": file.content,
    })
    ret.save(ignore_permissions=True)
    attachments.append(ret.name)
    attachments_simp.append(ret.name)

    description_email_text = doc_ggc.send_text if doc_ggc.send_text else "Estimado Propietario, Su recibo de condomnio del mes"

    for d in data_emails:
        new_attachments = attachments
        file = get_pdf_backend_api_report(
            report_name='Recibo de Condominio Copia', params=json.dumps({
                # 'company': doc_ggc.company,
                'condominium': ggc,
                "customer": d['customer'],
                "from_date": "2000-01-01",
                "housing":  d['housing'],
                "to_date":  "2099-12-31"
            }))
        ret = frappe.get_doc({
            "doctype": "File",
            "folder": "Home",
            "file_name": "recibo_de_condominio.pdf",
            "is_private": 1,
            "content": file.content,
        })
        ret.save(ignore_permissions=True)
        new_attachments.append(ret.name)

        extra_message = "<br>  <p> Su codigo para consulta y realizar pagos es: {0}</p>".format(
            d['code']) if d['code'] else ''

        if get_env('MOD_DEV') == 'False':
            send_email_condo(emails=d['email'], name=d['invoice'],
                             description=description_email_text + extra_message, attachments=new_attachments)
        else:

            send_email_condo(emails='armando.develop@gmail.com', name=d['invoice'],
                             description=description_email_text + extra_message, attachments=new_attachments)
            break

    email_condo = get_env('EMAIL_CONDO')
    if len(email_condo) > 0:
        send_email_condo(emails=email_condo, name=d['invoice'],
                         description=description_email_text, attachments=attachments_simp)

    print("finalizar proceso")
    frappe.publish_realtime('msgprint', 'Finalizacion de envio de Correos')


@frappe.whitelist()
def send_email_test(ggc):
    frappe.enqueue(
        'condominium_ve.condominium_ve.doctype.condominium_common_expenses.condominium_common_expenses.send_email_condo_queue', ggc=ggc)


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

    purchase_invoice_list = frappe.db.get_list("Purchase Invoice",  filters=[
        ["is_for_condominium", "=", 1],
        ["apply_process_condo", "=", 0],
        ["docstatus", "=", 1],
        ["is_return", "=", 0],
        ["condominium", "=", condo],
        ["status", "in", ["Overdue", "Unpaid", "Partly Paid", "Paid"]],
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
        keys_reserve.append(fund.cost_center_name)

    for dd in data_cost_center_copy.keys():

        if data_cost_center_copy[dd]['is_for_fund'] == 0:
            data_cost_center.append(data_cost_center_copy[dd])
        else:
            data_cost_center_fund.append(data_cost_center_copy[dd])

    for fund in doc_condo.reserve:

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
        'detail_funds_use': detail_funds_use
    }})

    return build_response("json")
