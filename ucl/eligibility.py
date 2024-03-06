import frappe
import json
from frappe import _
from datetime import datetime, timedelta
import ucl
import re

from ucl import auth
from .exceptions import *
import requests
import base64
import xmltodict


@frappe.whitelist(allow_guest=True)
def verify_eligibility_otp(**kwargs):
    try:
        user = ucl.__user()
        ucl.validate_http_method("POST")

        data = ucl.validate(
            kwargs,
            {
                "mobile": ["required", "decimal", ucl.validator.rules.LengthRule(10)],
                "otp": ["required", "decimal", ucl.validator.rules.LengthRule(4)],
            },
        )
        
        api_log_doc = ucl.log_api(method = "Eligibility Verify OTP", request_time = datetime.now(), request = str(data))      
        token = ucl.verify_user_token(
                entity=data.get("mobile"), token=data.get("otp"), token_type="Eligibility OTP"
        )

        if not token:
            response = "Invalid OTP."
            message = frappe._(response)
            raise ucl.exceptions.FailureException(message)

        if token:
            if token.expiry <= frappe.utils.now_datetime():
                response = "OTP Expired"
                raise ucl.exceptions.FailureException(response)
        if token:
            ucl.token_mark_as_used(token)
            response = "OTP Verified" + "\n" + str(data)
            ucl.log_api_response(is_error = 0, error  = "", api_log_doc = api_log_doc, api_type = "Internal", response = response)
            return ucl.responder.respondWithSuccess(message=frappe._("OTP Verified"))    

    except ucl.exceptions.APIException as e:
        frappe.db.rollback()
        api_log_doc = ucl.log_api(method = "Verify OTP", request_time = datetime.now(), request = "")
        ucl.log_api_response(is_error = 1, error  = frappe.get_traceback(), api_log_doc = api_log_doc, api_type = "Internal", response = "")
        return e.respond()
    except frappe.SecurityException as e:
        frappe.db.rollback()
        api_log_doc = ucl.log_api(method = "Verify OTP", request_time = datetime.now(), request = "")
        ucl.log_api_response(is_error = 1, error  = frappe.get_traceback(), api_log_doc = api_log_doc, api_type = "Internal", response = "")
        return ucl.respondUnauthorized(message=str(e))


@frappe.whitelist(allow_guest=True)
def update_basic_details(**kwargs):
    try:
        ucl.validate_http_method("POST")
        user = ucl.__user()
        data = ucl.validate(
            kwargs,
            {
                "product" : "required",
                "mobile" : ["required", "decimal", ucl.validator.rules.LengthRule(10)],
        })
        api_log_doc = ucl.log_api(method = "Update Basic Details", request_time = datetime.now(), request = str(data))
        if frappe.db.exists("Lead", {"mobile_number" : data.get("mobile")}):
            lead = frappe.get_last_doc("Lead", filters={"mobile_number" : data.get("mobile")})
            eligibility_doc = frappe.get_doc(
                {
                    "doctype": "Eligibility Check",
                    "mobile_no": data.get("mobile"),
                    "product": data.get("product"),
                    "pan_number": lead.pan_number,
                    "first_name": lead.first_name,
                    "last_name": lead.last_name,
                    "full_name": lead.applicant_name,
                    "line_1": lead.line_1,
                    "line_2": lead.line_2,
                    "zip": lead.zip,
                    "pan_city": lead.city,
                    "pan_state": lead.state,
                    "pan_country": lead.country,
                    "street_name": lead.street,
                    "gender": lead.gender,
                    "dob": lead.dob,
                    "full_address": lead.address,
                    "email_id": lead.email_id,
                    "masked_aadhaar": lead.aadhar,
                    "pan_details_filled": 1
                }
            ).insert(ignore_permissions=True)
            frappe.db.commit()
        
        else:
            eligibility_doc = frappe.get_doc(
                {
                    "doctype": "Eligibility Check",
                    "mobile_no": data.get("mobile"),
                    "product": data.get("product"),
                }
            ).insert(ignore_permissions=True)
            frappe.db.commit()
        eligibility_doc_name = eligibility_doc.name
        ucl.log_api_response(is_error = 0, error  = "", api_log_doc = api_log_doc, api_type = "Internal", response = str(eligibility_doc))
        return ucl.responder.respondWithSuccess(message=frappe._(" Data updated successfuly"), data={"id": eligibility_doc_name,"details": eligibility_doc.as_dict()})

    except ucl.exceptions.APIException as e:
        api_log_doc = ucl.log_api(method = "Update Basic Details", request_time = datetime.now(), request = "")
        ucl.log_api_response(is_error = 1, error  = frappe.get_traceback(), api_log_doc = api_log_doc, api_type = "Internal", response = "")
        return e.respond()


