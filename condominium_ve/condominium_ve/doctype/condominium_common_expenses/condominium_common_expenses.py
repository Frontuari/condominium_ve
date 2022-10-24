# Copyright (c) 2022, Armando Rojas and contributors
# For license information, please see license.txt
from attr import field
import frappe
from frappe.model.document import Document
from frappe.utils.response import build_response
from datetime import datetime  # from python std library
from frappe.utils import add_to_date


class CondominiumCommonExpenses(Document):
    def on_submit(self):
        doc = self.get_doc_before_save()
        doc_condo = frappe.get_doc('Condominium', doc.condominium)

        housings = frappe.db.get_list("Housing", fields=['*'], filters={
            'active': 1,
            'condominium': doc_condo.name,
        })

        after_days = add_to_date(doc.posting_date, days=3, as_string=True)

        for house in housings:
            total = doc.total * (house.aliquot / 100)
            sales_invoice = frappe.get_doc(dict(
                doctype="Sales Invoice",
                docstatus=0,
                customer=house.owner_customer,
                posting_date=doc.posting_date,
                due_date=after_days,
                is_return=0,
                disable_rounded_total=0,
                items=[
                    dict(
                        itemcode='Cuota de Condominio {0} {1} '.format(
                            get_month(doc.posting_date.month), doc.posting_date.year),
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
                        income_account="Ventas - D"
                    )
                ],
                gc_condo=doc.name
            )).insert()
            sales_invoice.submit()

            for invoice in doc.condominium_common_expenses_invoices:
                doc_invoice = frappe.get_doc(
                    'Purchase Invoice', invoice.invoice)
                doc_invoice.apply_process_condo = 1
                doc_invoice.save(ignore_permissions=True)

    def on_cancel(self):
        doc = self.get_doc_before_save()

        sales_invoices = frappe.db.get_list("Sales Invoice", fields=['*'], filters={
            'gc_condo': doc.name,
        })

        for d in sales_invoices:
            sales_invoice = frappe.get_doc('Sales Invoice', d.name)
            sales_invoice.cancel()

        for invoice in doc.condominium_common_expenses_invoices:
                doc_invoice = frappe.get_doc(
                    'Purchase Invoice', invoice.invoice)
                doc_invoice.apply_process_condo = 0
                doc_invoice.save(ignore_permissions=True)


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
def get_invoice_condo(condo, date):

    purchase_invoice_list = frappe.db.get_list("Purchase Invoice",  filters={

        "is_for_condominium": 1,
        "apply_process_condo": 0,
        "docstatus": 1,
        "is_return": 0,
        "condominium": condo,
        "status": {"in": ["Overdue", "Unpaid", "Partly Paid", "Paid"]}
    }, order_by='cost_center ASC')

    doc_condo = frappe.get_doc('Condominium', condo)

    data_invoice = []
    data_item = []
    data_cost_center = {}

    total = 0
    total_per_unit = 0
    active_units = doc_condo.n_houses_active

    for purchase_invoice_data in purchase_invoice_list:

        invoice = frappe.get_doc(
            "Purchase Invoice", purchase_invoice_data.name)

        if not invoice.cost_center:
            invoice.cost_center = "Gastos de Condominio"
        else:
            cost_center_doc = frappe.get_doc(
                'Cost Center', invoice.cost_center)
            invoice.cost_center = cost_center_doc.cost_center_name

        if not invoice.cost_center in data_cost_center.keys():
            data_cost_center[invoice.cost_center] = {
                'amount': 0,
                'concept': invoice.cost_center,
                'per_unit': 0
            }

        element = data_cost_center[invoice.cost_center]

        element['amount'] = element['amount'] + invoice.total
        element['per_unit'] = element['per_unit'] + \
            (invoice.total / doc_condo.n_houses_active)

        data_cost_center[invoice.cost_center] = element

        for item in invoice.items:

            taxes = 0

            if not item.item_tax_template:
                item.item_tax_template = " "

            if "16" in item.item_tax_template:
                taxes = 0.16
            elif "8" in item.item_tax_template:
                taxes = 0.08

            data_item.append({
                'supplier':  invoice.supplier,
                'amount': item.amount + (item.amount * taxes),
                'net': item.amount,
                'tax': taxes,
                'concept': item.item_name,
                'item_code': item.item_code,
                'per_unit': item.amount / doc_condo.n_houses_active
            })

        data_invoice.append({
            'date': invoice.posting_date,
            'invoice': invoice.name,
            'supplier': invoice.supplier,
            'amount': invoice.total,
        })

        total = total + invoice.total
        total_per_unit = total_per_unit + \
            (invoice.total / doc_condo.n_houses_active)

    data_cost_center_copy = data_cost_center
    data_cost_center = []

    for dd in data_cost_center_copy.keys():
        data_cost_center.append(data_cost_center_copy[dd])

    frappe.local.response.update({"data": {
        'invoices': data_invoice,
        'detail': data_cost_center,
        'detail_2': data_item,
        'active_units': active_units,
        'total': total,
        'total_per_unit': total_per_unit
    }})

    return build_response("json")
