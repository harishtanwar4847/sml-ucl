import base64
import frappe
import json
from frappe import _
from datetime import datetime, timedelta
from frappe.utils.password import check_password, update_password
import ucl
import re
from .exceptions import *
import fitz  # PyMuPDF
from PIL import Image
from urllib.parse import urlparse
import os
import face_recognition
import numpy as np
from random import randint
import requests
from ucl import auth


@frappe.whitelist(allow_guest=True)
def update_partner_type(**kwargs):
    try:
        ucl.validate_http_method("POST")
        user = ucl.__user()
        partner = ucl.__partner(user.name)

        data = ucl.validate(
            kwargs,
            {
            "associate": ["required"],
            "parent_partner_name": "",
            "partner_type": "",
            "company_type": "",
        })
        api_log_doc = ucl.log_api(method = "Update Partner Type", request_time = datetime.now(), request = str(data))

        if data.get("associate") == 1:
            if not data.get("parent_partner_name"):
                response = "Please Enter Parent Partner Name."
                raise ucl.exceptions.RespondFailureException(_(response))
            else:
                partner.associate = 1
                partner.parent_partner_code = data.get("parent_partner_name")
                parent_partner = frappe.get_doc("Partner", data.get("parent_partner_name"))
                partner.partner_type = parent_partner.partner_type
                if parent_partner.partner_type == "Corporate":
                    partner.company_type = parent_partner.company_type
                user.remove_roles("Partner")
                user.add_roles("Partner Associate")
                user.save(ignore_permissions=True)
        
        else:
            partner.associate = 0
            if not data.get("partner_type"):
                response = "Please Enter Parent Type."
                raise ucl.exceptions.RespondFailureException(_(response))
            elif data.get("partner_type") == "Corporate" and not data.get("company_type"):
                response = "Please Enter Company Type."
                raise ucl.exceptions.RespondFailureException(_(response))
            elif data.get("partner_type") == "Individual":
                partner.partner_type = data.get("partner_type")
            elif data.get("partner_type") == "Corporate" and data.get("company_type"):
                partner.partner_type = data.get("partner_type")
                partner.company_type = data.get("company_type")
            user.remove_roles("Partner Associate")
            user.add_roles("Partner")
            user.save(ignore_permissions=True)
        partner.save(ignore_permissions = True)
        frappe.db.commit()

        ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = "success")
        return ucl.responder.respondWithSuccess(message=frappe._("success"), data=data)

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()


@frappe.whitelist(allow_guest=True)
def update_pan_details(**kwargs):
    try:
        ucl.validate_http_method("POST")
        user = ucl.__user()
        partner = ucl.__partner(user.name)

        data = ucl.validate(
            kwargs,
            {
                "fathers_name": "",
                "pan_number": ["required" if partner.company_type != "Proprietary Firm" else ""],
                "pan_type": "",
                "full_name": ["required" if partner.company_type != "Proprietary Firm" else ""],
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
                "aadhaar_linked": "decimal|between:0,1"
        })
        api_log_doc = ucl.log_api(method = "Update Pan Details", request_time = datetime.now(), request = str(data))
        if data.get("pan_type") == "Individual":
            partner_dict = {
                "pan_father_name": data.get("fathers_name"),
                "pan_number": data.get("pan_number"),
                "pan_type": data.get("pan_type"),
                "pan_full_name": data.get("full_name"),
                "masked_aadhaar": data.get("masked_aadhaar"),
                "line_1": data.get("address_line_1"),
                "line_2": data.get("address_line_2"),
                "street_name": data.get("address_street_name"),
                "zip": data.get("zip"),
                "pan_city": data.get("city"),
                "pan_state": data.get("state"),
                "pan_country": data.get("country"),
                "pan_full_address": data.get("full_address"),
                "email_id": data.get("email"),
                "pan_phone_number": data.get("phone_number"),
                "pan_gender": data.get("gender"),
                "pan_dob": data.get("dob"),
                "aadhaar_linked": data.get("aadhaar_linked"),
                "kyc_pan_linked": 1
            }
        else:
            partner_dict = {
                "company_pan_number": data.get("pan_number"),
                "company_pan_type": data.get("pan_type"),
                "company_name": data.get("full_name"),
                "company_address_line1": data.get("address_line_1"),
                "company_address_line2": data.get("address_line_2"),
                "company_address_street_name": data.get("address_street_name"),
                "company_address_zip": data.get("zip"),
                "company_address_city": data.get("city"),
                "company_address_state": data.get("state"),
                "company_address_country": data.get("country"),
                "company_full_address": data.get("full_address"),
                "company_email": data.get("email"),
                "company_phone_no": data.get("phone_number"),
                "company_dob": data.get("dob"),
                "kyc_company_pan_linked": 1
            }   
        
        partner_doc = frappe.get_doc("Partner KYC", partner.partner_kyc).update(partner_dict).save(ignore_permissions = True)
        frappe.db.commit()
        
        response = {"message" : "Pan details updated successfully", "partner" : partner_doc.as_dict()}

        ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = str(response))
        return ucl.responder.respondWithSuccess(message=frappe._("Pan details updated successfully"), data = partner_doc.as_dict())    

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    