@frappe.whitelist(allow_guest=True)
def verify_pan(**kwargs):
    try:
        ucl.validate_http_method("POST")
        user = ucl.__user()
        data = ucl.validate(
            kwargs,
            {
            "pan_number" : "required"
        })
        api_log_doc = ucl.log_api(method = "Pan Plus", request_time = datetime.now(), request = str(data))
        pan_plus_response = auth.pan_plus(data.get("pan_number"))
        if pan_plus_response["code"] == 200 and pan_plus_response["sub_code"] == "SUCCESS":
            return ucl.responder.respondWithSuccess(message=frappe._("Pan Verified Successfully."), data=pan_plus_response['data'])
        else:
            return ucl.responder.respondWithFailure(message=frappe._("Pan Verification Failed"), data=pan_plus_response)

    except ucl.exceptions.APIException as e:
        api_log_doc = ucl.log_api(method = "Pan Plus", request_time = datetime.now(), request = "")
        ucl.log_api_response(is_error = 1, error  = frappe.get_traceback(), api_log_doc = api_log_doc, api_type = "Third Party", response = "")
        return e.respond()


@frappe.whitelist(allow_guest=True)
def update_pan_details(**kwargs):
    try:
        ucl.validate_http_method("POST")
        user = ucl.__user()
        data = ucl.validate(
            kwargs,
            {
                "id" : "required",
                "pan_number": "required",
                "full_name": ["required"],
                "masked_aadhaar": "",
                "address_line_1": "",
                "address_line_2": "",
                "address_street_name": "",
                "zip": "",
                "city": "",
                "state": "",
                "country": "",
                "full_address": "",
                "email": "",
                "phone_number": "",
                "gender": "",
                "dob": "",
        })
        api_log_doc = ucl.log_api(method = "Update Eligibility PAN Details", request_time = datetime.now(), request = str(data))
        eligibility_dict = {
                "mobile_no": data.get("mobile"),
                "product": data.get("product"),
                "pan_number": data.get("pan_number"),
                "fathers_name": data.get("fathers_name"),
                "full_name": data.get("full_name"),
                "masked_aadhaar": data.get("masked_aadhaar"),
                "line_1": data.get("address_line_1"),
                "line_2": data.get("address_line_2"),
                "street_name": data.get("address_street_name"),
                "zip": data.get("zip"),
                "pan_city": data.get("city"),
                "pan_state": data.get("state"),
                "pan_country": data.get("country"),
                "full_address": data.get("full_address"),
                "email_id": data.get("email"),
                "phone_number": data.get("phone_number"),
                "gender": data.get("gender"),
                "dob": data.get("dob"),
                "pan_details_filled": 1
            }
        eligibility_doc = frappe.get_doc("Eligibility Check", data.get("id")).update(eligibility_dict).save(ignore_permissions = True)
        frappe.db.commit()
        ucl.log_api_response(is_error = 0, error  = "", api_log_doc = api_log_doc, api_type = "Internal", response = str(eligibility_doc))
        return ucl.responder.respondWithSuccess(message=frappe._("Data updated successfuly"), data={"id": data.get("id")})

    except ucl.exceptions.APIException as e:
        api_log_doc = ucl.log_api(method = "Update Eligibility PAN Details", request_time = datetime.now(), request = "")
        ucl.log_api_response(is_error = 1, error  = frappe.get_traceback(), api_log_doc = api_log_doc, api_type = "Internal", response = "")
        return e.respond()
    


@frappe.whitelist(allow_guest=True)
def update_existing_loan_details(**kwargs):
    try:
        ucl.validate_http_method("POST")
        user = ucl.__user()
        data = ucl.validate(
            kwargs,
            {
                "running_loan": "",
                "lender_name": "",
                "pos": "required",
                "sanctioned_loan_amount": "",
                "emi": "",
                "total_emis_paid": "",
                "co_applicant": ""
        })
        api_log_doc = ucl.log_api(method = "Update Existing Loan Details", request_time = datetime.now(), request = str(data))
        eligibility_dict ={
                "running_loan": data.get("running_loan"),
                "lender_name": data.get("lender_name"),
                "pos": data.get("pos"),
                "sanctioned_loan_amount": data.get("sanctioned_loan_amount"),
                "emi": data.get("emi"),
                "total_emis_paid": data.get("total_emis_paid"),
                "co_applicant": data.get("co_applicant")
        }
        eligibility_doc = frappe.get_doc("Eligibility Check", "115dd115d6").update(eligibility_dict).save(ignore_permissions = True)
        frappe.db.commit()
        ucl.log_api_response(is_error = 0, error  = "", api_log_doc = api_log_doc, api_type = "Internal", response = str(eligibility_doc))
        return ucl.responder.respondWithSuccess(message=frappe._("Existing Loan details updated successfuly"))

    except ucl.exceptions.APIException as e:
        api_log_doc = ucl.log_api(method = "Update Existing Loan Details", request_time = datetime.now(), request = "")
        ucl.log_api_response(is_error = 1, error  = frappe.get_traceback(), api_log_doc = api_log_doc, api_type = "Internal", response = "")
        return e.respond()
    

