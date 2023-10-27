import frappe

def before_uninstall():
	print("* Eliminado campos personalizados...")
	custom_fields = ["Purchase Invoice Item-is_single_sector", "Sales Invoice-housing", "Sales Invoice-condominium",
						"Purchase Invoice-condominium", "Purchase Invoice-apply_process_condo", "Purchase Invoice-is_for_condominium"]
	
	for cf in custom_fields:
		sql = """
			DELETE FROM `tabCustom Field` WHERE name = '{0}'
		""".format(cf)
		frappe.db.sql(sql)
	
	