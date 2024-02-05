import base64
import frappe
import json
from frappe import _
from datetime import datetime, timedelta
import ucl
import re
from .exceptions import *
import fitz
from PIL import Image
from urllib.parse import urlparse
import os
import face_recognition
import numpy as np


@frappe.whitelist(allow_guest=True)
def update_partner_type(**kwargs):
    try:
        ucl.validate_http_method("GET")
        user = ucl.__user()
        partner = ucl.__partner(user)

        data = ucl.validate(
        kwargs,{
            "associate": ["required"],
            "parent_partner_name": "",
            "partner_type": "",
            "company_type": "",
        })
        api_log_doc = ucl.log_api(method = "Update Partner Type", request_time = datetime.now(), request = str(data))

        if data.get("associate") == 1:
            if not data.get("parent_partner"):
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
        ucl.validate_http_method("GET")
        user = ucl.__user()
        partner = ucl.__partner(user.name)

        data = ucl.validate(
        kwargs,{
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
            "aadhaar_linked": ["required", "decimal|between:0,1"],
        })
        api_log_doc = ucl.log_api(method = "Save Pan Details", request_time = datetime.now(), request = str(data))
        partner = {
            "fathers_name": data.get("pan_father_name"),
            "pan_number": data.get("pan_number"),
            "pan_type": data.get("pan_type"),
            "full_name": data.get("pan_full_name"),
            "masked_aadhaar": data.get("masked_aadhaar"),
            "address_line_1": data.get("line_1"),
            "address_line_2": data.get("line_2"),
            "address_street_name": data.get("street_name"),
            "zip": data.get("zip"),
            "city": data.get("pan_city"),
            "state": data.get("pan_state"),
            "country": data.get("pan_country"),
            "full_address": data.get("pan_full_address"),
            "email": data.get("email_id"),
            "phone_number": data.get("pan_phone_number"),
            "gender": data.get("pan_gender"),
            "dob": data.get("pan_dob"),
            "aadhaar_linked": data.get("aadhaar_linked"),
        }
        
        response = "Pan details saved successfully"
        ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = response)
            
        return ucl.responder.respondWithSuccess(message=frappe._(response))

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    

@frappe.whitelist(allow_guest=True)
def update_aadhaar_details(**kwargs):
    try:
        ucl.validate_http_method("GET")
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
            "street_address": "",
        })
        api_log_doc = ucl.log_api(method = "Save Pan Details", request_time = datetime.now(), request = str(data))
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
        
        response = {"message" : "Pan details saved successfully", "partner" : partner_doc.as_dict()}
        ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = response)
            
        return ucl.responder.respondWithSuccess(message=frappe._(response))

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()


@frappe.whitelist(allow_guest=True)
def update_current_address(**kwargs):
    try:
        ucl.validate_http_method("GET")
        user = ucl.__user()
        partner = ucl.__partner(user.name)

        data = ucl.validate(
            kwargs, 
            {
            "same_as_on_pan":["required", "decimal|between:0,1"],
            "line1": "",
            "line2": "",
            "street_name": "",
            "pincode": "",
            "city": "",
            "state": "",
            "country": "",
        })
        api_log_doc = ucl.log_api(method = "Save Pan Details", request_time = datetime.now(), request = str(data))
        if data.get("same_as_aadhaar") == 0:
            partner_dict = {
                "ca_line1" : data.get("line1"),
                "ca_line2": data.get("line2"),
                "ca_street_name": data.get("street_name"),
                "ca_pincode": data.get("pincode"),
                "ca_city": data.get("city"),
                "ca_state": data.get("state"),
                "ca_country": data.get("country"),
                }
            
        else:
            partner_dict = {
                "same_as_on_pan" : data.get("same_as_on_pan"),
            }
        

        partner_doc = frappe.get_doc("Partner", partner.name).update(partner_dict).save(ignore_permissions = True)
        frappe.db.commit()
        response = "Pan details saved successfully"
        ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = response)
            
        return ucl.responder.respondWithSuccess(message=frappe._(response))

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    
@frappe.whitelist(allow_guest=True)
def face_match(**kwargs):
    try:
        user = ucl.__user("8708759004")
        partner = ucl.__partner(user.name)

        ucl.validate_http_method("POST")
            
        data = ucl.validate(
            kwargs,
            {
                "image": ["required"],
                "extension": "required"
            },
        )

        live_picture_file = "{}_live_image.{}".format(
            partner.partner_name,data.get("extension")
        ).replace(" ", "-")

        live_image = ucl.attach_files(image_bytes=data.get("image"),file_name = live_picture_file, attached_to_doctype="Partner", attached_to_name=partner.name, attached_to_field="live_image", partner=partner)
        image_path_1 = frappe.utils.get_files_path(live_picture_file)
        if partner.pan_card_file:
            path = urlparse(partner.pan_card_file).path
            file_extension = os.path.splitext(path)[1]

            if file_extension ==".pdf":
            # Specify the input PDF file and output folder
                input_pdf_path = frappe.utils.get_files_path(partner.pan_card_file)
                # output_folder = frappe.utils.get_files_path("/files")
                
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
                image_path_2 = frappe.utils.get_files_path(partner.pan_card_file)
            
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