@frappe.whitelist(allow_guest=True)
def update_car_details(**kwargs):
    try:
        ucl.validate_http_method("POST")
        user = ucl.__user()
        data = ucl.validate(
            kwargs,
            {
                "brand": "required",
                "registration_number": "",
                "model": "required",
                "variant": "required",
                "on_road_price": "",
                "manufacturing_year": "required",
                "month": "required",
                "city": "required",
                "car_owner": "required",
                "colour": "required",
                "kms_driven": "required"

        })
        api_log_doc = ucl.log_api(method = "Update Car Details", request_time = datetime.now(), request = str(data))
        eligibility_dict ={
                "brand": data.get("brand"),
                "registration_number": data.get("registration_number"),
                "model": data.get("model"),
                "variant": data.get("variant"),
                "on_road_price": data.get("on_road_price"),
                "manufacturing_year": data.get("manufacturing_year"),
                "month": data.get("month"),
                "city": data.get("city"),
                "car_owner": data.get("car_owner"),
                "colour": data.get("colour"),
                "kms_driven": data.get("kms_driven")

        }
        eligibility_doc = frappe.get_doc("Eligibility Check", "115dd115d6").update(eligibility_dict).save(ignore_permissions = True)
        frappe.db.commit()
        ucl.log_api_response(is_error = 0, error  = "", api_log_doc = api_log_doc, api_type = "Internal", response = str(eligibility_doc))
        return ucl.responder.respondWithSuccess(message=frappe._("Car details updated successfuly"))

    except ucl.exceptions.APIException as e:
        api_log_doc = ucl.log_api(method = "Update Car Details", request_time = datetime.now(), request = "")
        ucl.log_api_response(is_error = 1, error  = frappe.get_traceback(), api_log_doc = api_log_doc, api_type = "Internal", response = "")
        return e.respond()
    

@frappe.whitelist(allow_guest=True)
def update_coapplicant_details(**kwargs):
    try:
        ucl.validate_http_method("POST")
        user = ucl.__user()
        data = ucl.validate(
            kwargs,
            {
                "occupation_type": "required",
                "pan_number": "required",
                "first_name": "required",
                "last_name": "",
                "gender": "required",
                "dob": "required",
                "address": "required",
                "requested_loan_amount" : "required",
                "monthly_salary" : "",
                "monthly_gross_income": ""
        })
        api_log_doc = ucl.log_api(method = "Update Coapplicant Details", request_time = datetime.now(), request = str(data))
        eligibility_dict ={
                "coapplicant_occupation_type": data.get("occupation_type"),
                "coapplicant_pan": data.get("pan_number"),
                "coapplicant_first_name": data.get("first_name"),
                "coapplicant_last_name": data.get("last_name"),
                "coapplicant_gender": data.get("gender"),
                "coapplicant_dob": data.get("dob"),
                "coapplicant_address": data.get("address"),
                "coapplicant_requested_loan_amount" : data.get("requested_loan_amount"),
                "coapplicant_monthly_salary" : data.get("monthly_salary"),
                "coapplicant_monthly_gross_income": data.get("monthly_gross_income")
        }
        eligibility_doc = frappe.get_doc("Eligibility Check", "115dd115d6").update(eligibility_dict).save(ignore_permissions = True)
        frappe.db.commit()
        ucl.log_api_response(is_error = 0, error  = "", api_log_doc = api_log_doc, api_type = "Internal", response = str(eligibility_doc))
        return ucl.responder.respondWithSuccess(message=frappe._("Coapplicant details updated successfuly"))

    except ucl.exceptions.APIException as e:
        api_log_doc = ucl.log_api(method = "Update Coapplicant Details", request_time = datetime.now(), request = "")
        ucl.log_api_response(is_error = 1, error  = frappe.get_traceback(), api_log_doc = api_log_doc, api_type = "Internal", response = "")
        return e.respond()
    

@frappe.whitelist(allow_guest=True)
def register_mobile_no(data):
    try:
        ucl_setting = frappe.get_single("UCL Settings")
        if data['match'] == "enhance":
            url = ucl_setting.enhance_match_register
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        
            payload={
                "clientName" : "SWITCH_EM",
                "allowInput" : 1,
                "allowEdit" : 1,
                "allowCaptcha" : 1,
                "allowConsent" : 1,
                "allowEmailVerify" : 1,
                "allowVoucher" : 1,
                "voucherCode" : "SWITCHMYLOAN8iwnw",
                "firstName" : data["firstName"],
                "surName" : data["surName"],
                "mobileNo" : data["mobileNo"],
                "reason" : data["reason"],
                "noValidationByPass" : 0,
                "emailConditionalByPass" : 1
            }
        else:
            url = ucl_setting.full_match_register
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            input_date = data['dateOfBirth']
            parsed_date = datetime.strptime(input_date, "%Y-%d-%m")
            formatted_date = parsed_date.strftime("%d-%b-%Y")

            payload={
                "clientName" : "SWITCH_FM",
                "allowInput" : 1,
                "allowEdit" : 1,
                "allowCaptcha" : 1,
                "allowConsent" : 1,
                "allowVoucher" : 1,
                "allowConsent_additional" : 1,
                "allowEmailVerify" : 1,
                "voucherCode" : "SWITCHMYLOAN8iwnw",
                "emailConditionalByPass" : 1,
                "firstName" : data["firstName"],
                "middleName" : "",
                "surName" : data["surName"],
                "dateOfBirth"  : formatted_date,
                "gender" : data['gender'],
                "mobileNo" : data["mobileNo"],
                "telephoneNo" :"",
                "telephoneType" : "",
                "email" : data['email'],
                "flatno" : "01",
                "buildingName" : "",
                "roadName" : "",
                "city" : data['city'],
                "state" : "27",
                "pincode" : data['pincode'],
                "pan" : data['pan'],
                "reason" : data['reason'],
                "novalidationbypass" : 0 
            }

        api_log_doc = ucl.log_api(method = "Experian Register Mobile No", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers)))
        response = requests.request("POST", url, headers=headers, data=payload)
        ucl.log_api_response(is_error = 0, error  = "", api_log_doc = api_log_doc, api_type = "Third Party", response = str(response.json()))
        return response.json()

    except ucl.exceptions.APIException as e:
        api_log_doc = ucl.log_api(method = "Register Mobile No", request_time = datetime.now(), request = "")
        ucl.log_api_response(is_error = 1, error  = frappe.get_traceback(), api_log_doc = api_log_doc, api_type = "Third Party", response = "")
        return e.respond()
    

