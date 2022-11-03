data = {
    "desktop_icons": ["Condominium", "Housing", "Condominium Sectors"],
    "restricted_roles": ["Condominium Manager", "Condominium User", "Condominium Guest"],
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

    "property_setters": [
        {
            "name": "Purchase Invoice-cost_center-mandatory_depends_on",
            "doctype_or_field": "DocField",
            "doc_type": "Purchase Invoice",
                        "field_name": "cost_center",
                        "property": "mandatory_depends_on",
                        "property_type": "Data",
                        "value": "eval:doc.is_for_condominium == 1",
                        "doctype": "Property Setter",
        },
        {
            "name": "Purchase Invoice-remarks-fetch_from",
            "doc_type": "Purchase Invoice",
            "field_name": "remarks",
                        "property": "fetch_from",
                        "property_type": "Small Text",
                        "value": "cost_center.name",
                        "doctype": "Property Setter"
        },
        {
            "name": "Purchase Invoice-remarks-ignore_user_permissions",
            "doctype_or_field": "DocField",
            "doc_type": "Purchase Invoice",
            "field_name": "remarks",
                    "property": "ignore_user_permissions",
                    "property_type": "Check",
                    "value": "1",
                    "doctype": "Property Setter"
        }
    ]
}
