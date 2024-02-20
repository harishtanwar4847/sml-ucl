import frappe
import json
from frappe import _
from datetime import datetime, timedelta
import ucl
import re
from .exceptions import *
import requests
import base64

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
    

@frappe.whitelist(allow_guest=True)
def create_workorder():
    try:
        user = ucl.__user()
        url = "https://switch-my-loan.staging.autosift.cloud/api/work_orders/?report_type=personal_salaried"
        ucl_setting = frappe.get_single("UCL Settings")

        headers = {
            'client-id': ucl_setting.glib_client_id,
            'client-secret': ucl_setting.glib_client_secret,
        }
        response = requests.request("POST", url, headers=headers)
        if response.status_code == 201:
            api_log_doc = ucl.log_api(method = "Glib create workorder", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers) + "\n" ))
        
            ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Third Party", response = str(response.json()))
            id = response.json()['id']
            add_bank_statement(id)
            return ucl.responder.respondWithSuccess(message=frappe._("success"), data=response.json())
        else:
            return ucl.responder.respondWithFailure(message=frappe._("Failed"), data=response.text)


    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    

def add_bank_statement(id):
    try:
        user = ucl.__user()
        url = "https://switch-my-loan.staging.autosift.cloud/api/work_orders/{}/bank_statement/".format(id)
        ucl_setting = frappe.get_single("UCL Settings")

        headers = {
            'client-id': ucl_setting.glib_client_id,
            'client-secret': ucl_setting.glib_client_secret,
        }
        payload = {
            "file_type" : "bank_statement"
        }
        files = {
            'file': ('file_name.txt', open('/home/dell/Downloads/bank_statement.pdf', 'rb'), 'text/plain'),
        }
        response = requests.request("POST", url, headers=headers, data=payload, files=files)
        if response.status_code == 200:
            api_log_doc = ucl.log_api(method = "Glib add bank statement", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers) + "\n" ))
        
            ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Third Party", response = str(response.json()))
            process_workorder(id)
            return ucl.responder.respondWithSuccess(message=frappe._("success"), data=response.json())
        else:
            return ucl.responder.respondWithFailure(message=frappe._("Failed"), data=response.text)
       
    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()

def process_workorder(id):
    try:
        user = ucl.__user()
        url = "https://switch-my-loan.staging.autosift.cloud/api/work_orders/{}/process/".format(id)
        ucl_setting = frappe.get_single("UCL Settings")

        headers = {
            'client-id': ucl_setting.glib_client_id,
            'client-secret': ucl_setting.glib_client_secret,
        }
        response = requests.request("POST", url, headers=headers)
        if response.status_code == 200:
            api_log_doc = ucl.log_api(method = "Glib process workorder", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers) + "\n" ))
        
            ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Third Party", response = str(response.json()))
            retrieve_workorder(id)
            return ucl.responder.respondWithSuccess(message=frappe._("success"), data=response.json())

        else:
            return ucl.responder.respondWithFailure(message=frappe._("Failed"), data=response.text)
    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()

def retrieve_workorder(id):
    try:
        user = ucl.__user()
        url = "https://switch-my-loan.staging.autosift.cloud/api/work_orders/{}/".format(id)
        ucl_setting = frappe.get_single("UCL Settings")

        headers = {
            'client-id': ucl_setting.glib_client_id,
            'client-secret': ucl_setting.glib_client_secret,
        }
        response = requests.request("GET", url, headers=headers)
        if response.status_code == 200:
            api_log_doc = ucl.log_api(method = "Glib retrieve workorder", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers) + "\n" ))
            
            ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Third Party", response = str(response.json()))
            download_report(id)
            return ucl.responder.respondWithSuccess(message=frappe._("success"), data=response.json())
        else:
            return ucl.responder.respondWithFailure(message=frappe._("Failed"), data=response.text)
        
    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()


# @frappe.whitelist(allow_guest=True)
def download_report(id):
    try:
        user = ucl.__user()
        # id = "3cc1b47f-a750-4a5f-9cd6-bc1ebb3ee1c7"
        print(id)
        url = "https://switch-my-loan.staging.autosift.cloud/api/work_orders/{}/download/".format(id)
        print(url)
        ucl_setting = frappe.get_single("UCL Settings")

        headers = {
            'client-id': ucl_setting.glib_client_id,
            'client-secret': ucl_setting.glib_client_secret,
        }
        params = {
            "file_type": "json"
        }
        response = requests.get(url, headers=headers, params=params)
        print(response)
        print(response.status_code)
        print(response.json(), "Content")
        print("Download Report")
        if response.status_code == 200:
            print("Request successful!")
            api_log_doc = ucl.log_api(method = "Glib download report", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers) + "\n" ))
        
            ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Third Party", response = str(response.json()))
            details = response.json()['Summary - Fixed Income / Obligation']
            for i in details:
                if i['Type'] == "Salary":
                    salary = i['Amount']
                if i['Type'] == "EMI/LOAN":
                    obligation = i["Amount"]
            print(salary)
            print(obligation)

            return ucl.responder.respondWithSuccess(message=frappe._("success"), data=response.json())
        else:
            return ucl.responder.respondWithFailure(message=frappe._("Failed"), data=response.text)

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()

    