@frappe.whitelist(allow_guest=True)
def generate_mobile_otp(data):
    try:
        ucl_setting = frappe.get_single("UCL Settings")

        url = ucl_setting.generate_otp
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    
        payload={
            "stgOneHitId" : data["stgOneHitId"],
            "stgTwoHitId" : data["stgTwoHitId"],
            "mobileNo" : data["mobileNo"],
            "type" : data["type"]

        }
        api_log_doc = ucl.log_api(method = "Experian Generate Mobile No OTP", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers)))
        response = requests.request("POST", url, headers=headers, data=payload)
        ucl.log_api_response(is_error = 0, error  = "", api_log_doc = api_log_doc, api_type = "Third Party", response = str(response.json()))
        return response.json()

    except ucl.exceptions.APIException as e:
        api_log_doc = ucl.log_api(method = "Generate Mobile OTP", request_time = datetime.now(), request = "")
        ucl.log_api_response(is_error = 1, error  = frappe.get_traceback(), api_log_doc = api_log_doc, api_type = "Third Party", response = "")
        return e.respond()


@frappe.whitelist(allow_guest=True)
def enhance_match(**kwargs):
    try:
        ucl.validate_http_method("POST")
        data = ucl.validate(
            kwargs,
            {
            "id" : "required",
            "occupation_type": "required",
            "requested_loan_amount" : "required",
            "monthly_salary" : "",
            "monthly_gross_income": "",
        })
        api_log_doc = ucl.log_api(method = "Enhance Match", request_time = datetime.now(), request = str(data))
        eligibility_dict ={
                "occupation_type": data.get("occupation_type"),
                "requested_loan_amount" : data.get("requested_loan_amount"),
                "monthly_salary" : data.get("monthly_salary"),
                "monthly_gross_income": data.get("monthly_gross_income")
        }
        eligibility_doc = frappe.get_doc("Eligibility Check", data.get("id")).update(eligibility_dict).save(ignore_permissions = True)
        frappe.db.commit()
        register_data = {
            "firstName" : eligibility_doc.first_name,
            "surName" : eligibility_doc.last_name,
            "mobileNo" : eligibility_doc.mobile_no,
            "reason" : "Find my credit report",
            "match": "enhance"
        }
        register = register_mobile_no(register_data)
        generate_otp_data = {"mobileNo" : eligibility_doc.mobile_no, "stgOneHitId":register["stgOneHitId"], "stgTwoHitId":register["stgTwoHitId"], "type" : "CUSTOM"}

        generate_otp = generate_mobile_otp(generate_otp_data)
        if generate_otp["otpGenerationStatus"] == "1":
            generate_otp["type"] = "CUSTOM"
            generate_otp["id"] = eligibility_doc.name
            ucl.log_api_response(is_error = 0, error  = "", api_log_doc = api_log_doc, api_type = "Third Party", response = str(generate_otp))
            return ucl.responder.respondWithSuccess(message = frappe._("Otp Generated Successfully"), data=generate_otp)
        else:
            ucl.log_api_response(is_error = 1, error  = generate_otp["errorString"], api_log_doc = api_log_doc, api_type = "Third Party", response = str(generate_otp))
            return ucl.responder.respondWithFailure(message = frappe._(generate_otp["errorString"]))
    except ucl.exceptions.APIException as e:
        api_log_doc = ucl.log_api(method = "Enhance Match", request_time = datetime.now(), request = "")
        ucl.log_api_response(is_error = 1, error  = frappe.get_traceback(), api_log_doc = api_log_doc, api_type = "Third Party", response = "")
        return e.respond()
    

