# Copyright (c) 2022, Armando Rojas and contributors
# For license information, please see license.txt

from numpy import number
import frappe
import random
import string
from frappe.model.document import Document
from frappe.utils.response import build_response

class Housing(Document):
	pass

def get_random_string(length):
    letters = string.ascii_uppercase
    letters = letters + string.digits
    result_str = ''.join(random.choice(letters) for i in range(length))
	
    return result_str

@frappe.whitelist()
def generate_code():

	control = True
	while control:
		code = get_random_string(10)
		control = frappe.db.exists("Housing",{"code": code})

	frappe.local.response.update({"data": {  'code': code  } })

	return build_response("json")

@frappe.whitelist()
def update_condominium_houses(condominium, active, inserted=0):
	print('active: ',active, type(active), '\ncondominium: ',condominium, type(condominium), '\ninserted: ', inserted, type(inserted))
	active = int(active)
	inserted = int(inserted)
	print('active: ',active, type(active), '\ncondominium: ',condominium, type(condominium), '\ninserted: ', inserted, type(inserted))
	condominium_doc = frappe.get_doc('Condominium', condominium)
	if inserted:
		condominium_doc.n_houses += 1
		if active:
			condominium_doc.n_houses_active += 1
	else:
		if active:
			condominium_doc.n_houses_active += 1
		else:
			condominium_doc.n_houses_active -= 1
	condominium_doc.save()
