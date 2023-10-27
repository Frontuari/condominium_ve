import frappe

def after_uninstall():
	custom_fields = ("Purchase Invoice Item-is_single_sector", "Sales Invoice-housing", "Sales Invoice-condominium",
						"Purchase Invoice-condominium", "Purchase Invoice-apply_process_condo", "Purchase Invoice-is_for_condominium")
	
	sql = """
		DELETE FROM `tabCustom Field` WHERE name in {0}
	""".format(str(custom_fields))
	frappe.db.sql(sql)
	
	print("Se han eliminado los siguientes campos personalizados tras la desinstalacion: {0}".format(custom_fields))