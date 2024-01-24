from __future__ import unicode_literals
import frappe


def execute():
    role_list = [
        "Partner",
        "Partner Associate",
        "CBO",
        "SM",
        "FOS",
        "Ops",
        "Finance",
        "Auditor",
        "Employee"
    ]
    for role in role_list:
        if frappe.db.exists("Role", role) != role:
            doc = frappe.new_doc("Role")
            doc.role_name = role
            doc.insert()

    frappe.db.commit()