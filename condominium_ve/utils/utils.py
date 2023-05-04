import frappe
import os
from datetime import datetime

def add_log(e, origen, description):
    tiempo = datetime.now()
    tiempo = tiempo.strftime("%d-%m-%Y %H:%M")

    app_path = frappe.get_app_path('condominium_ve')

    if not os.path.exists(app_path+'/log'):
          os.mkdir(app_path+'/log')
    
    with open(app_path+'/log/error.log', 'a') as f:
            f.write('\n{0} {1} - {2}: {3}'.format(tiempo, origen, description, e))