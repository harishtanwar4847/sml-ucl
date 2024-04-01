# Copyright (c) 2024, Developers and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from ucl import send_sms_custom
from frappe import _


class Lead(Document):
	
	def before_save(self):
		ucl_setting = frappe.get_single("UCL Settings")
		receiver_list = [self.mobile_number]
		message = ""
		if self.status == "Call Done" and not self.caller_name:
			frappe.throw(_("Please enter the caller name."))
		pre_sanction_count = 0
		post_sanction_count = 0
		if self.id_proof:
			pre_sanction_count+=1
		if self.address_proof:
			pre_sanction_count+=1
		if self.s_v_proof:
			pre_sanction_count+=1
		if self.salary_slips:
			pre_sanction_count+=1
		if self.itr:
			pre_sanction_count+=1
		if self.financials:
			pre_sanction_count+=1
		if self.bank_statements:
			pre_sanction_count+=1
		if self.rc_copy:
			pre_sanction_count+=1
		if self.valid_vehicle_insurance:
			pre_sanction_count+=1
		self.pre_sanction_checklist_count = pre_sanction_count

		if self.status == "Complete Docs Received" and self.pre_sanction_checklist_count<9:
			frappe.throw(_("Please Upload all the Pre Sanction Documents."))

		if self.loan_agreement:
			post_sanction_count+=1
		if self.pdcsspdcs:
			post_sanction_count+=1
		if self.nach_mandate:
			post_sanction_count+=1
		if self.additional_document_asked_by_lender:
			post_sanction_count+=1
		self.post_sanction_checklist_count = post_sanction_count
		if self.status == "Post Sanction Docs" and self.pre_sanction_checklist_count < 4:
			frappe.throw(_("Please Upload all the Post Sanction Documents."))

		if len(self.lender_selection_and_decision)<1 and self.status == "Lender Selection":
			frappe.throw(_("Please select atleast one Lender."))

		if self.status == "Draft":
			sms_notification_doc = frappe.get_doc("UCL SMS Notification", "Lead Draft State")
			message = sms_notification_doc.message.format(lead_name = self.full_name)
		elif self.status == "Open" and self.workflow_state == "Open":
			sms_notification_doc = frappe.get_doc("UCL SMS Notification", "Lead Open State")
			message = sms_notification_doc.message.format(lead_name = self.full_name, lead_id =  self.name)
		elif self.status == "Call Done" and self.caller_name:
			sms_notification_doc = frappe.get_doc("UCL SMS Notification", "Lead Call Done State")
			message = sms_notification_doc.message.format(lead_name = self.full_name, caller_name = self.caller_name, website=ucl_setting.sml_website)
		elif self.status == "Lender Selection" and self.caller_name:
			sms_notification_doc = frappe.get_doc("UCL SMS Notification", "Lead Lender Selection")
			message = sms_notification_doc.message.format(lead_name = self.full_name, lender = "the lender", phone=ucl_setting.sml_contact_number, email=ucl_setting.sml_email_id)
		elif self.status == "Logged In":
			sms_notification_doc = frappe.get_doc("UCL SMS Notification", "Lead Logged In")
			message = sms_notification_doc.message.format(lead_name = self.full_name, lender = "the lender", phone=ucl_setting.sml_contact_number, email=ucl_setting.sml_email_id)
		elif self.status == "Decisioned - Sanctioned":
			sms_notification_doc = frappe.get_doc("UCL SMS Notification", "Lead Decisioned - Sanctioned")
			message = sms_notification_doc.message.format(phone=ucl_setting.sml_contact_number)
		elif self.status == "Decisioned - Rejected":
			sms_notification_doc = frappe.get_doc("UCL SMS Notification", "Lead Decisioned - Rejected")
			message = sms_notification_doc.message.format(lead_name = self.full_name, website=ucl_setting.sml_website)
		elif self.status == "Post Sanction Docs" and self.caller_name:
			sms_notification_doc = frappe.get_doc("UCL SMS Notification", "Lead Post Sanctioned Docs")
			message = sms_notification_doc.message.format(lead_name = self.full_name, phone=ucl_setting.sml_contact_number, email=ucl_setting.sml_email_id)
		elif self.status == "Post Sanction Docs" and self.caller_name:
			sms_notification_doc = frappe.get_doc("UCL SMS Notification", "Lead Partial Docs Received")
			message = sms_notification_doc.message.format(lead_name = self.full_name)
		elif self.status == "Post Sanction Docs" and self.caller_name:
			sms_notification_doc = frappe.get_doc("UCL SMS Notification", "Lead Complete Docs Received")
			message = sms_notification_doc.message.format(lead_name = self.full_name)
		elif self.status == "Post Sanction Docs" and self.caller_name:
			sms_notification_doc = frappe.get_doc("UCL SMS Notification", "Lead Disbursed to Customer")
			message = sms_notification_doc.message.format(lead_name = self.full_name, phone=ucl_setting.sml_contact_number, email=ucl_setting.sml_email_id)
			
		frappe.enqueue(method=send_sms_custom, receiver_list=receiver_list, msg=message, sms_template_id = sms_notification_doc.template_id)

			