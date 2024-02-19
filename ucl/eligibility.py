import frappe
import json
from frappe import _
from datetime import datetime, timedelta
import ucl
import re
from .exceptions import *
import requests

@frappe.whitelist(allow_guest=True)
def register_mobile_no(**kwargs):
    try:
        ucl.validate_http_method("POST")
        user = ucl.__user()
        data = ucl.validate(
            kwargs,
            {
            "firstName" : "required",
            "surName" : "required",
            "mobileNo" : ["required", "decimal", ucl.validator.rules.LengthRule(10)],
            "reason" : "required"

        })
        ucl_setting = frappe.get_single("UCL Settings")

        url = "https://consumer.experian.in:8443/ECV-P2/content/registerEnhancedMatchMobileOTP.action"
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
            "firstName" : data.get("firstName"),
            "surName" : data.get("surName"),
            "mobileNo" : data.get("mobileNo"),
            "reason" : data.get("reason"),
            "noValidationByPass" : 0,
            "emailConditionalByPass" : 1
        }
        api_log_doc = ucl.log_api(method = "Experian Register Mobile No", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers)))
        response = requests.request("POST", url, headers=headers, data=payload)
        ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Third Party", response = str(response.json()))
        return response.json()

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    

@frappe.whitelist(allow_guest=True)
def generate_mobile_otp(**kwargs):
    try:
        ucl.validate_http_method("POST")
        user = ucl.__user()
        data = ucl.validate(
            kwargs,
            {
            "stgOneHitId" : "required",
            "stgTwoHitId" : "required",
            "mobileNo" : "required",
            "type" : "required"

        })
        ucl_setting = frappe.get_single("UCL Settings")

        url = "https://consumer.experian.in:8443/ECV-P2/content/generateMobileOTP.action"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    
        payload={
            "stgOneHitId" : data.get("stgOneHitId"),
            "stgTwoHitId" : data.get("stgTwoHitId"),
            "mobileNo" : data.get("mobileNo"),
            "type" : data.get("type")

        }
        api_log_doc = ucl.log_api(method = "Experian Generate Mobile No OTP", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers)))
        response = requests.request("POST", url, headers=headers, data=payload)
        ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Third Party", response = str(response.json()))
        return response.json()

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    

@frappe.whitelist(allow_guest=True)
def validate_mobile_otp(**kwargs):
    try:
        ucl.validate_http_method("POST")
        user = ucl.__user()
        data = ucl.validate(
            kwargs,
            {
            "stgOneHitId" : "required",
            "stgTwoHitId" : "required",
            "mobileNo" : "required",
            "otp": "required",
            "type" : "required"

        })
        ucl_setting = frappe.get_single("UCL Settings")

        url = "https://consumer.experian.in:8443/ECV-P2/content/validateMobileOTP.action"
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
        ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Third Party", response = str(response.json()))
        return response.json()

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    
@frappe.whitelist(allow_guest=True)
def bre_offers(**kwargs):
    try:
        ucl.validate_http_method("POST")
        user = ucl.__user()
        data = ucl.validate(
            kwargs,
            {
            "cibilScore": "required",
            "previousLoanAmount": "required",
            "loanAmount": "required",
            "outstandingLoanAmount": "required",
            "previousEmiAmount": "required",
            "netIncome": "required",
            "dob": "required",
            "carEstValue": "required",
            "product": "required",
            "emiPaid": "required",
            "manufactureYear": "required",
            "otherIncomeMonthlyRent": "required",
            "obligations": "required",
            "profession": "required",
            "coApplicant": "required",
            "coApplicantProfile": "required",
            "coApplicantTotalNetIncome": "required",
            "creditReportXml": "required"
        })

        url = "http://bre.switchmyloan.in/v1/bre/used-car-loans/offers-post-new"
        headers = {
            'Content-Type': 'application/json'
        }
    
        payload={
            "cibilScore": data.get("cibilScore"),
            "previousLoanAmount": data.get("previousLoanAmount"),
            "loanAmount": data.get("loanAmount"),
            "outstandingLoanAmount": data.get("outstandingLoanAmount"),
            "previousEmiAmount": data.get("previousEmiAmount"),
            "netIncome": data.get("netIncome"),
            "dob": data.get("dob"),
            "carEstValue": data.get("carEstValue"),
            "product": data.get("product"),
            "emiPaid": data.get("emiPaid"),
            "manufactureYear": data.get("manufactureYear"),
            "otherIncomeMonthlyRent": data.get("otherIncomeMonthlyRent"),
            "obligations": data.get("obligations"),
            "profession": data.get("profession"),
            "coApplicant": data.get("coApplicant"),
            "coApplicantProfile": data.get("coApplicantProfile"),
            "coApplicantTotalNetIncome": data.get("coApplicantTotalNetIncome"),
            "creditReportXml": data.get("creditReportXml")
        }
        api_log_doc = ucl.log_api(method = "BRE Offers", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers)))
        response = requests.request("POST", url, headers=headers, data=payload)
        ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Third Party", response = str(response))
        print(response)
        return response

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    