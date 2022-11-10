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
        "Purchase Invoice":{
            "label": "Is For Condominium",
            "default": "1",
            "fieldname": "is_for_condominium",
            "insert_after": "apply_tds",
            "length": 0,
            "fieldtype": "Check",
            "precision": "",
            "hide_seconds": 0,
            "hide_days": 0,
            "fetch_if_empty": 0,
            "collapsible": 0,
            "non_negative": 0,
            "reqd": 0,
            "unique": 0,
            "read_only": 0,
            "ignore_user_permissions": 0,
            "hidden": 0,
            "print_hide": 0,
            "print_hide_if_no_value": 0,
            "no_copy": 0,
            "allow_on_submit": 0,
            "in_list_view": 0,
            "in_standard_filter": 0,
            "in_global_search": 0,
            "in_preview": 0,
            "bold": 0,
            "report_hide": 0,
            "search_index": 0,
            "allow_in_quick_entry": 0,
            "ignore_xss_filter": 0,
            "translatable": 0,
            "hide_border": 0,
        }
    },

    "properties": [
        {
            "name": "Purchase Invoice-cost_center-mandatory_depends_on",
            "doctype_or_field": "DocField",
            "doc_type": "Purchase Invoice",
                        "fieldname": "cost_center",
                        "property": "mandatory_depends_on",
                        "property_type": "Data",
                        "value": "eval:doc.is_for_condominium == 1",
                        "doctype": "Purchase Invoice",
        },
        {
            "name": "Purchase Invoice-remarks-fetch_from",
            "doc_type": "Purchase Invoice",
            "fieldname": "remarks",
                        "property": "fetch_from",
                        "property_type": "Small Text",
                        "value": "cost_center.cost_center_name",
                        "doctype": "Purchase Invoice"
        },
        {
            "name": "Purchase Invoice-remarks-ignore_user_permissions",
            "doctype_or_field": "DocField",
            "doc_type": "Purchase Invoice",
            "fieldname": "is_for_condominium",
                    "property": "ignore_user_permissions",
                    "property_type": "Check",
                    "value": "1",
                    "doctype": "Purchase Invoice"
        }
    ]
}
