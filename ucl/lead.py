import frappe
import json
from frappe import _
from datetime import datetime, timedelta
from frappe.auth import LoginAttemptTracker
import ucl
import re
from .exceptions import *


@frappe.whitelist(allow_guest=True)
def dup_entry_check(product, mobile, loan_amt):
    if frappe.db.exists("Lead", {"mobile_number" : mobile, "sub_product" : product, "requested_loan_amount" : loan_amt}):
        lead = frappe.get_last_doc("Lead", filters={"mobile_number" : mobile, "sub_product" : product, "requested_loan_amount" : loan_amt})
        message = "Lead with the same mobile number and loan amount already exists"
        raise ucl.exceptions.FailureException(message=message)



@frappe.whitelist(allow_guest=True)
def lead_details(**kwargs):
    try:
        ucl.validate_http_method("POST")
        user = ucl.__user()
        user_roles = frappe.db.get_values(
            "Has Role", {"parent": user.name, "parenttype": "User"}, ["role"]
        )
        user_role = []
        for i in list(user_roles):
            user_role.append(i[0])
        if "Partner" in user_role or "Partner Associate" in user_role:
            partner = ucl.__partner(user.name)

        data = ucl.validate(
            kwargs,{
            "sub_product": "",
            "source": "",
            "partner_code": "",
            "mobile_number": ["required",  "decimal", ucl.validator.rules.LengthRule(10)],
            "pan_number": ["required"],
            "first_name": ["required"],
            "last_name": ["required"],
            "full_name": "",
            "gender": "",
            "dob": ["required"],
            "line_1": "",
            "line_2": "",
            "street": "",
            "zip": "",
            "city": "",
            "state": "",
            "country": "",
            "address": "",
            "email_id": ["required"],
            "aadhar": "",
            "occupation_type": ["required"],
            "monthly_income": "",
            "obligations": "",
            "requested_loan_amount": ["required"]
        })
        api_log_doc = ucl.log_api(method = "Save Lead Details", request_time = datetime.now(), request = str(data))
        if int(data.get("mobile_number")[0]) < 5:
            return ucl.responder.respondInvalidData(message=frappe._("Please Enter Valid Mobile Number"),)
        else:
            dup_entry_check(product=data.get("sub_product"), mobile=data.get("mobile_number"), loan_amt=data.get("requested_loan_amount"))

            lead = frappe.get_doc({
                "doctype": "Lead",
                "sub_product": data.get("sub_product"),
                "source": data.get("source"),
                "partner_code": data.get("partner_code"),
                "mobile_number": data.get("mobile_number"),
                "pan_number": data.get("pan_number"),
                "first_name": data.get("first_name"),
                "last_name": data.get("last_name"),
                "full_name": data.get("full_name"),
                "gender": data.get("gender"),
                "dob": data.get("dob"),
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
                "monthly_income": data.get("monthly_income"),
                "obligations": data.get("obligations"),
                "requested_loan_amount": data.get("requested_loan_amount"),
            }).insert(ignore_permissions=True)
            frappe.db.commit()
            
            message = "Lead details saved successfully"
            response = {"message" : message, "id" : lead.name}
            ucl.log_api_response(is_error = 0, error  = "", api_log_doc = api_log_doc, api_type = "Internal", response = str(response))
                
            return ucl.responder.respondWithSuccess(message=frappe._("Success"), data=response)

    except ucl.exceptions.APIException as e:
        api_log_doc = ucl.log_api(method = "Lead details", request_time = datetime.now(), request = "")
        ucl.log_api_response(is_error = 1, error  = frappe.get_traceback(), api_log_doc = api_log_doc, api_type = "Internal", response = "", status_code=e.http_status_code)
        return e.respond()
    

@frappe.whitelist(allow_guest=True)
def update_lead_details(**kwargs):
    try:
        ucl.validate_http_method("POST")
        user = ucl.__user()
        user_roles = frappe.db.get_values(
            "Has Role", {"parent": user.name, "parenttype": "User"}, ["role"]
        )
        user_role = []
        for i in list(user_roles):
            user_role.append(i[0])
        if "Partner" in user_role or "Partner Associate" in user_role:
            partner = ucl.__partner(user.name)

        data = ucl.validate(
            kwargs,{
            "id": ["required"],
            "vehicle_owned": "",
            "make": "",
            "model": "",
            "insurance_expiry_date": "",
            "existing_lender": "",
            "existing_banker": "",
            "principal_outstanding": "",
            "rate_of_interest": "",
            "tenure_serviced": "",
        })

        api_log_doc = ucl.log_api(method = "Save Lead Details", request_time = datetime.now(), request = str(data))
        lead = {
            "vehicle_owned": data.get("vehicle_owned"),
            "make": data.get("make"),
            "model": data.get("model"),
            "insurance_expiry_date": data.get("insurance_expiry_date"),
            "existing_lender": data.get("existing_lender"),
            "existing_banker": data.get("existing_banker"),
            "principal_outstanding": data.get("principal_outstanding"),
            "rate_of_interest": data.get("rate_of_interest"),
            "tenure_serviced": data.get("tenure_serviced"),
        }
        lead_doc = frappe.get_doc("Lead", data.get("id")).update(lead).save(ignore_permissions = True)
        
        response = "Lead details saved successfully"
        ucl.log_api_response(is_error = 0, error  = "", api_log_doc = api_log_doc, api_type = "Internal", response = response)
            
        return ucl.responder.respondWithSuccess(message=frappe._(response))

    except ucl.exceptions.APIException as e:
        api_log_doc = ucl.log_api(method = "Update lead details", request_time = datetime.now(), request = "")
        ucl.log_api_response(is_error = 1, error  = frappe.get_traceback(), api_log_doc = api_log_doc, api_type = "Internal", response = "", status_code=e.http_status_code)
        return e.respond()
    

@frappe.whitelist(allow_guest=True)
def all_lead_details():
    try:
        try:
            associate = ucl.lead_dashboard_list()
            return ucl.responder.respondWithSuccess(
                    message=frappe._("success"), data=associate
                )
            
        except NotFoundException:
            raise ucl.exceptions.LeadNotFoundException()
    except ucl.exceptions.APIException as e:
        frappe.db.rollback()
        api_log_doc = ucl.log_api(method = "Get Lead Dashboard List", request_time = datetime.now(), request = "")
        ucl.log_api_response(is_error = 1, error  = frappe.get_traceback(), api_log_doc = api_log_doc, api_type = "Internal", response = "", status_code=e.http_status_code)
        return e.respond()
    except frappe.SecurityException as e:
        frappe.db.rollback()
        api_log_doc = ucl.log_api(method = "Get Lead Dashboard List", request_time = datetime.now(), request = "")
        ucl.log_api_response(is_error = 1, error  = frappe.get_traceback(), api_log_doc = api_log_doc, api_type = "Internal", response = "", status_code=e.http_status_code)
        return ucl.responder.respondUnauthorized(message=str(e))