@frappe.whitelist(allow_guest=True)
def update_aadhaar_details(**kwargs):
    try:
        ucl.validate_http_method("POST")
        user = ucl.__user()
        partner = ucl.__partner(user.name)

        data = ucl.validate(
            kwargs, 
            {
            "address": "",
            "date_of_birth": "",
            "district": "",
            "fathers_name": "",
            "gender": "",
            "house_number": "",
            "id_number": "",
            "name_on_card": "",
            "pincode": "",
            "state": "",
            "street_address": ""
        })
        api_log_doc = ucl.log_api(method = "Update Aadhaar Details", request_time = datetime.now(), request = str(data))
        partner_dict = {
            "aadhaar_address" : data.get("address"),
            "aadhaar_dob": data.get("date_of_birth"),
            "district": data.get("district"),
            "aadhaar_father_name": data.get("fathers_name"),
            "aadhaar_gender": data.get("gender"),
            "house_number": data.get("house_number"),
            "id_number": data.get("id_number"),
            "name_on_card": data.get("name_on_card"),
            "aadhaar_pin_code": data.get("pincode"),
            "aadhaar_state": data.get("state"),
            "street_address": data.get("street_address"),
            "kyc_aadhaar_linked": 1
        }
        partner_doc = frappe.get_doc("Partner KYC", partner.partner_kyc).update(partner_dict).save(ignore_permissions = True)
        frappe.db.commit()
        
        response = {"message" : "Aadhaar details updated successfully", "partner" : partner_doc.as_dict()}
        ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = str(response))
        return ucl.responder.respondWithSuccess(message=frappe._("Aadhaar details updated successfully"), data = partner_doc.as_dict())    

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()


