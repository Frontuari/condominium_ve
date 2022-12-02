import frappe


def validate_payment():

    dd = frappe.get_list("Manual payment",  filters={"docstatus": 0})

    # for d in docs:
    for d in dd:
        mp = frappe.get_doc("Manual payment", d.name)
        mp.submit()


def validate_sales_invoices():

    dd = frappe.get_list("Sales Invoice",  filters=[  [ 'gc_condo' , '!=', '']  , ['docstatus' , '=' , '0']] )
    # for d in docs:
    for d in dd:
        try:
            mp = frappe.get_doc("Sales Invoice", d.name)
            mp.submit()
        except print(0):
            pass
