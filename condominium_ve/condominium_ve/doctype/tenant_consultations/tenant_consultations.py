# Copyright (c) 2022, Armando Rojas and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.response import build_response


class TenantConsultations(Document):
    pass


@frappe.whitelist()
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
        housing = frappe.get_list(
            "Housing", filters={"code": code}, fields=["*"])[0]
        customer_name = housing.owner_customer
        sales_invoices = []

        cce_list = frappe.get_list("Condominium Common Expenses", filters={
            "condominium":  housing.condominium , "docstatus": "1" }, fields=["*"])

        for cce in cce_list:
            sgg_condo_list = frappe.get_list("Sales Invoice", filters={"docstatus": "1",
                                                                       "gc_condo":  cce.name, "customer":  customer_name, "status": {"in": ["Unpaid and Discounted", "Submitted", "Paid", "  Partly Paid", "Overdue", "Overdue and Discounted", "Partly Paid and Discounted"]}}, fields=["*"])
            for ssg in sgg_condo_list:
                sales_invoices.append(ssg)

                ref_payment = frappe.get_list("Payment Entry Reference",    filters={
                    "reference_name": ssg.name, "reference_doctype": "Sales Invoice"}, fields=["*"])
                for rp in ref_payment:
                    payments.append(rp)

        customer = frappe.get_doc("Customer",  customer_name)
    else:
        frappe.throw("Propietario no encontrado ")

    frappe.local.response.update({"data": {
        "sales_invoices": sales_invoices,
        "cc_condo": cce_list,
        "payments": payments,
        "customer": customer
    }})

    return build_response("json")