def full_match(id):
    try:
        ucl.validate_http_method("POST")
        api_log_doc = ucl.log_api(method = "Full Match", request_time = datetime.now(), request = str(id))
        eligibility_doc = frappe.get_doc("Eligibility Check", id)
        print(eligibility_doc.gender)
        gender = 0
        if eligibility_doc.gender == "Male":
            gender = 1
        elif eligibility_doc.gender == "Female":
            gender = 2
        else:
            gender = 3
        
        register_data = {
            "firstName" : eligibility_doc.first_name,
            "surName" : eligibility_doc.last_name,
            "mobileNo" : eligibility_doc.mobile_no,
            "dateOfBirth" : eligibility_doc.dob,
            "email" : eligibility_doc.email_id,
            "pincode": eligibility_doc.zip,
            "city": eligibility_doc.pan_city,
            "state": eligibility_doc.pan_state,
            "gender": gender,
            "pan" : eligibility_doc.pan_number,
            "aadhaar" : eligibility_doc.masked_aadhaar,
            "reason" : "Find my credit report",
            "match": "full"
        }
        register = register_mobile_no(register_data)
        generate_otp_data = {"mobileNo" : eligibility_doc.mobile_no, "stgOneHitId":register["stgOneHitId"], "stgTwoHitId":register["stgTwoHitId"], "type" : "NORMAL"}

        generate_otp = generate_mobile_otp(generate_otp_data)
        if generate_otp["otpGenerationStatus"] == "1":
            generate_otp["type"] = "NORMAL"
            generate_otp["id"] = eligibility_doc.name
            ucl.log_api_response(is_error = 0, error  = "", api_log_doc = api_log_doc, api_type = "Third Party", response = str(generate_otp))
            return ucl.responder.respondWithSuccess(message = frappe._("Dear Customer, we are not able to fetch your bureau report via enhanced match hence we are redirecting to full match"), data=generate_otp)
        else:
            ucl.log_api_response(is_error = 1, error  = generate_otp["errorString"], api_log_doc = api_log_doc, api_type = "Third Party", response = str(generate_otp))
            return ucl.responder.respondWithFailure(message = frappe._(generate_otp["errorString"]))
    except ucl.exceptions.APIException as e:
        api_log_doc = ucl.log_api(method = "Full Match", request_time = datetime.now(), request = "")
        ucl.log_api_response(is_error = 1, error  = frappe.get_traceback(), api_log_doc = api_log_doc, api_type = "Third Party", response = "")
        return e.respond()
    

@frappe.whitelist(allow_guest=True)
def validate_mobile_otp(**kwargs):
    try:
        ucl.validate_http_method("POST")
        user = ucl.__user()
        data = ucl.validate(
            kwargs,
            {
            "id" : "required",
            "mobileNo": "required",
            "stgOneHitId" : "required",
            "stgTwoHitId" : "required",
            "otp": "required",
            "type" : "required"

        })
        ucl_setting = frappe.get_single("UCL Settings")

        url = ucl_setting.validate_otp
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        payload={
            "stgOneHitId" : data.get("stgOneHitId"),
            "stgTwoHitId" : data.get("stgTwoHitId"),
            "mobileNo" : data.get("mobileNo"),
            "otp" : data.get("otp"),
            "type" : data.get("type")

        }
        api_log_doc = ucl.log_api(method = "Experian Validate Mobile No OTP", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers)))
        response = requests.request("POST", url, headers=headers, data=payload)
        if data.get("type") == "CUSTOM" and response.json()['errorString'] == "consumer record not found":
            full_match(data.get("id"))
        # if response.json()['showHtmlReportForCreditReport'] == None:
        #     eligibility_doc = frappe.get_doc("Eligibility Check", data.get("id"))
        #     eligibility_doc.cibil_score = -1
        #     eligibility_doc.save(ignore_permissions=True)
        # else:
        #     xml_dict = xmltodict.parse(response.json()['showHtmlReportForCreditReport'])
        #     json_data = json.dumps(xml_dict)
        #     print(json_data)

        response = {"id" : data.get("id"), "response" : response.json()}
        ucl.log_api_response(is_error = 0, error  = "", api_log_doc = api_log_doc, api_type = "Third Party", response = str(response))
        return response

    except ucl.exceptions.APIException as e:
        api_log_doc = ucl.log_api(method = "Validate Mobile OTP", request_time = datetime.now(), request = "")
        ucl.log_api_response(is_error = 1, error  = frappe.get_traceback(), api_log_doc = api_log_doc, api_type = "Third Party", response = "")
        return e.respond()
    