@frappe.whitelist(allow_guest=True)
def update_current_address(**kwargs):
    try:
        ucl.validate_http_method("POST")
        user = ucl.__user()
        partner = ucl.__partner(user.name)

        data = ucl.validate(
            kwargs, 
            {
            "address_proof":"required",
            "extension":"required",
            "same_as_on_pan":"decimal|between:0,1",
            "line1": "",
            "line2": "",
            "street_name": "",
            "pincode": "",
            "city": "",
            "state": "",
            "country": "",
        })
        address_file_name = "{}_address_proof_{}.{}".format(partner.partner_name,randint(1,9),data.get("extension")).replace(" ", "-")

        address_proof_url = ucl.attach_files(image_bytes=data.get("address_proof"),file_name=address_file_name,attached_to_doctype="Partner",attached_to_name=partner.name, attached_to_field="address_proof",partner=partner)
        # partner.address_proof = "/files/{}".format(address_file_name)
        # partner.save(ignore_permissions=True)
        # frappe.db.commit()

        api_log_doc = ucl.log_api(method = "Update Current Address", request_time = datetime.now(), request = str(data))
        if data.get("same_as_on_pan") == 1:
            address_dict = {
                "same_as_on_pan" : data.get("same_as_on_pan"),
                "address_proof" : "/files/{}".format(address_file_name),
                "ca_line1" : "",
                "ca_line2": "",
                "ca_street_name": "",
                "ca_pincode": "",
                "ca_city": "",
                "ca_state": "",
                "ca_country": "",
                "kyc_current_address_linked": 1
            }
        else:
            address_dict = {
                "same_as_on_pan" : data.get("same_as_on_pan"),
                "address_proof" : "/files/{}".format(address_file_name),
                "ca_line1" : data.get("line1"),
                "ca_line2": data.get("line2"),
                "ca_street_name": data.get("street_name"),
                "ca_pincode": data.get("pincode"),
                "ca_city": data.get("city"),
                "ca_state": data.get("state"),
                "ca_country": data.get("country"),
                "kyc_current_address_linked": 1

                }
        

        partner_doc = frappe.get_doc("Partner KYC", partner.partner_kyc).update(address_dict).save(ignore_permissions = True)
        frappe.db.commit()
        response = "Address updated successfully"
        ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = response)
            
        return ucl.responder.respondWithSuccess(message=frappe._(response))

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    
@frappe.whitelist(allow_guest=True)
def face_match(**kwargs):
    try:
        user = ucl.__user()
        partner = ucl.__partner(user.name)

        ucl.validate_http_method("POST")
            
        data = ucl.validate(
            kwargs,
            {
                "image": ["required"],
                "extension": "required"
            },
        )

        live_picture_file = "{}_live_image_{}.{}".format(
            partner.partner_name,randint(1,9),data.get("extension")
        ).replace(" ", "-")
        partner_kyc = frappe.get_doc("Partnern KYC", partner.partner_kyc)

        live_image = ucl.attach_files(image_bytes=data.get("image"),file_name = live_picture_file, attached_to_doctype="Partner KYC", attached_to_name=partner.partner_kyc, attached_to_field="live_image", partner=partner)
        image_path_1 = frappe.utils.get_files_path(live_picture_file)
        partner_kyc.live_image = "/files/{}".format(live_picture_file)
        if partner_kyc.pan_card_file:
            path = urlparse(partner_kyc.pan_card_file).path
            file_extension = os.path.splitext(path)[1]
            filename = os.path.basename(partner_kyc.pan_card_file)
            if file_extension ==".pdf":
            # Specify the input PDF file and output folder
                input_pdf_path = frappe.utils.get_files_path(filename)
                pdf_document = fitz.open(input_pdf_path)
                for page_number in range(pdf_document.page_count):
                    page = pdf_document[page_number]
                    image = page.get_pixmap()
                    pil_image = Image.frombytes("RGB", [image.width, image.height], image.samples)
                    # image_path_2 = f"{output_folder}/{partner.partner_name}_pan_card.jpg"
                    image_path_2 = frappe.utils.get_files_path("{}_pan_card.jpg".format(partner.partner_name))
                    pil_image.save(image_path_2, "JPEG")
                pdf_document.close()
            
            else:
                image_path_2 = frappe.utils.get_files_path(filename)
            
            image_1 = face_recognition.load_image_file(image_path_1)
            image_2 = face_recognition.load_image_file(image_path_2)

            face_locations_1 = face_recognition.face_locations(image_1)
            face_locations_2 = face_recognition.face_locations(image_2)

            face_encodings_1 = face_recognition.face_encodings(image_1, face_locations_1)
            face_encodings_2 = face_recognition.face_encodings(image_2, face_locations_2)

            if len(face_encodings_1) > 0 and len(face_encodings_2) > 0:
                face_encoding_1 = face_encodings_1[0]
                face_encoding_2 = face_encodings_2[0]

                results = face_recognition.compare_faces([face_encoding_1], face_encoding_2)

                if results[0]:
                    partner_kyc.kyc_live_image_linked = 1
                    partner_kyc.save(ignore_permissions=True)                    
                    frappe.db.commit()
                    return ucl.responder.respondWithSuccess(message=frappe._("Faces Match!"))

                else:
                    partner_kyc.live_image =""
                    partner_kyc.kyc_live_image_linked = 0
                    partner_kyc.save(ignore_permissions=True)                    
                    frappe.db.commit()
                    return ucl.responder.respondUnauthorized(message = "Faces do not match.")
            else:
                partner_kyc.live_image =""
                partner_kyc.kyc_live_image_linked = 0
                partner_kyc.save(ignore_permissions=True)                    
                frappe.db.commit()
                return ucl.responder.respondNotFound(message = "No faces detected.")

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    
# @frappe.whitelist(allow_guest=True)
# def update_company_pan_details(**kwargs):
#     try:
#         ucl.validate_http_method("POST")
#         user = ucl.__user()
#         partner = ucl.__partner(user.name)

