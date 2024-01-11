import frappe
import ucl
from .rules import *
from validator import validate as validate_


def validate(data, rules):
	valid, valid_data, errors = validate_(data, rules, return_info=True)

	if not valid:
		from ucl.exceptions import ValidationException
		raise ValidationException(errors=errors)

	return valid_data

def validate_http_method(*methods):
	if frappe.request:
		if frappe.request.method.upper() not in [method.upper() for method in methods]:
			from ucl.exceptions import MethodNotAllowedException
			raise MethodNotAllowedException