@frappe.whitelist(allow_guest=True)
def bre_offers(**kwargs):
    try:
        user = ucl.__user()
        ucl.validate_http_method("POST")
        data = ucl.validate(
            kwargs,
            {
            # "cibilScore": "required",
            # "previousLoanAmount": "required",
            # "loanAmount": "required",
            # "outstandingLoanAmount": "required",
            # "previousEmiAmount": "required",
            # "netIncome": "required",
            # "dob": "required",
            # "carEstValue": "required",
            # "product": "required",
            # "emiPaid": "required",
            # "manufactureYear": "required",
            # "otherIncomeMonthlyRent": "required",
            # "obligations": "required",
            # "profession": "required",
            # "coApplicant": "required",
            # "coApplicantProfile": "",
            # "coApplicantTotalNetIncome": "required",
            # "creditReportXml": ""
            "id" : "required"
        })
        eligibility_doc = frappe.get_doc("Eligibility Check", data.get("id"))
        if eligibility_doc.product == "New Car Purchase":
            lead = frappe.new_doc("Lead")
            lead.sub_product = eligibility_doc.product
            lead.partner_code = ""
            lead.mobile_number = eligibility_doc.mobile_no
            lead.occupation_type = eligibility_doc.occupation_type
            lead.requested_loan_amount = eligibility_doc.requested_loan_amount
            lead.pan_number = eligibility_doc.pan_number
            lead.first_name = eligibility_doc.first_name
            lead.last_name = eligibility_doc.last_name
            lead.applicant_name = eligibility_doc.full_name
            lead.line_1 = eligibility_doc.line_1
            lead.line_2 = eligibility_doc.line_2
            lead.zip = eligibility_doc.zip
            lead.city = eligibility_doc.pan_city
            lead.state = eligibility_doc.pan_state
            lead.country = eligibility_doc.pan_country
            lead.street = eligibility_doc.street_name
            lead.gender = eligibility_doc.gender
            lead.dob = eligibility_doc.dob
            lead.address = eligibility_doc.full_address
            lead.email_id = eligibility_doc.email_id
            lead.aadhar = eligibility_doc.masked_aadhaar
            lead.insert()
            return ucl.responder.respondWithSuccess(message=frappe._("Thanks for sharing your details. We will get back to you shortly to assist you for your loan application."))

        else:
            ucl_setting = frappe.get_single("UCL Settings")
            url = ucl_setting.bre
            headers = {
                'Content-Type': 'application/json'
            }
            cibilscore = eligibility_doc.cibil_score
            loanamount = eligibility_doc.requested_loan_amount
            if eligibility_doc.occupation_type == "Salaried":
                netincome = eligibility_doc.monthly_salary
            else:
                netincome = eligibility_doc.monthly_gross_income
            dob = eligibility_doc.dob
            carvalue = eligibility_doc.estimated_value
            if eligibility_doc.product == "Used Car Purchase":
                product = "Re-Purchase"
            else:
                product = "Bt-TopUp"
            emipaid = eligibility_doc.total_emis_paid
            manufactureyear = eligibility_doc.manufacturing_year
            obligations = eligibility_doc.obligations
            profession = eligibility_doc.occupation_type
            if eligibility_doc.coapplicant != "":
                coapplicant = True
            else:
                coapplicant = False
            coapplicant_profile = eligibility_doc.coapplicant_occupation_type
            if eligibility_doc.coapplicant_occupation_type == "Salaried":
                coapplicant_income = eligibility_doc.coapplicant_monthly_salary
            else:
                coapplicant_income = eligibility_doc.coapplicant_monthly_gross_income
            creditreport = eligibility_doc.credit_report
        
            payload={
                "cibilScore": cibilscore,
                "previousLoanAmount": "1",
                "loanAmount": loanamount,
                "outstandingLoanAmount": "1",
                "previousEmiAmount": "1",
                "netIncome": netincome,
                "dob": dob,
                "carEstValue": carvalue,
                "product": product,
                "emiPaid": emipaid,
                "manufactureYear": manufactureyear,
                "otherIncomeMonthlyRent": "0",
                "obligations": obligations,
                "profession": profession,
                "coApplicant": coapplicant,
                "coApplicantProfile": coapplicant_profile,
                "coApplicantTotalNetIncome": coapplicant_income,
                "creditReportXml": creditreport
            }

            response = requests.request("POST", url, headers=headers, json=payload)
            api_log_doc = ucl.log_api(method = "BRE Offers", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers)))
            if response.status_code == 200:
                ucl.log_api_response(is_error = 0, error  = "", api_log_doc = api_log_doc, api_type = "Third Party", response = str(response.json()))
                return ucl.responder.respondWithSuccess(message=frappe._("Offers Successfully Generated"), data=response.json()['offers'])
            else:
                return ucl.responder.respondWithFailure(message=frappe._("Failed"), data=response.text)

    except ucl.exceptions.APIException as e:
        api_log_doc = ucl.log_api(method = "BRE Offers", request_time = datetime.now(), request = "")
        ucl.log_api_response(is_error = 1, error  = frappe.get_traceback(), api_log_doc = api_log_doc, api_type = "Third Party", response = "")
        return e.respond()
    

@frappe.whitelist(allow_guest=True)
def create_workorder(**kwargs):
    try:
        user = ucl.__user()
        data = ucl.validate(
            kwargs,
            {
            "id" : "required"
            })
        ucl_setting = frappe.get_single("UCL Settings")
        url = ucl_setting.create_workorder.format(report_type="personal_salaried")


        headers = {
            'client-id': ucl_setting.glib_client_id,
            'client-secret': ucl_setting.glib_client_secret,
        }
        response = requests.request("POST", url, headers=headers)
        api_log_doc = ucl.log_api(method = "Glib create workorder", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers) + "\n" ))
        if response.status_code == 201:        
            ucl.log_api_response(is_error = 0, error  = "", api_log_doc = api_log_doc, api_type = "Third Party", response = str(response.json()))
            id = response.json()['id']
            add_bank_statement(id,data.get("id"))
            return ucl.responder.respondWithSuccess(message=frappe._("success"), data=response.json())
        else:
            ucl.log_api_response(is_error = 0, error  = "", api_log_doc = api_log_doc, api_type = "Third Party", response = str(response.json()))
            return ucl.responder.respondWithFailure(message=frappe._("Failed"), data=response.text)


    except ucl.exceptions.APIException as e:
        api_log_doc = ucl.log_api(method = "Create Workorder", request_time = datetime.now(), request = "")
        ucl.log_api_response(is_error = 1, error  = frappe.get_traceback(), api_log_doc = api_log_doc, api_type = "Third Party", response = "")
        return e.respond()
    

