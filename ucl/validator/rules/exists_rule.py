import frappe
from validator.rules import Rule

class ExistsRule(Rule):
	def __init__(self, doctype, fields, message=None):
		Rule.__init__(self)
		self.doctype = doctype
		self.fields = fields
		self.message = message

	def check(self, arg):
		filters = {
			'doctype': self.doctype
		}
		for field in self.fields.split(','):
			filters[field] = arg
		
		if frappe.db.exists(filters):
			if self.message:
				self.set_error(self.message.format(arg=arg))
			return False

		return True