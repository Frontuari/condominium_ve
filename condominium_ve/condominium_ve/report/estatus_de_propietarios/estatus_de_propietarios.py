# Copyright (c) 2015, Datacomm and Contributors and contributors
# For license information, please see license.txt


import frappe
from frappe import _, scrub
from frappe.utils import cint, flt
from six import iteritems
from datetime import timedelta
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
        "balance_type": filters.balance_type
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

        houses_in_data = []
        for party, party_dict in iteritems(self.party_total):
            if (self.filters.territory and  party_dict.territory != self.filters.territory) \
                or not filter_estatus(args["balance_type"], party_dict.outstanding):
                continue
            
            row = frappe._dict()

            row.party = party
            row['housing'] = self.get_number_house(row.party)
            row['months'] = self.get_number_months(row.housing , self.filters.report_date)

            if row.housing not in houses_in_data:
                houses_in_data.append(row.housing)

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
        
        self.add_houses_with_zero(houses_in_data)

        self.group_data_by_sector(args)
    
    def get_number_house(self, customer):
        data = ''
        housings = frappe.db.sql(
            "select name from tabHousing th where owner_customer = '{0}'  ".format(customer))

        for housing in housings:
            data = data + housing[0]
        return data

    def get_number_months(self, housing, report_date):
        # esta funcion se cambio para que retornase los dias entre dos fechas en lugar de los meses
        count_sales_invoice = frappe.db.sql(
            """
                SELECT 
                    DATEDIFF('{1}', due_date) AS diferencia_dias 
                FROM `tabSales Invoice` tsi
                WHERE gc_condo IS NOT NULL  
                    AND housing = '{0}' 
                    AND docstatus = 1 
                    AND status <> 'Paid' 
                    AND due_date < '{1}' ;


            """.format(housing,report_date)
        )
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
        
        
        self.add_column(label=_("Due Days"),
                        fieldname="months",
                        fieldtype="Data",
                        width=80)
        
        

        if self.party_naming_by == "Naming Series":
            self.add_column(_("{0} Name").format(
                self.party_type), fieldname="party_name", fieldtype="Data")

        credit_debit_label = "Credit Note" if self.party_type == "Customer" else "Debit Note"

        self.add_column(_("Outstanding Amount"), fieldname="outstanding")

        if self.party_type == "Customer":
            self.add_column(
                label=_("Customer Group"),
                fieldname="customer_group",
                fieldtype="Link",
                options="Customer Group",
            )
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

    def add_houses_with_zero(self, houses):
        if filter_estatus(self.filters.balance_type, 0):
            currency = frappe.db.get_value("Company", self.filters.company, "default_currency")
            cond = ""
            if self.filters.territory:
                cond += " where h.sector = '{0}'".format(self.filters.territory)
            sql = """
                select h.owner_customer as party, 
                    h.housing,
                    h.sector as territory,
                    0 as months,
                    0 as outstanding,
                    c.customer_group,
                    '{1}' as currency

                from `tabHousing` h
                join `tabCustomer` c on c.name = h.owner_customer
                {0}
            """.format(cond, currency)
            query = frappe.db.sql(sql, as_dict=True)
            if query:
                result = [q for q in query if q.housing not in houses]
                self.data += result

    def group_data_by_sector(self, args):
        group = {}
        for data in self.data:
            skip = not data['housing']
            if skip:
                continue
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
            
            total = 0
            # total row por sector
            for r in sorted_data:
                total += r['outstanding']
            data_formated += [{'party': key, 'territory': key,'indent': 0}] + sorted_data
            data_formated += [{'party': 'Total', 'indent': 1, 'outstanding': total}]
            
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


def filter_estatus(request_estatus, balance):
    if request_estatus == "Con deuda" and balance > 0:
        return True
    elif request_estatus == "Sin deuda" and balance == 0:
        return True
    elif request_estatus == "Saldo a favor" and balance < 0:
        return True
    elif not request_estatus or request_estatus == "":
        return True
    
    return False