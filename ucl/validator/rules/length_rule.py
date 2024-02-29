import frappe
from validator.rules import Rule

class LengthRule(Rule):
	def __init__(self, length, message=None):
		Rule.__init__(self)
		self.length = length
		self.message = message or frappe._('Should be atleast {} in length.'.format(length))

	def check(self, arg):
		if len(str(arg)) != self.length:
			self.set_error(self.message.format(arg=arg))
			return False

		return True