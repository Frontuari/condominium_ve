# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

from pyrsistent import thaw

import frappe
from frappe import _, throw
from frappe.utils import now
from frappe.utils.response import build_response

sitemap = 1


def get_context(context):
    doc = frappe.get_doc("Contact Us Settings", "Contact Us Settings")

    if doc.query_options:
        query_options = [opt.strip() for opt in doc.query_options.replace(
            ",", "\n").split("\n") if opt]
    else:
        query_options = ["Sales", "Support", "General"]

    out = {"query_options": query_options, "parents": [
        {"name": _("Home"), "route": "/"}]}
    out.update(doc.as_dict())

    return out


max_communications_per_hour = 1000


@frappe.whitelist(allow_guest=True)
def send_message(subject="Website Query", message="", sender=""):
    if not message:
        frappe.response["message"] = "Please write something"
        return

    if not sender:
        frappe.response["message"] = "Email Address Required"
        return

    # guest method, cap max writes per hour
    if (
            frappe.db.sql(
                """select count(*) from `tabCommunication`
		where `sent_or_received`="Received"
		and TIMEDIFF(%s, modified) < '01:00:00'""",
                now(),
            )[0][0]
            > max_communications_per_hour
    ):
        frappe.response[
            "message"
        ] = "Sorry: we believe we have received an unreasonably high number of requests of this kind. Please try later"
        return

    # send email
    forward_to_email = frappe.db.get_value(
        "Contact Us Settings", None, "forward_to_email")
    if forward_to_email:
        frappe.sendmail(recipients=forward_to_email,
                        sender=sender, content=message, subject=subject)

    # add to to-do ?
    frappe.get_doc(
        dict(
            doctype="Communication",
            sender=sender,
            subject=_("New Message from Website Contact Page"),
            sent_or_received="Received",
            content=message,
            status="Open",
        )
    ).insert(ignore_permissions=True)

    return "okay"


@frappe.whitelist(allow_guest=True)
def query_code(code=""):

    if not code:
        frappe.throw("Error al consultar el codigo")

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
                                  "condominium":  housing.condominium}, fields=["*"])

        for cce in cce_list:
            sgg_condo_list = frappe.get_list("Sales Invoice", filters={ "docstatus" : "1" ,
                                            "gc_condo":  cce.name, "customer":  customer_name , "status":{"in": ["Unpaid and Discounted" , "Submitted" , "Paid" , "  Partly Paid" , "Overdue" , "Overdue and Discounted", "Partly Paid and Discounted"]  }   }, fields=["*"])
            for ssg in sgg_condo_list:
                sales_invoices.append(ssg)

                ref_payment = frappe.get_list("Payment Entry Reference",    filters={
                                             "reference_name": ssg.name, "reference_doctype": "Sales Invoice"}, fields=["*"])
                for rp in ref_payment:
                    payments.append(rp)

        customer = frappe.get_doc("Customer",  customer_name)

    frappe.local.response.update({"data": {
        "sales_invoices": sales_invoices,
        "cc_condo": cce_list,
        "payments": payments,
        "customer": customer
    }})

    return build_response("json")