#         data = ucl.validate(
#         kwargs,{
#             "pan_number": ["required"],
#             "pan_type": "",
#             "full_name": ["required"],
#             "address_line_1": "",
#             "address_line_2": "",
#             "address_street_name": "",
#             "zip": "",
#             "city": "",
#             "state": "",
#             "country": "",
#             "full_address": "",
#             "email": "",
#             "phone_number": "",
#             "dob": "",
#         })
#         api_log_doc = ucl.log_api(method = "Update Company Pan Details", request_time = datetime.now(), request = str(data))
#         company_address_dict = {
#             "company_pan_number": data.get("pan_number"),
#             "company_pan_type": data.get("pan_type"),
#             "company_name": data.get("full_name"),
#             "company_address_line1": data.get("address_line_1"),
#             "company_address_line2": data.get("address_line_2"),
#             "company_address_street_name": data.get("address_street_name"),
#             "company_address_zip": data.get("zip"),
#             "company_address_city": data.get("city"),
#             "company_address_state": data.get("state"),
#             "company_address_country": data.get("country"),
#             "company_full_address": data.get("full_address"),
#             "company_email": data.get("email"),
#             "company_phone_no": data.get("phone_number"),
#             "company_dob": data.get("dob"),
#             "kyc_company_pan_linked": 1
#         }
        
#         partner_doc = frappe.get_doc("Partner", partner.name).update(company_address_dict).save(ignore_permissions = True)
#         frappe.db.commit()
#         response = "Company Pan details updated successfully"
#         ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = response)
            
#         return ucl.responder.respondWithSuccess(message=frappe._(response))

#     except ucl.exceptions.APIException as e:
#         ucl.log_api_error()
        # return e.respond()


@frappe.whitelist(allow_guest=True)
def update_business_proof(**kwargs):
    try:
        ucl.validate_http_method("POST")
        user = ucl.__user()
        partner = ucl.__partner(user.name)
        data = ucl.validate(
            kwargs,
            {
                "document1": ["required"],
                "extension" : ["required"],
                "business_proof_type" : ""
        })
        partner_kyc = frappe.get_doc("Partner KYC", partner.partner_kyc)
        file_name = "{}_{}_{}.{}".format(partner.partner_name, data.get("business_proof_type"), randint(1,9),data.get("extension")).replace(" ", "-")
        file_url = ucl.attach_files(image_bytes=data.get("document1"),file_name=file_name,attached_to_doctype="Partner KYC",attached_to_name=partner.partner_kyc,attached_to_field="business_proof",partner=partner)
        partner_kyc.business_proof = "/files/{}".format(file_name)
        partner_kyc.kyc_business_proof_linked = 1
        partner_kyc.save(ignore_permissions=True)
        frappe.db.commit()
        return ucl.responder.respondWithSuccess(message=frappe._("{} processed successfuly".format(data.get("business_proof_type"))))

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    

@frappe.whitelist(allow_guest=True)
def update_gst_certificate(**kwargs):
    try:
        ucl.validate_http_method("POST")
        user = ucl.__user()
        partner = ucl.__partner(user.name)
        if partner.partner_kyc:
            partner_kyc = frappe.get_doc("Partner KYC", partner.partner_kyc)
        else:
            raise ucl.exceptions.PartnerKYCNotFoundException()
        data = ucl.validate(
            kwargs,
            {
                "document1": ["required" if partner.company_type not in ["Proprietary Firm", "HUF"] else ""],
                "extension" : ["required" if partner.company_type not in ["Proprietary Firm", "HUF"] else ""]
        })
        if data.get("document1"):
            file_name = "{}_gst_cert_{}.{}".format(partner.partner_name, randint(1,9),data.get("extension")).replace(" ", "-")
            file_url = ucl.attach_files(image_bytes=data.get("document1"),file_name=file_name,attached_to_doctype="Partner KYC",attached_to_name=partner_kyc.name,attached_to_field="company_gst_certificate",partner=partner)
            partner_kyc.company_gst_certificate = "/files/{}".format(file_name)
            partner_kyc.kyc_company_gst_certificate_linked = 1
            partner_kyc.save(ignore_permissions=True)
            frappe.db.commit()
            return ucl.responder.respondWithSuccess(message=frappe._("GST Certificate processed successfuly"))
        else:
            partner_kyc.kyc_company_gst_certificate_linked = 1
            partner_kyc.save(ignore_permissions=True)
            frappe.db.commit()
            return ucl.responder.respondWithSuccess(message=frappe._("GST Certificate processed successfuly"))

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    

