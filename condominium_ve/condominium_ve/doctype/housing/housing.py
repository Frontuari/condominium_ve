# Copyright (c) 2022, Armando Rojas and contributors
# For license information, please see license.txt

from numpy import number
import frappe
import random
import string
from frappe.model.document import Document
from frappe.utils.response import build_response

class Housing(Document):
	def validate(self):
		
		condominium_doc = frappe.get_doc('Condominium', self.condominium)

		if not self.inserted:
			# actualiza el campo inserted en el documento de housing
			
			self.inserted = 1
			#self.save()
			condominium_doc.n_houses += 1
			if self.active:
				condominium_doc.n_houses_active += 1
			
		else:
			if self.active:
				condominium_doc.n_houses_active += 1
			else:
				condominium_doc.n_houses_active -= 1
		condominium_doc.save()
	
	def on_trash(self):
		is_house_active = frappe.db.get_value('Housing', self.name, 'active')
		condominium_doc = frappe.get_doc('Condominium', self.condominium)
		condominium_doc.n_houses -= 1
		if is_house_active:
			condominium_doc.n_houses_active -= 1
		
		condominium_doc.save()

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
"""
@frappe.whitelist()
def update_condominium_houses(house, condominium, active, inserted):
	active = int(active)
	inserted = int(inserted)
	condominium_doc = frappe.get_doc('Condominium', condominium)

	if not inserted:
		# actualiza el campo inserted en el documento de housing
		house_doc = frappe.get_doc('Housing', house)
		house_doc.inserted = 1
		house_doc.save()
		condominium_doc.n_houses += 1
		if active:
			condominium_doc.n_houses_active += 1
		
	else:
		if active:
			condominium_doc.n_houses_active += 1
		else:
			condominium_doc.n_houses_active -= 1
	condominium_doc.save()
"""
