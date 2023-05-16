
from reportbro_integration.utils.print_format import get_pdf
import frappe
from frappe.utils.response import build_response
from reportbro_integration.report_design.doctype.report_bro.report_bro import get_pdf_backend


@frappe.whitelist(allow_guest=True)
def query_code(code=""):

    if not code:
        frappe.throw("El codigo no puede estar vacio")

    exist_housing = frappe.db.exists(
        "Housing", {
            "code": code,
        },
    )
    cce_list = []
    payments = []

    if exist_housing:

        customer = get_customer(code)
        cce_list = get_gcc(customer['condominium'])
        balance = get_balance(customer['customer'])
        payments = get_payments(customer['customer'])
        invoices = get_sales_invoice(customer['customer'])

    else:
        frappe.throw("Propietario no encontrado ")

    frappe.local.response.update({"data": {
        "balance": balance,
        "cc_condo": cce_list,
        "payments": payments,
        "customer": customer,
        "invoices" : invoices
    }})

    return build_response("json")


def get_gcc(condominium):
    result = []
    data = frappe.db.sql(" SELECT name , posting_date , total  FROM  `tabCondominium Common Expenses` tcce where condominium = {} and docstatus=1 ".format(
        frappe.db.escape(condominium)))

    for d in data:
        result.append({'name':  d[0],  'posting_date': d[1], 'total': d[2]})

    return result


def get_payments(customer):

    data = frappe.db.sql(" SELECT name , party_name , posting_date , received_amount  from `tabPayment Entry` tpe  where party_name = {} and docstatus=1 order by posting_date asc ".format(
        frappe.db.escape(customer)), as_dict=1)

    return data


def get_sales_invoice(customer):
    
    
    sql = """SELECT name , customer_name  , grand_total , outstanding_amount , posting_date  
                from `tabSales Invoice` tsi  
                where customer = {0} 
                and docstatus=1 
                and outstanding_amount <> 0 
                order by posting_date asc """.format(frappe.db.escape(customer))
    
    data = frappe.db.sql(sql, as_dict=1)

    return data


@frappe.whitelist(allow_guest=True)
def query_code_housing(code=""):

    if not code:
        frappe.throw("El codigo no puede estar vacio")

    exist_housing = frappe.db.exists(
        "Housing", {
            "code": code,
        },
    )

    if exist_housing:
        customer = frappe.db.sql(
            'SELECT tc.name from tabCustomer tc join tabHousing th ON th.owner_customer = tc.name  where th.code ={}'.format(frappe.db.escape(code)))[0]
        balance = get_balance(customer[0])
        print('saldo propietario',balance)
        invoices = get_sales_invoice(customer[0])
        
    else:
        frappe.throw("Propietario no encontrado ")

    frappe.local.response.update({"data": {
        "customer": customer,
        "saldo": balance.saldo_deudor,
        "credito": balance.saldo_credito,
        "invoices" : invoices
    }})

    return build_response("json")


def get_customer(code):
    result = {
        'customer': None,
        'condominium': None
    }

    data = frappe.db.sql('SELECT tc.name  , th.condominium from tabCustomer tc join tabHousing th ON th.owner_customer = tc.name  where th.code ={}'.format(
        frappe.db.escape(code)))

    if data[0]:
        if data[0][0]:
            result = {'customer': data[0][0], 'condominium':  data[0][1]}

    return result


def get_balance(customer):
    sql = """
        SELECT 
            SUM(t.grand_total) AS saldo_deudor,
            SUM(t.base_paid_amount) AS saldo_credito
        FROM (
            SELECT
                ROUND(si.outstanding_amount, 2) AS grand_total,
                0 AS base_paid_amount
            FROM `tabSales Invoice` AS si
            WHERE si.customer = {0} AND docstatus = 1 and si.outstanding_amount <> 0
            UNION ALL
            SELECT
                0 AS grand_total,
                pay.base_paid_amount AS base_paid_amount
            FROM `tabPayment Entry` AS pay
            WHERE pay.party_name = {0} AND pay.docstatus = 1 AND pay.unallocated_amount > 0
        ) t;

    """.format(frappe.db.escape(customer))

    query = frappe.db.sql(sql, as_dict=True)
    if query:
        q = query[0]
        q.saldo_deudor -= q.saldo_credito
        return q
    else: 
        return frappe._dict(saldo_deudor=0, saldo_credito=0)


@frappe.whitelist(allow_guest=True)
def pdf(doctype, name, format=None, doc=None, no_letterhead=0):
    doc = doc or frappe.get_doc(doctype, name)

    html = frappe.get_print(doctype, name, format,
                            doc=doc, no_letterhead=no_letterhead)
    frappe.local.response.filename = "{name}.pdf".format(
        name=name.replace(" ", "-").replace("/", "-")
    )
    frappe.local.response.filecontent = get_pdf(html)
    frappe.local.response.type = "pdf"


@frappe.whitelist(allow_guest=True)
def pdf_2(report_name=None, doctype=None, name=None, doc=None, params=None, as_download=False):
    return get_pdf_backend(report_name=report_name, doctype=doctype, name=name, doc=doc, params=params, as_download=as_download)