@frappe.whitelist(allow_guest=True)
def update_bank_details(**kwargs):
    try:
        ucl.validate_http_method("POST")
        user = ucl.__user()
        partner = ucl.__partner(user.name)
        if partner.partner_kyc:
            partner_kyc = frappe.get_doc("Partner KYC", partner.partner_kyc)
        else:
            raise ucl.exceptions.PartnerKYCNotFoundException()
        data = ucl.validate(
            kwargs,
            {
                "document1": ["required" if partner.company_type != "Proprietary Firm" else ""],
                "bank_account_number" : ["required" if partner.company_type != "Proprietary Firm" else ""],
                "bank_name": ["required" if partner.company_type != "Proprietary Firm" else ""],
                "ifsc_code": ["required" if partner.company_type != "Proprietary Firm" else ""],
                "beneficiary_name": ["required" if partner.company_type != "Proprietary Firm" else ""],
                "extension" : ["required" if partner.company_type != "Proprietary Firm" else ""]
        })
        if data.get("document1"):
            file_name = "{}_cancelled_cheque_{}.{}".format(partner.partner_name, randint(1,9),data.get("extension")).replace(" ", "-")
        if data.get("bank_account_number") and data.get("ifsc_code"):
            penny_drop = auth.penny_drop(beneficiary_account_no = data.get("bank_account_number"),beneficiary_ifsc = data.get("ifsc_code"))
            if "verified" in penny_drop:
                if penny_drop["verified"] == True:
                    if data.get("document1"):
                        file_url = ucl.attach_files(image_bytes=data.get("document1"),file_name=file_name,attached_to_doctype="Partner KYC",attached_to_name=partner_kyc.name,attached_to_field="cancelled_cheque",partner=partner)
                    bank_details_dict = {
                        "cancelled_cheque": "/files/{}".format(file_name) if data.get("document1") else "",
                        "bank_account_number" : data.get("bank_account_number"),
                        "bank_name": data.get("bank_name"),
                        "ifsc_code": data.get("ifsc_code"),
                        "beneficiary_name": data.get("beneficiary_name"),
                        "kyc_bank_details_linked": 1
                    }
                    partner_doc = frappe.get_doc("Partner KYC", partner_kyc.name).update(bank_details_dict).save(ignore_permissions = True)
                    frappe.db.commit()
                    return ucl.responder.respondWithSuccess(message=frappe._("Bank details updated successfuly"))
                else:
                    return ucl.responder.respondUnauthorized(message=penny_drop["error_msg"])
            else:
                return ucl.responder.respondUnauthorized(message=penny_drop["message"])
        else:
            partner_kyc.kyc_bank_details_linked = 1
            partner_kyc.save(ignore_permissions = True)
            return ucl.responder.respondWithSuccess(message=frappe._("Bank details updated successfuly"))

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    
@frappe.whitelist(allow_guest=True)
def get_esign_consent():
    try:
        try:
            esign_doc = frappe.get_doc("Consent", "E-sign")
            consent_points = []
            ucl_setting = frappe.get_single("UCL Settings")
            esign_url = frappe.utils.get_url(ucl_setting.digital_agreement)
            for i in esign_doc.esign_consent:
                consent_points.append({"title":i.title, "description":i.description})
            return ucl.responder.respondWithSuccess(
                    message=frappe._("Success"), data={"consent_points" : consent_points, "esign_agreement_url" : esign_url}
                )
            
        except NotFoundException:
            raise ucl.exceptions.NotFoundException()
    except ucl.exceptions.APIException as e:
        frappe.db.rollback()
        ucl.log_api_error()
        return e.respond()
    except frappe.SecurityException as e:
        frappe.db.rollback()
        ucl.log_api_error()
        return ucl.responder.respondUnauthorized(message=str(e))    

    

