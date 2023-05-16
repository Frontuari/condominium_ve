# Copyright (c) 2022, Armando Rojas  and contributors
# For license information, please see license.txt

from custom_ve.custom_ve.doctype.environment_variables.environment_variables import get_env
import requests
import frappe
from frappe import _
from frappe.website.website_generator import WebsiteGenerator
from erpnext.accounts.doctype.sales_invoice.sales_invoice import get_bank_cash_account
from erpnext.accounts.doctype.payment_entry.payment_entry import get_account_details, get_party_details


class Manualpayment(WebsiteGenerator):

    def before_save(self):
        self.owner = "Guest"
    
    def after_save(self):
        self.owner = "Guest"
        self.save()

    def on_submit(self):
        self.create_entry_payment()

    def after_insert(self):
        # self.create_entry_payment()
        pass

    def on_change(self):
        pass
        # self.create_entry_payment()

    def create_entry_payment(self):
        # doc = self.get_doc_before_save()
        doc = self

        #payment_amount = doc.amount

        doc.mode_of_payment = self.get_type_bank(doc.mode_of_payment)
        #company = frappe.defaults.get_user_default("Company")

        customer = frappe.get_doc("Customer", doc.customer)
        mop_account = get_bank_cash_account(
            doc.mode_of_payment, frappe.defaults.get_user_default("Company"))

        acc_detail = get_account_details(
            mop_account['account'], doc.posting_date)
        party_detail = get_party_details(frappe.defaults.get_user_default(
            "Company"), "Customer", doc.customer, doc.posting_date)

        payment = frappe.get_doc(dict(
            doctype="Payment Entry",
            posting_date=doc.posting_date,
            mode_of_payment=doc.mode_of_payment,
            payment_type="Receive",
            party_type="Customer",
            party=doc.customer,
            party_name=customer.customer_name,
            paid_to=mop_account['account'],
            paid_to_account_currency=acc_detail['account_currency'],
            paid_from=party_detail['party_account'],
            paid_from_account_currency=party_detail['party_account_currency'],
            paid_amount=doc.amount,
            received_amount=doc.amount,
            reference_no=doc.reference,
            reference_date=doc.posting_date,
            


        )).insert(ignore_permissions=True, ignore_mandatory=True)
        #references=ord
        payload = {
            "doctype":"Payment Entry",
            "docname":payment.name,
            "file_url":self.voucher,
            "is_private": "NaN",
            "folder": "Home/Attachments"
        }

        self.upload_file(payload)
        self.payment = payment.name
        self.save()

        link_payment = "<b><a href='/app/payment-entry/{0}'>{0}</a></b>".format(payment.name)
        frappe.msgprint(_("Your payment receipt {0} has been created successfully, please verify and validate it").format(link_payment))

    def upload_file(self , payload):
        url_api = get_env('URL_API')
        api_key = get_env('API_KEY')

        method = "/method/upload_file"
        url = url_api + method
        headers = {
            'Authorization': "Basic %s" % api_key
        }

        return requests.post(url, payload , headers=headers)

    def get_type_bank(self, mode):
        modes = {
            "Transferencia Bancaria": "Transferencia Bancaria"
        }
        return modes[mode]
