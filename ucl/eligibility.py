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
def mobile_check(**kwargs):
    try:
        ucl.validate_http_method("POST")
        user = ucl.__user()
        data = ucl.validate(
            kwargs,
            {
            "mobile" : ["required", "decimal", ucl.validator.rules.LengthRule(10)]
        })
        
        api_log_doc = ucl.log_api(method = "Mobile No Check", request_time = datetime.now(), request = str(data))
        if frappe.db.exists("Lead", {"mobile_number" : data.get("mobile")}):
            lead = frappe.get_last_doc("Lead", filters={"mobile_number" : data.get("mobile")})
            details = {
                "pan_number": lead.pan_number,
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "gender": lead.gender,
                "dob": lead.dob,
                "address": lead.address 
            }
        else:
            details = "No Lead found with this Mobile No."
        ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = str(details))
        return ucl.responder.respondWithSuccess(message=frappe._("Success"), data=details)
    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    

@frappe.whitelist(allow_guest=True)
def pan_plus(**kwargs):
    try:
        ucl.validate_http_method("POST")
        user = ucl.__user()
        data = ucl.validate(
            kwargs,
            {
            "pan_number" : "required"
        })
        ucl_setting = frappe.get_single("UCL Settings")

        url = "https://production.deepvue.tech/v1/verification/pan-plus?pan_number=" + data.get("pan_number")
    
        payload={}
        headers = {'Authorization': ucl_setting.bearer_token,'x-api-key': ucl_setting.deepvue_client_secret,}
        response = requests.request("GET", url, headers=headers, data=payload)
        api_log_doc = ucl.log_api(method = "Pan Plus", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers)))
        if response.status_code == 200:
            ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Third Party", response = str(response.json()))
            return ucl.responder.respondWithSuccess(message=frappe._("Pan Verified Successfully."), data=response.json()['data'])
        else:
            return ucl.responder.respondWithFailure(message=frappe._("Failed"), data=response.json())

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    

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
                "pan_number": "required",
                "first_name": "required",
                "last_name": "",
                "gender": "required",
                "dob": "required",
                "address": "required"
        })
        api_log_doc = ucl.log_api(method = "Mobile No Check", request_time = datetime.now(), request = str(data))
        eligibility_doc = frappe.get_doc(
            {
                "doctype": "Eligibility Check",
                "mobile_no": data.get("mobile"),
                "product": data.get("product"),
                "pan_number": data.get("pan_number"),
                "first_name": data.get("first_name"),
                "last_name": data.get("last_name"),
                "gender": data.get("gender"),
                "dob": data.get("dob"),
                "address": data.get("address")
            }
        ).insert(ignore_permissions=True)
        frappe.db.commit()
        ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Third Party", response = str(eligibility_doc))
        return ucl.responder.respondWithSuccess(message=frappe._("Basic eligibility details updated successfuly"))

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    

@frappe.whitelist(allow_guest=True)
def update_loan_details(**kwargs):
    try:
        ucl.validate_http_method("POST")
        user = ucl.__user()
        data = ucl.validate(
            kwargs,
            {
                "occupation_type": "required",
                "requested_loan_amount" : "required",
                "monthly_salary" : "required",
                "monthly_gross_income": "required",
                "running_loan": "required",
                "lender_name": "",
                "pos": "required",
                "sanctioned_loan_amount": "required",
                "emi": "required",
                "total_emis_paid": "required",
                "co_applicant": "required"
        })
        api_log_doc = ucl.log_api(method = "Mobile No Check", request_time = datetime.now(), request = str(data))
        eligibility_doc = frappe.get_doc(
            {
                "occupation_type": data.get("occupation_type"),
                "requested_loan_amount" : data.get("requested_loan_amount"),
                "monthly_salary" : data.get("monthly_salary"),
                "monthly_gross_income": data.get("monthly_gross_income"),
                "running_loan": data.get("running_loan"),
                "lender_name": data.get("lender_name"),
                "pos": data.get("pos"),
                "sanctioned_loan_amount": data.get("sanctioned_loan_amount"),
                "emi": data.get("emi"),
                "total_emis_paid": data.get("total_emis_paid"),
                "co_applicant": data.get("co_applicant")
        }
        ).insert(ignore_permissions=True)
        frappe.db.commit()
        ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Third Party", response = str(eligibility_doc))
        return ucl.responder.respondWithSuccess(message=frappe._("Loan details updated successfuly"))

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    

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
        user = ucl.__user()
        ucl.validate_http_method("POST")
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
            "coApplicantProfile": "",
            "coApplicantTotalNetIncome": "required",
            "creditReportXml": ""
        })
        print(user)
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

        response = requests.request("POST", url, headers=headers, json=payload)
        api_log_doc = ucl.log_api(method = "BRE Offers", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers)))
        if response.status_code == 200:
            ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Third Party", response = str(response.json()))
            return ucl.responder.respondWithSuccess(message=frappe._("Offers Successfully Generated"), data=response.json()['offers'])
        else:
            return ucl.responder.respondWithFailure(message=frappe._("Failed"), data=response.text)

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
        api_log_doc = ucl.log_api(method = "Glib create workorder", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers) + "\n" ))
        if response.status_code == 201:        
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
        api_log_doc = ucl.log_api(method = "Glib add bank statement", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers) + "\n" ))
        if response.status_code == 200:        
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
        api_log_doc = ucl.log_api(method = "Glib process workorder", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers) + "\n" ))
        if response.status_code == 200:        
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
        api_log_doc = ucl.log_api(method = "Glib retrieve workorder", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers) + "\n" ))
        if response.status_code == 200:        
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
        api_log_doc = ucl.log_api(method = "Glib download report", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers) + "\n" ))
        if response.status_code == 200:     
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
    

