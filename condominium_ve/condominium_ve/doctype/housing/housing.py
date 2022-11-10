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