def add_bank_statement(id,eligibility_id):
    try:
        user = ucl.__user()
        print(id)
        ucl_setting = frappe.get_single("UCL Settings")
        url = ucl_setting.add_bank_statement.format(id = id)

        headers = {
            'client-id': ucl_setting.glib_client_id,
            'client-secret': ucl_setting.glib_client_secret,
        }
        payload = {
            "file_type" : "bank_statement"
        }
        eligibility_doc = frappe.get_doc("Eligibility Check", eligibility_id)
        bank_file = eligibility_doc.bank_statement_file
        response = requests.get(bank_file)
        files = {
            'file': ('bank_statement.pdf', response.content, 'application/pdf'),
        }
        # files = {
        #     'file': ('file_name.txt', open('/home/dell/Downloads/bank_statement.pdf', 'rb'), 'text/plain'),
        # }
        response = requests.request("POST", url, headers=headers, data=payload, files=files)
        api_log_doc = ucl.log_api(method = "Glib add bank statement", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers) + "\n" ))
        if response.status_code == 200:        
            ucl.log_api_response(is_error = 0, error  = "", api_log_doc = api_log_doc, api_type = "Third Party", response = str(response.json()))
            process_workorder(id)
            return ucl.responder.respondWithSuccess(message=frappe._("success"), data=response.json())
        else:
            ucl.log_api_response(is_error = 0, error  = "", api_log_doc = api_log_doc, api_type = "Third Party", response = str(response.json()))
            return ucl.responder.respondWithFailure(message=frappe._("Failed"), data=response.text)
       
    except ucl.exceptions.APIException as e:
        api_log_doc = ucl.log_api(method = "Add bank statement", request_time = datetime.now(), request = "")
        ucl.log_api_response(is_error = 1, error  = frappe.get_traceback(), api_log_doc = api_log_doc, api_type = "Third Party", response = "")
        return e.respond()

def process_workorder(id):
    try:
        user = ucl.__user()
        print(id)
        ucl_setting = frappe.get_single("UCL Settings")
        url = ucl_setting.process_workorder.format(id = id)

        headers = {
            'client-id': ucl_setting.glib_client_id,
            'client-secret': ucl_setting.glib_client_secret,
        }
        response = requests.request("POST", url, headers=headers)
        api_log_doc = ucl.log_api(method = "Glib process workorder", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers) + "\n" ))
        if response.status_code == 200:        
            ucl.log_api_response(is_error = 0, error  = "", api_log_doc = api_log_doc, api_type = "Third Party", response = str(response.json()))
            retrieve_workorder(id)
            return ucl.responder.respondWithSuccess(message=frappe._("success"), data=response.json())

        else:
            ucl.log_api_response(is_error = 0, error  = "", api_log_doc = api_log_doc, api_type = "Third Party", response = str(response.json()))
            return ucl.responder.respondWithFailure(message=frappe._("Failed"), data=response.text)
    except ucl.exceptions.APIException as e:
        api_log_doc = ucl.log_api(method = "Process Workorder", request_time = datetime.now(), request = "")
        ucl.log_api_response(is_error = 1, error  = frappe.get_traceback(), api_log_doc = api_log_doc, api_type = "Third Party", response = "")
        return e.respond()

def retrieve_workorder(id):
    try:
        user = ucl.__user()
        print(id)
        ucl_setting = frappe.get_single("UCL Settings")
        url = ucl_setting.retrieve_workorder.format(id = id)

        headers = {
            'client-id': ucl_setting.glib_client_id,
            'client-secret': ucl_setting.glib_client_secret,
        }
        response = requests.request("GET", url, headers=headers)
        api_log_doc = ucl.log_api(method = "Glib retrieve workorder", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers) + "\n" ))
        if response.status_code == 200:        
            ucl.log_api_response(is_error = 0, error  = "", api_log_doc = api_log_doc, api_type = "Third Party", response = str(response.json()))
            download_report(id)
            return ucl.responder.respondWithSuccess(message=frappe._("success"), data=response.json())
        else:
            ucl.log_api_response(is_error = 0, error  = "", api_log_doc = api_log_doc, api_type = "Third Party", response = str(response.json()))
            return ucl.responder.respondWithFailure(message=frappe._("Failed"), data=response.text)
        
    except ucl.exceptions.APIException as e:
        api_log_doc = ucl.log_api(method = "Retrieve Workorder", request_time = datetime.now(), request = "")
        ucl.log_api_response(is_error = 1, error  = frappe.get_traceback(), api_log_doc = api_log_doc, api_type = "Third Party", response = "")
        return e.respond()


