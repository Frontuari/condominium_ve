# Copyright (c) 2022, Armando Rojas and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document
from frappe.utils.response import build_response
from datetime import datetime  # from python std library
from frappe.utils import add_to_date
from frappe.core.doctype.communication import email


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
            total = doc.total * (float(house.aliquot) / 100)

            # owner = frappe.get_doc('Customer', house.owner_customer)

            # emails = get_emails(owner)

            sales_invoice = frappe.get_doc(dict(
                doctype="Sales Invoice",
                docstatus=0,
                company=doc_condo.company,
                customer=house.owner_customer,
                posting_date=doc.posting_date,
                due_date=after_days,
                is_return=0,
                disable_rounded_total=0,
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
            sales_invoice.queue_action('submit')

            for fund in doc.funds:
                total_fund = float(fund.amount) * (float(house.aliquot) / 100)
                sales_invoice_2 = frappe.get_doc(dict(
                    doctype="Sales Invoice",
                    docstatus=0,
                    company=doc_condo.company,
                    customer=house.owner_customer,
                    posting_date=doc.posting_date,
                    due_date=after_days,
                    is_return=0,
                    disable_rounded_total=0,
                    items=[
                        dict(
                            item_code='Cuota de Condominio',
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
                    select_print_heading="Recibo de Condominio"
                )).insert()
                sales_invoice_2.queue_action('submit')

            # if len(emails) > 0:
            #    send_email(emails, sales_invoice.name, description='Cuota de Condominio {0} {1} '.format(
            #        get_month(doc.posting_date.month), doc.posting_date.year))

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
            sales_invoice.queue_action('cancel')

        for invoice in doc.condominium_common_expenses_invoices:
            doc_invoice = frappe.get_doc(
                'Purchase Invoice', invoice.invoice)
            doc_invoice.apply_process_condo = 0
            doc_invoice.save(ignore_permissions=True)


def get_emails(owner):
    emails = ""

    results = frappe.db.sql(
        "select email_id  from `tabContact Email` tce where parent like '%{0}' ".format(owner.name))

    for r in results:
        emails = emails + r[0] + ","

    return emails


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
        # customer.email_id


def is_fund(cost_center):
    if cost_center != "Gastos Comunes Variables":
        cc = frappe.get_doc("Cost Center" , cost_center)
        parent_cc = frappe.get_doc("Cost Center" , cc.parent_cost_center)
        return parent_cc.is_reserve
    return 0


@frappe.whitelist()
def get_invoice_condo(condo, date):

    funds = []
    total = 0
    total_per_unit = 0

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


            # invoice.cost_center = invoice.description

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

        # for item in invoice.items:

        #     taxes = 0

        #     if not item.item_tax_template:
        #         item.item_tax_template = " "

        #     if "16" in item.item_tax_template:
        #         taxes = 0.16
        #     elif "8" in item.item_tax_template:
        #         taxes = 0.08

        #     data_item.append({
        #         'supplier':  invoice.supplier,
        #         'amount': item.amount + (item.amount * taxes),
        #         'net': item.amount,
        #         'tax': taxes,
        #         'concept': item.item_name,
        #         'item_code': item.item_code,
        #         'per_unit': item.amount / doc_condo.n_houses_active
        #     })


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
            # for kr in keys_reserve:
            #     if kr in data_cost_center_copy[dd][parent_cost_center]:
            #         fund_total_reserve

            #         if not (kr) in data_cost_center.keys():
            #             fund_total_reserve[kr] = {
            #                 'expense': 0.0
            #             }

            #         fund_total_reserve[kr]['expense'] = fund_total_reserve[kr]['expense'] + data_cost_center_copy[dd]['amount']

            # parent_cost_center

    for fund in doc_condo.reserve:
        # fund_total_reserve[kr]['expense']
        funds.append({'concept': fund.description, 'amount': fund.amount,
                     'amount_per_unit': fund.amount / doc_condo.n_houses_active,  'account': fund.account})
        total = total + fund.amount
        total_per_unit = total_per_unit + fund.amount / doc_condo.n_houses_active

    frappe.local.response.update({"data": {
        'invoices': data_invoice,
        'detail': data_cost_center,
        'detail_2': data_item,
        'active_units': active_units,
        'total': total,
        'total_per_unit': total_per_unit,
        'funds': funds,
        'expense_funds': data_cost_center_fund
    }})

    return build_response("json")
