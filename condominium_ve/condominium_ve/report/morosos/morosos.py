# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt


import frappe
from frappe import _, scrub
from frappe.utils import cint, flt
from six import iteritems

from erpnext.accounts.party import get_partywise_advanced_payment_amount
from erpnext.accounts.report.accounts_receivable.accounts_receivable import ReceivablePayableReport


def execute(filters=None):
    args = {
        "party_type": "Customer",
        "naming_by": ["Selling Settings", "cust_master_name"],
        "range1" : "30", 
        "range2" : "60", 
        "range3" : "80", 
        "range4" : "90", 
    }

    return AccountsReceivableSummary(filters).run(args)


class AccountsReceivableSummary(ReceivablePayableReport):
    def run(self, args):
        self.party_type = args.get("party_type")
        self.party_naming_by = frappe.db.get_value(
            args.get("naming_by")[0], None, args.get("naming_by")[1]
        )
        self.get_columns()
        self.get_data(args)

        return self.columns, self.data

    def get_data(self, args):
        self.data = []

        self.receivables = ReceivablePayableReport(self.filters).run(args)[1]

        self.get_party_total(args)

        party_advance_amount = (
            get_partywise_advanced_payment_amount(
                self.party_type,
                self.filters.report_date,
                self.filters.show_future_payments,
                self.filters.company,
            )
            or {}
        )

        if self.filters.show_gl_balance:
            gl_balance_map = get_gl_balance(self.filters.report_date)

        for party, party_dict in iteritems(self.party_total):
            if party_dict.outstanding == 0:
                continue

            row = frappe._dict()

            row.party = party
            row['housing'] = self.get_number_house(row.party)
            
            row['months'] = self.get_number_months(row.housing , self.filters.report_date)

            if self.party_naming_by == "Naming Series":
                row.party_name = frappe.get_cached_value(
                    self.party_type, party, scrub(self.party_type) + "_name"
                )

            row.update(party_dict)

            # Advance against party
            row.advance = party_advance_amount.get(party, 0)

            # In AR/AP, advance shown in paid columns,
            # but in summary report advance shown in separate column
            row.paid -= row.advance

            if self.filters.show_gl_balance:
                row.gl_balance = gl_balance_map.get(party)
                row.diff = flt(row.outstanding) - flt(row.gl_balance)

            self.data.append(row)

        self.group_data_by_sector()
    
    def get_number_house(self, customer):
        data = ''
        housings = frappe.db.sql(
            "select name from tabHousing th where owner_customer = '{0}'  ".format(customer))

        for housing in housings:
            data = data + housing[0]
        return data

    def get_number_months(self, housing, report_date):
        count_sales_invoice = frappe.db.sql(
            "select coalesce((period_diff((SELECT DATE_FORMAT( '{1}','%Y%m') ),min(DATE_FORMAT(due_date,'%Y%m')))),0) from `tabSales Invoice` tsi where gc_condo is not null  and housing='{0}' and  docstatus=1 and status <> 'Paid' and due_date<=(SELECT DATE_ADD(CAST(DATE_FORMAT( '{1}','%Y-%m-01') AS DATE),INTERVAL -1 DAY)) ".format(housing,report_date))
        
        if not count_sales_invoice:
            return 0
        else:  
            return count_sales_invoice[0][0]

    def get_party_total(self, args):
        self.party_total = frappe._dict()

        for d in self.receivables:
            self.init_party_total(d)

            # Add all amount columns
            for k in list(self.party_total[d.party]):
                if k not in ["currency", "sales_person"]:

                    self.party_total[d.party][k] += d.get(k, 0.0)

            # set territory, customer_group, sales person etc
            self.set_party_details(d)

    def init_party_total(self, row):
        self.party_total.setdefault(
            row.party,
            frappe._dict(
                {
                    "invoiced": 0.0,
                    "paid": 0.0,
                    "credit_note": 0.0,
                    "outstanding": 0.0,
                    "range1": 0.0,
                    "range2": 0.0,
                    "range3": 0.0,
                    "range4": 0.0,
                    "range5": 0.0,
                    "total_due": 0.0,
                    "sales_person": [],
                }
            ),
        )

    def set_party_details(self, row):
        self.party_total[row.party].currency = row.currency

        for key in ("territory", "customer_group", "supplier_group"):
            if row.get(key):
                self.party_total[row.party][key] = row.get(key)

        if row.sales_person:
            self.party_total[row.party].sales_person.append(row.sales_person)

    def get_columns(self):
        self.columns = []
        self.add_column(
            label=_(self.party_type),
            fieldname="party",
            fieldtype="Link",
            options=self.party_type,
            width=300,
        )
        self.add_column(label=_("Housing"),
                        fieldname="housing",
                        fieldtype="Link",
                        width=80,
                        options='Housing')
        
        
        self.add_column(label=_("Meses"),
                        fieldname="months",
                        fieldtype="Data",
                        width=80)
        
        

        if self.party_naming_by == "Naming Series":
            self.add_column(_("{0} Name").format(
                self.party_type), fieldname="party_name", fieldtype="Data")

        credit_debit_label = "Credit Note" if self.party_type == "Customer" else "Debit Note"

        # self.add_column(_("Advance Amount"), fieldname="advance")
        # self.add_column(_("Invoiced Amount"), fieldname="invoiced")
        # self.add_column(_("Paid Amount"), fieldname="paid")
        # self.add_column(_(credit_debit_label), fieldname="credit_note")
        self.add_column(_("Outstanding Amount"), fieldname="outstanding")

        # if self.filters.show_gl_balance:
        #	self.add_column(_("GL Balance"), fieldname="gl_balance")
        #	self.add_column(_("Difference"), fieldname="diff")

        # self.setup_ageing_columns()

        if self.party_type == "Customer":
            #self.add_column(
            #    label=_("Territory"), fieldname="territory", fieldtype="Link", options="Territory"
            #)
            self.add_column(
                label=_("Customer Group"),
                fieldname="customer_group",
                fieldtype="Link",
                options="Customer Group",
            )
            # if self.filters.show_sales_person:
            #	self.add_column(label=_("Sales Person"), fieldname="sales_person", fieldtype="Data")
        else:
            self.add_column(
                label=_("Supplier Group"),
                fieldname="supplier_group",
                fieldtype="Link",
                options="Supplier Group",
            )

        self.add_column(
            label=_("Currency"), fieldname="currency", fieldtype="Link", options="Currency", width=80
        )

    def group_data_by_sector(self):
        group = {}
        for data in self.data:
            territory = data['territory']
            # elimino el territorio para no repetirlo en el formato de impresion
            del data['territory']
            
            if territory not in group:
                group[territory] = []#{'party': data.territory, 'indent': 0}]
            
            
            data.indent = 1
            group[territory].append(data)
        
        # sort data
        data_formated = []
        for key in group:
            sorted_data = sorted(group[key], key=lambda x: x['housing'])
            data_formated += [{'party': key, 'territory': key,'indent': 0}] + sorted_data

        self.data = data_formated


def get_gl_balance(report_date):
    return frappe._dict(
        frappe.db.get_all(
            "GL Entry",
            fields=["party", "sum(debit -  credit)"],
            filters={"posting_date": (
                "<=", report_date), "is_cancelled": 0},
            group_by="party",
            as_list=1,
        )
    )
