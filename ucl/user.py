import base64
import frappe
import json
from frappe import _
from datetime import datetime, timedelta
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
                "pan_number": ["required"],
                "pan_type": "",
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
                "aadhaar_linked": "decimal|between:0,1"
        })
        api_log_doc = ucl.log_api(method = "Update Pan Details", request_time = datetime.now(), request = str(data))
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
        }
        
        partner_doc = frappe.get_doc("Partner", partner.name).update(partner_dict).save(ignore_permissions = True)
        frappe.db.commit()
        
        response = {"message" : "Pan details updated successfully", "partner" : partner_doc.as_dict()}
        ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = str(response))
            
        return ucl.responder.respondWithSuccess(message=frappe._(response))

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
        }
        partner_doc = frappe.get_doc("Partner", partner.name).update(partner_dict).save(ignore_permissions = True)
        frappe.db.commit()
        
        response = {"message" : "Aadhaar details updated successfully", "partner" : partner_doc.as_dict()}
        ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = str(response))
            
        return ucl.responder.respondWithSuccess(message=frappe._(response))

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
            "same_as_on_pan":"decimal|between:0,1",
            "line1": "",
            "line2": "",
            "street_name": "",
            "pincode": "",
            "city": "",
            "state": "",
            "country": "",
        })
        api_log_doc = ucl.log_api(method = "Update Pan Details", request_time = datetime.now(), request = str(data))
        if data.get("same_as_on_pan") == 1:
            address_dict = {
                "same_as_on_pan" : data.get("same_as_on_pan"),
                "ca_line1" : "",
                "ca_line2": "",
                "ca_street_name": "",
                "ca_pincode": "",
                "ca_city": "",
                "ca_state": "",
                "ca_country": "",
            }
        else:
            address_dict = {
                "same_as_on_pan" : data.get("same_as_on_pan"),
                "ca_line1" : data.get("line1"),
                "ca_line2": data.get("line2"),
                "ca_street_name": data.get("street_name"),
                "ca_pincode": data.get("pincode"),
                "ca_city": data.get("city"),
                "ca_state": data.get("state"),
                "ca_country": data.get("country"),
                }
        

        partner_doc = frappe.get_doc("Partner", partner.name).update(address_dict).save(ignore_permissions = True)
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

        live_image = ucl.attach_files(image_bytes=data.get("image"),file_name = live_picture_file, attached_to_doctype="Partner", attached_to_name=partner.name, attached_to_field="live_image", partner=partner)
        image_path_1 = frappe.utils.get_files_path(live_picture_file)
        partner.live_image = "/files/{}".format(live_picture_file)
        partner.save(ignore_permissions=True)
        frappe.db.commit()
        if partner.pan_card_file:
            path = urlparse(partner.pan_card_file).path
            file_extension = os.path.splitext(path)[1]
            filename = os.path.basename(partner.pan_card_file)
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
                    return ucl.responder.respondWithSuccess(message=frappe._("Faces Match!"))

                else:
                    return ucl.responder.respondUnauthorized(message = "Faces do not match.")
            else:
                return ucl.responder.respondNotFound(message = "No faces detected.")

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    
@frappe.whitelist(allow_guest=True)
def update_company_pan_details(**kwargs):
    try:
        ucl.validate_http_method("POST")
        user = ucl.__user()
        partner = ucl.__partner(user.name)

        data = ucl.validate(
        kwargs,{
            "pan_number": ["required"],
            "pan_type": "",
            "full_name": ["required"],
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
            "dob": "",
        })
        api_log_doc = ucl.log_api(method = "Update Company Pan Details", request_time = datetime.now(), request = str(data))
        company_address_dict = {
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
        }
        
        partner_doc = frappe.get_doc("Partner", partner.name).update(company_address_dict).save(ignore_permissions = True)
        frappe.db.commit()
        response = "Company Pan details updated successfully"
        ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = response)
            
        return ucl.responder.respondWithSuccess(message=frappe._(response))

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()


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
                "business_proof_type" : ["required"]
        })
        file_name = "{}_{}_{}.{}".format(partner.partner_name, data.get("business_proof_type"), randint(1,9),data.get("extension")).replace(" ", "-")
        pan_file_url = ucl.attach_files(image_bytes=data.get("document1"),file_name=file_name,attached_to_doctype="Partner",attached_to_name=partner.name,attached_to_field="business_proof",partner=partner)
        partner.business_proof = "/files/{}".format(file_name)
        partner.save(ignore_permissions=True)
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
        data = ucl.validate(
            kwargs,
            {
                "document1": ["required"],
                "extension" : ["required"]
        })
        file_name = "{}_gst_cert_{}.{}".format(partner.partner_name, randint(1,9),data.get("extension")).replace(" ", "-")
        pan_file_url = ucl.attach_files(image_bytes=data.get("document1"),file_name=file_name,attached_to_doctype="Partner",attached_to_name=partner.name,attached_to_field="company_gst_certificate",partner=partner)
        partner.company_gst_certificate = "/files/{}".format(file_name)
        partner.save(ignore_permissions=True)
        frappe.db.commit()
        return ucl.responder.respondWithSuccess(message=frappe._("GST Certificate processed successfuly"))

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()