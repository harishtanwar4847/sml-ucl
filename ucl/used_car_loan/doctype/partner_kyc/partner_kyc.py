# Copyright (c) 2024, Developers and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PartnerKYC(Document):
    # pass
	
	def before_save(self):
		if self.status in ["Rejected by SML", "Rejected by Partner"]:
			partner_name = frappe.db.sql("select name from `tabPartner` where partner_kyc = '{name}'".format(name = self.name))
			if partner_name:
				partner = frappe.get_doc("Partner", partner_name[0][0])
				partner.partner_kyc = ""
				partner.save(ignore_permissions=True)
				frappe.db.commit()