# @frappe.whitelist(allow_guest=True)
def download_report(id):
    try:
        user = ucl.__user()
        # print(id)
        # id = "5ad1a2d4-df26-495c-bf95-07b605699a5a"
        ucl_setting = frappe.get_single("UCL Settings")
        url = ucl_setting.download_report.format(id=id)

        headers = {
            'client-id': ucl_setting.glib_client_id,
            'client-secret': ucl_setting.glib_client_secret,
        }
        params = {
            "file_type": "json"
        }
        response = requests.get(url, headers=headers, params=params)
        api_log_doc = ucl.log_api(method = "Glib download report", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers) + "\n" ))
        if response.status_code == 200:     
            ucl.log_api_response(is_error = 0, error  = "", api_log_doc = api_log_doc, api_type = "Third Party", response = str(response.json()))
            details = response.json()['Summary - Fixed Income / Obligation']
            for i in details:
                if i['Type'] == "Salary":
                    salary = i['Amount']
                if i['Type'] == "EMI/LOAN":
                    obligation = i["Amount"]

            return ucl.responder.respondWithSuccess(message=frappe._("success"), data=response.json())
        else:
            ucl.log_api_response(is_error = 0, error  = "", api_log_doc = api_log_doc, api_type = "Third Party", response = str(response.json()))
            return ucl.responder.respondWithFailure(message=frappe._("Failed"), data=response.text)

    except ucl.exceptions.APIException as e:
        api_log_doc = ucl.log_api(method = "Download Report", request_time = datetime.now(), request = "")
        ucl.log_api_response(is_error = 1, error  = frappe.get_traceback(), api_log_doc = api_log_doc, api_type = "Third Party", response = "")
        return e.respond()
    

@frappe.whitelist(allow_guest=True)
def ibb(**kwargs):
    try:
        user = ucl.__user()
        ucl.validate_http_method("POST")
        data = ucl.validate(
            kwargs,{
            "id" : "required",
            "for" : "required",
            "year": "", 
            "month": "", 
            "make": "", 
            "model": "", 
            "variant": "", 
            "location": "", 
            "color": "", 
            "owner": "", 
            "kilometer": "", 
        },
        )
        ucl_setting = frappe.get_single("UCL Settings")
        url = ucl_setting.ibb_url

        if data.get("for") == "year":
            payload = {
            "for": "year", 
            "access_token": ucl_setting.ibb_token 
            }
            response = requests.request("POST", url, data=payload)
            details=response.json()['year']

        elif data.get("for") == "month":
            payload = {
            "for": "month",
            "year": data.get("year"), 
            "access_token": ucl_setting.ibb_token 
            }
            response = requests.request("POST", url, data=payload)
            details=response.json()['month']


        elif data.get("for") == "make":
            payload = {
            "for": "make", 
            "year": data.get("year"), 
            "month": data.get("month"), 
            "access_token": ucl_setting.ibb_token 
            }
            response = requests.request("POST", url, data=payload)
            details=response.json()['make']
        
        elif data.get("for") == "model":
            payload = {
            "for": "model", 
            "year": data.get("year"), 
            "month": data.get("month"), 
            "make": data.get("make"),
            "access_token": ucl_setting.ibb_token 
            } 
            response = requests.request("POST", url, data=payload)
            details=response.json()['model']  
            
        elif data.get("for") == "variant":
            payload = {
            "for": "variant", 
            "year": data.get("year"), 
            "month": data.get("month"), 
            "make": data.get("make"),
            "model": data.get("model"),
            "access_token": ucl_setting.ibb_token 
            }  
            response = requests.request("POST", url, data=payload)
            details=response.json()['variant'] 

        elif data.get("for") == "location":
            payload = {
            "for": "city",
            "access_token": ucl_setting.ibb_token 
            } 
            response = requests.request("POST", url, data=payload)
            details=response.json()['city']

        elif data.get("for") == "color":
            payload = {
            "for": "color",
            "access_token": ucl_setting.ibb_token 
            }
            response = requests.request("POST", url, data=payload)
            details=response.json()['color'] 
            

        else:
            payload = {
                "for": "comprehensivePrice", 
                "year": data.get("year"), 
                "month": data.get("month"), 
                "make": data.get("make"), 
                "model": data.get("model"), 
                "variant": data.get("variant"), 
                "location": data.get("location"), 
                "color": data.get("color"), 
                "owner": data.get("owner"), 
                "kilometer": data.get("kilometer"), 
                "access_token": ucl_setting.ibb_token 
            }
            response = requests.request("POST", url, data=payload)
            details=response.json()['retail']
            eligibility_doc = frappe.get_doc("Eligibility Check", data.get("id"))
            eligibility_doc.estimated_value = response.json()['retail']['marketprice']
            eligibility_doc.save(ignore_permissions = True)


        
        api_log_doc = ucl.log_api(method = "IBB {} API".format(data.get("for")), request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(payload) + "\n" ))          
        if response.status_code == 200:
            ucl.log_api_response(is_error = 0, error  = "", api_log_doc = api_log_doc, api_type = "Third Party", response = str(response.json()))
            return ucl.responder.respondWithSuccess(message=frappe._("success"), data=details)
        else:
            return ucl.responder.respondWithFailure(message=frappe._("Failed"), data=response.text)
        
    except ucl.exceptions.APIException as e:
        api_log_doc = ucl.log_api(method = "IBB", request_time = datetime.now(), request = "")
        ucl.log_api_response(is_error = 1, error  = frappe.get_traceback(), api_log_doc = api_log_doc, api_type = "Third Party", response = "")
        return e.respond()
    



    