@frappe.whitelist(allow_guest=True)
def esign_request(**kwargs):
    try:
        user = ucl.__user()
        partner = ucl.__partner(user.name)
        ucl.validate_http_method("POST")

        data = ucl.validate(
            kwargs,
            {
            "consent" : "decimal|between:0,1"
            })
        url = "https://api.digio.in/v2/client/document/upload"
        ucl_setting = frappe.get_single("UCL Settings")

        credentials = f"{ucl_setting.digio_client_id}:{ucl_setting.digio_client_secret}"
        base64_credentials = base64.b64encode(credentials.encode()).decode()
        headers = {
            "authorization": f"Basic {base64_credentials}",
        }
        api_log_doc = ucl.log_api(method = "Esign request", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers) + "\n" ))
        if data.get("consent") == 1:

            signers_data = {
                "signers": [
                    {
                        "identifier": user.name,
                        "name": partner.partner_name,
                        "sign_type": "aadhaar",
                        "reason": "Digio esign test-atriina team"
                    }
                ],
                "comment": "Testing",
                "expire_in_days": 10,
                "sequential": True,
                "display_on_page": "last",
                "notify_signers": True,
                "send_sign_link": True
            }
            esign_file = ucl_setting.digital_agreement.split("/files/")[1]
            files = {
                'file': (esign_file, open(frappe.utils.get_files_path(esign_file), 'rb'), 'application/pdf'),
                'request': (
                    None,
                    json.dumps(signers_data),
                    'text/plain'
                )
            }
            response = requests.post(url, headers=headers, files=files)
            login_consent_doc = frappe.get_doc(
                        {
                            "doctype": "User Consent",
                            "mobile": user.mobile_no,
                            "consent": "E-sign",
                        }
                    ).insert(ignore_permissions=True)
            ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Third Party", response = response.text)

            id = response.json()['id']
            partner.document_id = id
            partner.save(ignore_permissions = True)
            return ucl.responder.respondWithSuccess(message=frappe._("success"), data={"document_id":id,"esign_url":"https://app.digio.in/#/gateway/login/{}/vI3atY/{}?redirect_url=https://atriina.com".format(id,user.name)})

        else:
            ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Third Party", response = "Consent not received")
            return ucl.responder.respondUnauthorized(message="Not received your consent yet. To continue please review agreement once.")
    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()

@frappe.whitelist(allow_guest=True)
def get_esign_details(**kwargs):
    try:
        user = ucl.__user()
        partner = ucl.__partner(user.name)
        ucl.validate_http_method("GET")

        data = ucl.validate(
            kwargs,
            {
            "document_id" : "required"
            })
        
        url = "https://api.digio.in/v2/client/document/{}".format(data.get("document_id"))
        ucl_setting = frappe.get_single("UCL Settings")

        credentials = f"{ucl_setting.digio_client_id}:{ucl_setting.digio_client_secret}"
        base64_credentials = base64.b64encode(credentials.encode()).decode()
        headers = {
            "authorization": f"Basic {base64_credentials}",
            "Content-Type": "application/json"
        }
        print(headers, "headers")

        response = requests.get(url, headers=headers, data=data)
       
        api_log_doc = ucl.log_api(method = "Get Esign details", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers) + "\n" ))
        
        ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Third Party", response = response.text)
        if response.status_code == 200:
            if json.loads(response.text)["agreement_status"] == "completed":
                download_esign_document(data.get("document_id"))
        return ucl.responder.respondWithSuccess(message=frappe._("success"), data=response.json())

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond() 


def download_esign_document(document_id):
    try:
        user = ucl.__user()
        partner = ucl.__partner(user.name)
            
        url = "https://api.digio.in/v2/client/document/download?document_id={}".format(document_id)
        ucl_setting = frappe.get_single("UCL Settings")

        credentials = f"{ucl_setting.digio_client_id}:{ucl_setting.digio_client_secret}"
        base64_credentials = base64.b64encode(credentials.encode()).decode()
        headers = {
            "authorization": f"Basic {base64_credentials}",
            "Content-Type": "application/json"
        }
        payload = {}
        save_path = "/home/dell/Downloads/output.pdf"
        response = requests.get(url, headers=headers)

        file_name = "{}_signed_agreement_{}.pdf".format(partner.partner_name, randint(1,9)).replace(" ", "-")
        file = frappe.get_doc(
            {
                "doctype": "File",
                "file_name": file_name,
                "attached_to_doctype": "Partner",
                "attached_to_name": partner.name,
                "attached_to_field" : "digital_agreement",
                "content" : response.content,
                "is_private": False,
            }
        ).insert(ignore_permissions=True)
        frappe.db.commit()
        partner.digital_agreement = "/files/{}".format(file_name)
        partner.kyc_digital_agreement_linked = 1
        partner.save(ignore_permissions = True)
        api_log_doc = ucl.log_api(method = "Download Esign document", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers) + "\n" + document_id))
        
        ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Third Party", response = "success")

        return ucl.responder.respondWithSuccess(message=frappe._("success"), data=response.content)

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    

