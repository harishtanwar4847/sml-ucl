import frappe
import json
from frappe import _
from datetime import datetime, timedelta
import ucl
import re
from .exceptions import *

@frappe.whitelist(allow_guest=True)
def save_lead_details(**kwargs):
    try:
        ucl.validate_http_method("POST")
        # user = ucl.__user()
        # partner = ucl.__partner(user.name)

        data = ucl.validate(
            kwargs,{
            "sub_product": "",
            "source": ["required"],
            "partner_code": "",
            "mobile_number": ["required"],
            "pan_number": ["required"],
            "first_name": ["required"],
            "middle_name": "",
            "last_name": "",
            "applicant_name": ["required"],
            "gender": ["required"],
            "dob": ["required"],
            "line_1": ["required"],
            "line_2": ["required"],
            "street": ["required"],
            "zip": ["required"],
            "city": ["required"],
            "state": ["required"],
            "country": ["required"],
            "address": ["required"],
            "email_id": ["required"],
            "aadhar": ["required"],
            "occupation_type": ["required"],
            "net_take_home_salary": "",
            "profit": "",
            "requested_loan_amount": ["required"],
            "vehicle_owned": ["required"],
            "make": "",
            "model": "",
            "insurance_expiry_date": "",
            "total_existing_obligations": ["required"],
            "existing_lender": "",
            "existing_banker": "",
            "principal_outstanding": "",
            "rate_of_interest": "",
            "tenure_serviced": "",
        })
        api_log_doc = ucl.log_api(method = "Save Lead Details", request_time = datetime.now(), request = str(data))
        lead = frappe.get_doc({
            "doctype": "Lead",
            "sub_product": data.get("sub_product"),
            "source": data.get("source"),
            "partner_code": data.get("partner_code"),
            "mobile_number": data.get("mobile_number"),
            "pan_number": data.get("pan_number"),
            "first_name": data.get("first_name"),
            "middle_name": data.get("middle_name"),
            "last_name": data.get("last_name"),
            "applicant_name": data.get("applicant_name"),
            "gender": data.get("gender"),
            "dob": datetime.strptime(data.get("dob"), '%m-%d-%Y').date(),
            "line_1": data.get("line_1"),
            "line_2": data.get("line_2"),
            "street": data.get("street"),
            "zip": data.get("zip"),
            "city": data.get("city"),
            "state": data.get("state"),
            "country": data.get("country"),
            "address": data.get("address"),
            "email_id": data.get("email_id"),
            "aadhar": data.get("aadhar"),
            "occupation_type": data.get("occupation_type"),
            "net_take_home_salary": data.get("net_take_home_salary"),
            "profit": data.get("profit"),
            "requested_loan_amount": data.get("requested_loan_amount"),
            "vehicle_owned": data.get("vehicle_owned"),
            "make": data.get("make"),
            "model": data.get("model"),
            "insurance_expiry_date": data.get("insurance_expiry_date"),
            "total_existing_obligations": data.get("total_existing_obligations"),
            "existing_lender": data.get("existing_lender"),
            "existing_banker": data.get("existing_banker"),
            "principal_outstanding": data.get("principal_outstanding"),
            "rate_of_interest": data.get("rate_of_interest"),
            "tenure_serviced": data.get("tenure_serviced"),
        }).insert(ignore_permissions=True)
        
        response = "Lead details saved successfully"
        ucl.log_api_response(is_error = 0, error  = "", api_log_doc = api_log_doc, api_type = "Internal", response = response)
            
        return ucl.responder.respondWithSuccess(message=frappe._(response))

    except ucl.exceptions.APIException as e:
        api_log_doc = ucl.log_api(method = "Save lead details", request_time = datetime.now(), request = "")
        ucl.log_api_response(is_error = 1, error  = frappe.get_traceback(), api_log_doc = api_log_doc, api_type = "Internal", response = "")
        return e.respond()
    

@frappe.whitelist(allow_guest=True)
def update_lead_details(**kwargs):
    try:
        ucl.validate_http_method("POST")
        # user = ucl.__user()
        # partner = ucl.__partner(user.name)

        data = ucl.validate(
            kwargs,{
            "workflow_state": ["required"],
            "name": ["required"],
            "sub_product": "",
            "source": ["required"],
            "partner_code": "",
            "mobile_number": ["required"],
            "pan_number": ["required"],
            "first_name": ["required"],
            "middle_name": "",
            "last_name": "",
            "applicant_name": ["required"],
            "gender": ["required"],
            "dob": ["required"],
            "line_1": ["required"],
            "line_2": ["required"],
            "street": ["required"],
            "zip": ["required"],
            "city": ["required"],
            "state": ["required"],
            "country": ["required"],
            "address": ["required"],
            "email_id": ["required"],
            "aadhar": ["required"],
            "occupation_type": ["required"],
            "net_take_home_salary": "",
            "profit": "",
            "requested_loan_amount": ["required"],
            "vehicle_owned": ["required"],
            "make": "",
            "model": "",
            "insurance_expiry_date": "",
            "total_existing_obligations": ["required"],
            "existing_lender": "",
            "existing_banker": "",
            "principal_outstanding": "",
            "rate_of_interest": "",
            "tenure_serviced": "",
        })

        api_log_doc = ucl.log_api(method = "Save Lead Details", request_time = datetime.now(), request = str(data))
        lead = {
            "workflow_state": data.get("workflow_state"),
            "sub_product": data.get("sub_product"),
            "source": data.get("source"),
            "partner_code": data.get("partner_code"),
            "mobile_number": data.get("mobile_number"),
            "pan_number": data.get("pan_number"),
            "first_name": data.get("first_name"),
            "middle_name": data.get("middle_name"),
            "last_name": data.get("last_name"),
            "applicant_name": data.get("applicant_name"),
            "gender": data.get("gender"),
            "dob": datetime.strptime(data.get("dob"), '%m-%d-%Y').date(),
            "line_1": data.get("line_1"),
            "line_2": data.get("line_2"),
            "street": data.get("street"),
            "zip": data.get("zip"),
            "city": data.get("city"),
            "state": data.get("state"),
            "country": data.get("country"),
            "address": data.get("address"),
            "email_id": data.get("email_id"),
            "aadhar": data.get("aadhar"),
            "occupation_type": data.get("occupation_type"),
            "net_take_home_salary": data.get("net_take_home_salary"),
            "profit": data.get("profit"),
            "requested_loan_amount": data.get("requested_loan_amount"),
            "vehicle_owned": data.get("vehicle_owned"),
            "make": data.get("make"),
            "model": data.get("model"),
            "insurance_expiry_date": data.get("insurance_expiry_date"),
            "total_existing_obligations": data.get("total_existing_obligations"),
            "existing_lender": data.get("existing_lender"),
            "existing_banker": data.get("existing_banker"),
            "principal_outstanding": data.get("principal_outstanding"),
            "rate_of_interest": data.get("rate_of_interest"),
            "tenure_serviced": data.get("tenure_serviced"),
        }
        lead_doc = frappe.get_doc("Lead", data.get("name")).update(lead).save(ignore_permissions = True)
        
        response = "Lead details saved successfully"
        ucl.log_api_response(is_error = 0, error  = "", api_log_doc = api_log_doc, api_type = "Internal", response = response)
            
        return ucl.responder.respondWithSuccess(message=frappe._(response))

    except ucl.exceptions.APIException as e:
        api_log_doc = ucl.log_api(method = "Update lead details", request_time = datetime.now(), request = "")
        ucl.log_api_response(is_error = 1, error  = frappe.get_traceback(), api_log_doc = api_log_doc, api_type = "Internal", response = "")
        return e.respond()