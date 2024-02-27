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
    list = []
    for i in frappe.get_list("Role"):
        list.append(i['name'])
    for role in role_list:
        if role not in list:
            doc = frappe.new_doc("Role")
            doc.role_name = role
            doc.insert()

    frappe.db.commit()