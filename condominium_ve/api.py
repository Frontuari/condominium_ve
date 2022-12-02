
from custom_reports.utils.print_format import get_pdf
import frappe
from frappe.utils.response import build_response
from custom_reports.report_design.doctype.report_bro.report_bro import get_pdf_backend


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

    else:
        frappe.throw("Propietario no encontrado ")

    frappe.local.response.update({"data": {
        "balance": balance,
        "cc_condo": cce_list,
        "payments": payments,
        "customer": customer
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
        saldo = get_balance(customer[0])[0][0]
    else:
        frappe.throw("Propietario no encontrado ")

    frappe.local.response.update({"data": {
        "customer": customer,
        "saldo": saldo
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
            select sum(t.total)
            from (
            Select
            ROUND(si.grand_total,2) as total
            from `tabSales Invoice` as si
            where si.customer =  {0} and  docstatus = 1
            union all
            Select
                (pay.base_paid_amount *-1) as total
            from `tabPayment Entry` as pay
            where pay.party_name =  {0}  and pay.docstatus = 1
            )t
    """.format(frappe.db.escape(customer))

    return frappe.db.sql(sql)


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