@frappe.whitelist(allow_guest=True)
def ibb_make(**kwargs):
    try:
        user = ucl.__user()
        ucl.validate_http_method("POST")
        data = ucl.validate(
            kwargs,{
            "year": "required", 
            "month": "required"
        },
        )
        url = "https://system.indianbluebook.com/api/SwitchMyLoan"
        ucl_setting = frappe.get_single("UCL Settings")

        payload = {
            "for": "make", 
            "year": data.get("year"), 
            "month": data.get("month"), 
            "access_token": ucl_setting.ibb_token 
        }
        
        response = requests.request("POST", url, data=payload)
        api_log_doc = ucl.log_api(method = "IBB Make API", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(payload) + "\n" ))          
        if response.status_code == 200:
            ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Third Party", response = str(response.json()))
            return ucl.responder.respondWithSuccess(message=frappe._("success"), data=response.json()['make'])
        else:
            return ucl.responder.respondWithFailure(message=frappe._("Failed"), data=response.text)
        
    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    

@frappe.whitelist(allow_guest=True)
def ibb_model(**kwargs):
    try:
        user = ucl.__user()
        ucl.validate_http_method("POST")
        data = ucl.validate(
            kwargs,{
            "year":"required", 
            "month":"required", 
            "make": "required"        },
        )
        url = "https://system.indianbluebook.com/api/SwitchMyLoan"
        ucl_setting = frappe.get_single("UCL Settings")

        payload = {
            "for": "model", 
            "year": data.get("year"), 
            "month": data.get("month"), 
            "make": data.get("make"),
            "access_token": ucl_setting.ibb_token 
        }        
        response = requests.request("POST", url, data=payload)
        api_log_doc = ucl.log_api(method = "IBB Model API", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(payload) + "\n" ))          
        if response.status_code == 200:
            ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Third Party", response = str(response.json()))
            return ucl.responder.respondWithSuccess(message=frappe._("success"), data=response.json()['model'])
        else:
            return ucl.responder.respondWithFailure(message=frappe._("Failed"), data=response.text)
        
    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    

@frappe.whitelist(allow_guest=True)
def ibb_variant(**kwargs):
    try:
        user = ucl.__user()
        ucl.validate_http_method("POST")
        data = ucl.validate(
            kwargs,{
            "year":"required", 
            "month":"required", 
            "make": "required",
            "model": "required"
        },
        )
        url = "https://system.indianbluebook.com/api/SwitchMyLoan"
        ucl_setting = frappe.get_single("UCL Settings")

        payload = {
            "for": "variant", 
            "year": data.get("year"), 
            "month": data.get("month"), 
            "make": data.get("make"),
            "model": data.get("model"),
            "access_token": ucl_setting.ibb_token 
        }        
        response = requests.request("POST", url, data=payload)
        api_log_doc = ucl.log_api(method = "IBB Variant API", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(payload) + "\n" ))          
        if response.status_code == 200:
            ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Third Party", response = str(response.json()))
            return ucl.responder.respondWithSuccess(message=frappe._("success"), data=response.json()['variant'])
        else:
            return ucl.responder.respondWithFailure(message=frappe._("Failed"), data=response.text)
        
    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    

@frappe.whitelist(allow_guest=True)
def ibb_location(**kwargs):
    try:
        user = ucl.__user()
        url = "https://system.indianbluebook.com/api/SwitchMyLoan"
        ucl_setting = frappe.get_single("UCL Settings")

        payload = {
            "for": "city",
            "access_token": ucl_setting.ibb_token 
        }        
        response = requests.request("POST", url, data=payload)
        api_log_doc = ucl.log_api(method = "IBB Location API", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(payload) + "\n" ))          
        if response.status_code == 200:
            ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Third Party", response = str(response.json()))
            return ucl.responder.respondWithSuccess(message=frappe._("success"), data=response.json()['city'])
        else:
            return ucl.responder.respondWithFailure(message=frappe._("Failed"), data=response.text)
        
    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    

@frappe.whitelist(allow_guest=True)
def ibb_color(**kwargs):
    try:
        user = ucl.__user()
        url = "https://system.indianbluebook.com/api/SwitchMyLoan"
        ucl_setting = frappe.get_single("UCL Settings")

        payload = {
            "for": "color",
            "access_token": ucl_setting.ibb_token 
        }        
        response = requests.request("POST", url, data=payload)
        api_log_doc = ucl.log_api(method = "IBB Color API", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(payload) + "\n" ))          
        if response.status_code == 200:
            ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Third Party", response = str(response.json()))
            return ucl.responder.respondWithSuccess(message=frappe._("success"), data=response.json()['color'])
        else:
            return ucl.responder.respondWithFailure(message=frappe._("Failed"), data=response.text)
        
    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()



@frappe.whitelist(allow_guest=True)
def ibb_price(**kwargs):
    try:
        user = ucl.__user()
        ucl.validate_http_method("POST")
        data = ucl.validate(
            kwargs,{
            "year": "required", 
            "month": "required", 
            "make": "required", 
            "model": "required", 
            "variant": "", 
            "location": "required", 
            "color": "required", 
            "owner": "required", 
            "kilometer": "required", 
        },
        )
        url = "https://system.indianbluebook.com/api/SwitchMyLoan"
        ucl_setting = frappe.get_single("UCL Settings")

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
        print(payload)
        
        response = requests.request("POST", url, data=payload)
        api_log_doc = ucl.log_api(method = "IBB Price API", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(payload) + "\n" ))          
        if response.status_code == 200:
            ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Third Party", response = str(response.json()))
            return ucl.responder.respondWithSuccess(message=frappe._("success"), data=response.json()['retail'])
        else:
            return ucl.responder.respondWithFailure(message=frappe._("Failed"), data=response.text)
        
    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    



    