@frappe.whitelist()
def reset_pin(**kwargs):
    try:
        ucl.validate_http_method("POST")
        data = ucl.validate(
            kwargs,
            {
                "old_pin": ["required","decimal",ucl.validator.rules.LengthRule(4)],
                "new_pin": ["required","decimal",ucl.validator.rules.LengthRule(4)],
                "retype_pin": ["required","decimal",ucl.validator.rules.LengthRule(4)],
            },
        )

        req = {"old_pin": "****","new_pin": "****","retype_new_pin": "****"}
        api_log_doc = ucl.log_api(method = "Reset Pin", request_time = datetime.now(), request = str(req))
        try:
            user = ucl.__user()
        except UserNotFoundException:
            user = None
            raise ucl.exceptions.UserNotFoundException()
            
        try:
            # returns user in correct case
            old_pass_check = check_password(
                frappe.session.user, data.get("old_pin")
            )
        except frappe.AuthenticationError:
            raise ucl.exceptions.RespondFailureException(_("Invalid current pin."))
        
        if old_pass_check:
            if data.get("retype_pin") == data.get("new_pin") and data.get(
                "old_pin"
            ) != data.get("new_pin"):
                # update pin
                update_password(frappe.session.user, data.get("retype_pin"))
                frappe.db.commit()
                response = "Your pin has been changed successfully!"

            elif data.get("old_pin") == data.get("new_pin"):
                response = "New pin cannot be same as old pin."
                raise ucl.exceptions.RespondFailureException(
                    _(response)
                )
            
            else:
                response = "Retyped pin does not match with new pin"
                raise ucl.exceptions.RespondFailureException(
                    _(response)
                )
            return ucl.responder.respondWithSuccess(
                message=frappe._(response)
            )

        ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = response)
    except ucl.exceptions.APIException as e:
        frappe.db.rollback()
        ucl.log_api_error()
        return e.respond()
    except frappe.SecurityException as e:
        frappe.db.rollback()
        ucl.log_api_error()
        return ucl.responder.respondUnauthorized(message=str(e))
    

@frappe.whitelist(allow_guest=True)
def kyc_submit():
    try:
        user = ucl.__user()
        partner = ucl.__partner(user.name)
        partner_kyc = frappe.get_doc("Partner KYC", partner.partner_kyc)
        ucl.validate_http_method("POST")
        if (partner.partner_type == "Corporate" and partner_kyc.kyc_pan_linked and partner_kyc.kyc_aadhaar_linked and partner_kyc.kyc_company_pan_linked and partner_kyc.kyc_business_proof_linked and partner_kyc.kyc_company_gst_certificate_linked and partner_kyc.kyc_bank_details_linked) or (partner.partner_type == "Individual" and partner_kyc.kyc_live_image_linked and partner_kyc.kyc_pan_linked and partner_kyc.kyc_aadhaar_linked and partner_kyc. kyc_current_address_linked and partner_kyc.kyc_bank_details_linked) or (partner.associate and partner_kyc.kyc_live_image_linked and partner_kyc.kyc_pan_linked and partner_kyc.kyc_aadhaar_linked):
            response = "KYC Successful"
            partner_kyc.status = "Pending"
            partner_kyc.workflow_state = "Pending"
            partner_kyc.save(ignore_permissions=True)
            frappe.db.commit()
        else:
            response = "Please complete the KYC process"
            raise ucl.exceptions.RespondFailureException(
                _(response)
            )
        
        return ucl.responder.respondWithSuccess(
            message=frappe._(response)
        )

    except ucl.exceptions.APIException as e:
        frappe.db.rollback()
        ucl.log_api_error()
        return e.respond()
    except frappe.SecurityException as e:
        frappe.db.rollback()
        ucl.log_api_error()
        return ucl.responder.respondUnauthorized(message=str(e))

