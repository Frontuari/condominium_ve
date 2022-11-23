import frappe


def validate_payment():

    dd = frappe.get_list("Manual payment",  filters={"docstatus": 0})

    # for d in docs:
    for d in dd:
        mp = frappe.get_doc("Manual payment", d.name)
        mp.submit()

