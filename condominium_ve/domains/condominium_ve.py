data = {
	"desktop_icons": ["Condominium", "Housing", "Condominium Sectors"],
	"restricted_roles": ["Condominium Manager", "Condominium User" , "Condominium Guest"],
	"custom_fields": {
		"Sales Invoice": [
				{
					"fieldname": "housing",
					"fieldtype": "Data",
					"label": "Housing",
					"insert_after": "due_date",
					"hidden": 0,
    				"no_copy": 1,
          			"read_only": 1,
				}
			],
	},
}
