import base64
import os
from random import randint
import frappe
import json
from frappe import _
from datetime import datetime, timedelta
import ucl
import re
from .exceptions import *
from frappe.auth import LoginAttemptTracker, get_login_attempt_tracker
from pdf2image import convert_from_path
from frappe.utils.password import (
    check_password,
    delete_login_failed_cache,
    update_password,
)

@frappe.whitelist(allow_guest=True)
def verify_email(**kwargs):
    try:
        ucl.validate_http_method("POST")
        
        data = ucl.validate(
            kwargs,
            {
                "mobile": ["required"],
                "email": ["required"],
                # "resend": ["required"],
                "first_name": ["required"],
                "last_name": ""
            },
        )

        if frappe.db.exists("User Token", {"entity" : data.get("mobile"), "used": 1}):
            api_log_doc = ucl.log_api(method = "Verify Email", request_time = datetime.now(), request = str(data))

            email_regex = (
                r"^([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})"
            )
            if re.search(email_regex, data.get("email")) is None or (
                len(data.get("email").split("@")) > 2
            ):
                raise ucl.exceptions.FailureException(_("Please enter valid email ID."))
            
            # if data.get("resend") == 1:
            #     return ucl.responder.respondForbidden(message=frappe._("User already exists with this mobile no."), data = {})

            
            if not frappe.db.exists("User", {"name" : data.get("email")}):
                ucl.create_user(first_name = data.get("first_name"),last_name = data.get("last_name"),email = data.get("email"),mobile = data.get("mobile"),)

                try:
                    user = ucl.__user(data.get("mobile"))
                except UserNotFoundException:
                    user = None

                token = dict(
                        token=ucl.create_user_access_token(user.name)
                    )
                
                ucl.create_partner(first_name = user.full_name, mobile = user.mobile_no, email = user.name, user = user.name)
                    
                ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = "User Created Successfully")

                return ucl.responder.respondWithSuccess(
                        message=frappe._("User Created Successfully"), data=token
                    )
            else:
                ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = "User already exists")
                return ucl.responder.respondForbidden(
                    message=frappe._("User already exists"), data = {}
                )
        
        else:
            ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = "Please verify your mobile no.")
            return ucl.responder.respondWithFailure(
                    message=frappe._("Please verify your mobile no."), data = []
                )
    

    except (ucl.ValidationError, ucl.ServerError) as e:
        ucl.log_api_error()
        return ucl.generateResponse(status=e.http_status_code, message=str(e))
    except Exception as e:
        ucl.log_api_error()
        return ucl.generateResponse(is_success=False, error=e)
    

@frappe.whitelist()
def request_verification_email():
    try:
        # validation
        ucl.validate_http_method("POST")


        ucl.create_user_token(
            entity=frappe.session.user,
            token=ucl.random_token(),
            token_type="Email Verification Token",
        )

        return ucl.generateResponse(message=frappe._("Verification email sent"))
    except (ucl.ValidationError, ucl.ServerError) as e:
        ucl.log_api_error()
        return ucl.generateResponse(status=e.http_status_code, message=str(e))
    except Exception as e:
        ucl.log_api_error()
        return ucl.generateResponse(is_success=False, error=e)
    

@frappe.whitelist(allow_guest=True)
def verify_otp(**kwargs):
    try:
        ucl.validate_http_method("POST")

        data = ucl.validate(
            kwargs,
            {
                "mobile": ["required", "decimal", ucl.validator.rules.LengthRule(10)],
                "firebase_token": "required",
                "otp": ["required", "decimal", ucl.validator.rules.LengthRule(4)],
                "platform": "",
                "app_version": "",
            },
        )
        if data.get("firebase_token"):
            reg = ucl.regex_special_characters(
                search=data.get("firebase_token"),
                regex=re.compile("[@!#$%^&*()<>?/\|}{~`]"),
            )
            if reg:
                return ucl.responder.respondWithFailure(
                    status=422,
                    message=frappe._("Special Characters not allowed."),
                )
                

        # try:
        #     is_dummy_account = lms.validate_spark_dummy_account(data.get("mobile"))
        #     if not is_dummy_account:
        token = ucl.verify_user_token(
            entity=data.get("mobile"), token=data.get("otp"), token_type="Login OTP"
        )
        #    else:
        #         token = lms.validate_spark_dummy_account_token(
        #             data.get("mobile"), data.get("otp")
        #         )
        # except InvalidUserTokenException:
        #     token = None
        try:
            user = ucl.__user(data.get("mobile"))
        except:
            user = None

        api_log_doc = ucl.log_api(method = "Verify OTP", request_time = datetime.now(), request = str(data))

        if not token:
            response = "Invalid OTP."
            message = frappe._(response)

            if user:
                LoginAttemptTracker(user_name=user.name).add_failure_attempt()
                if not user.enabled:
                    raise ucl.exceptions.UnauthorizedException(
                        _("User disabled or missing")
                    )

                invalid_login_attempts = get_login_attempt_tracker(user.name)
                if invalid_login_attempts.login_failed_count > 0:
                    message += " {} invalid {}.".format(
                        invalid_login_attempts.login_failed_count,
                        "attempt"
                        if invalid_login_attempts.login_failed_count == 1
                        else "attempts",
                                   empty_token = {}
                )
            ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = "Invalid OTP.")
            raise ucl.exceptions.UnauthorizedException(message)

        if token:
            # frappe.db.begin()
            # if (not is_dummy_account) and (token.expiry <= frappe.utils.now_datetime()):
            if token.expiry <= frappe.utils.now_datetime():
                response = "OTP Expired"

                raise ucl.exceptions.UnauthorizedException(response)
            
            user_data = {}
            if user:
                access_token = ucl.create_user_access_token(user.name)
                user_data = {
                        "first_name":user.first_name,
                        "last_name":user.last_name,
                        "email":user.name,
                        "token":access_token,
                        "role":frappe.get_roles(user.name)
                    }
                if "Partner" in frappe.get_roles(user.name) or "Partner Associate" in frappe.get_roles(user.name):
                    partner = ucl.__partner(user.name)
                    user_data['partner'] = partner.as_dict()
            
            # else:
            #     user_data = {}

            # if not is_dummy_account:
            #     token.used = 1
            #     token.save(ignore_permissions=True)

            app_version_platform = ""
            if data.get("app_version") and data.get("platform"):
                app_version_platform = (
                    data.get("app_version") + " | " + data.get("platform")
                )
            # ucl.add_firebase_token(
            #     data.get("firebase_token"), app_version_platform, data.get("mobile")
            # )
            ucl.token_mark_as_used(token)
            response = "OTP Verified" + "\n" + str(data)
            ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = response)
            return ucl.responder.respondWithSuccess(message=frappe._("OTP Verified"), data = user_data if user_data else {})    

    except ucl.exceptions.APIException as e:
        frappe.db.rollback()
        ucl.log_api_error()
        return e.respond()
    except frappe.SecurityException as e:
        frappe.db.rollback()
        ucl.log_api_error()
        return ucl.respondUnauthorized(message=str(e))

@frappe.whitelist(allow_guest=True)
def set_pin(**kwargs):
    try:
        ucl.validate_http_method("POST")
    
        data = ucl.validate(
            kwargs,
            {
                "pin": ["required", "decimal", ucl.validator.rules.LengthRule(4)],
            },
        )

        api_log_doc = ucl.log_api(method = "Set Pin", request_time = datetime.now(), request = str(data))

        try:
            user = ucl.__user()
        except frappe.DoesNotExistError:
            raise ucl.exceptions.UserNotFoundException()

        if not user.enabled:
            response
            response = "User disabled or missing"
            ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = response)
            raise ucl.exceptions.UnauthorizedException(_(response))

        # try:
        #     is_dummy_account = lms.validate_spark_dummy_account(
        #         user.username, data.get("email"), check_valid=True
        #     )
        #     if not is_dummy_account:
        #         token = lms.verify_user_token(
        #             entity=data.get("email"),
        #             token=data.get("otp"),
        #             token_type="Forgot Pin OTP",
        #         )
        #     else:
        #         token = lms.validate_spark_dummy_account_token(
        #             user.username, data.get("otp"), token_type="Forgot Pin OTP"
        #         )
        # except InvalidUserTokenException:
        #     # raise utils.respondForbidden(message=frappe._("Invalid Forgot Pin OTP."))
        #     raise lms.exceptions.ForbiddenException(_("Invalid Forgot Pin OTP"))

        # # frappe.db.begin()

        # if token and not is_dummy_account:
        #     if token.expiry <= frappe.utils.now_datetime():
        #         # return utils.respondUnauthorized(message=frappe._("OTP Expired."))
        #         raise lms.exceptions.UnauthorizedException(_("OTP Expired"))

        if data.get("pin"):
            if data.get("pin"):
                update_password(user.name, data.get("pin"))
                if frappe.db.exists("Partner", {"user_id" : user.name}):
                    partner = ucl.__partner(user.name)
                    partner.is_pin_set = 1
                    partner.save(ignore_permissions=True)
                response = "User PIN has been updated."
                ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = response)

                return ucl.responder.respondWithSuccess(
                    message=frappe._(response)
                )

        else:
            response = "Please Enter value for pin."
            ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = response)
            raise ucl.exceptions.RespondFailureException(
                _(response)
            )
        # if not is_dummy_account:
        #     lms.token_mark_as_used(token)

    except ucl.exceptions.APIException as e:
        frappe.db.rollback()
        ucl.log_api_error()
        return e.respond()
    
    
@frappe.whitelist(allow_guest=True)
def verify_forgot_pin_otp(**kwargs):
    try:
        ucl.validate_http_method("POST")

        data = ucl.validate(
            kwargs,
            {
                "otp": ["required", "decimal", ucl.validator.rules.LengthRule(4)],
                "new_pin": ["required", "decimal", ucl.validator.rules.LengthRule(4)],
            },
        )
        api_log_doc = ucl.log_api(method = "Verify Forgot Pin OTP", request_time = datetime.now(), request = str(data))

        try:
            user = ucl.__user()
        except frappe.DoesNotExistError:
            raise ucl.exceptions.UserNotFoundException()

        if not user.enabled:
            response = "User disabled or missing"
            ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = response)
            raise ucl.exceptions.UnauthorizedException(_(response))

        try:
            # is_dummy_account = ucl.validate_spark_dummy_account(
            #     user.username, data.get("email"), check_valid=True
            # )
            # if not is_dummy_account:
            token = ucl.verify_user_token(
                entity=user.mobile_no,
                token=data.get("otp"),
                token_type="Forgot Pin OTP",
            )
            # else:
            #     token = ucl.validate_spark_dummy_account_token(
            #         user.username, data.get("otp"), token_type="Forgot Pin OTP"
            #     )
        except InvalidUserTokenException:
            response = "Invalid Forgot Pin OTP"
            ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = response)
            raise ucl.exceptions.ForbiddenException(_(response))


        if token:
            if token.expiry <= frappe.utils.now_datetime():
                response = "OTP Expired"
                ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = response)
                raise ucl.exceptions.UnauthorizedException(_(response))

        if data.get("otp") and data.get("new_pin"):
            if data.get("new_pin"):
                update_password(user.name, data.get("new_pin"))
                response = "User PIN has been updated."
                ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = response)
                ucl.token_mark_as_used(token)
                return ucl.responder.respondWithSuccess(
                    message=frappe._(response)
                )


        elif not data.get("new_pin"):
            response = "Please Enter value for new pin."
            ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = response)
            raise ucl.exceptions.RespondFailureException(
                _(response)
            )

    except ucl.exceptions.APIException as e:
        frappe.db.rollback()
        ucl.log_api_error()
        return e.respond()
    

@frappe.whitelist(allow_guest=True)
def login(**kwargs):
    try:
        ucl.validate_http_method("POST")
        data = ucl.validate(
            kwargs,
            {
                "pin": [ucl.validator.rules.LengthRule(4)],
                "firebase_token": [ucl.validator.rules.RequiredIfPresent("pin")],
                # "accept_terms": "decimal|between:0,1",
                "platform": "",
                "app_version": "",
            },
        )

        api_log_doc = ucl.log_api(method = "Login", request_time = datetime.now(), request = str(data))
        if data.get("firebase_token"):
            reg = ucl.regex_special_characters(
                search=data.get("firebase_token"),
                regex=re.compile("[@!#$%^&*()<>?/\|}{~`]"),
            )
            if reg:
                response = "Special Characters not allowed."
                ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = response)
                raise ucl.exceptions.FailureException(
                    _(response)
                )

        try:
            user = ucl.__user()
        except UserNotFoundException:
            user = None
            raise ucl.exceptions.UserNotFoundException()
            

        # frappe.db.begin()
        if data.get("pin"):
            try:
                frappe.local.login_manager.authenticate(
                    user=user.name, pwd=data.get("pin")
                )
            except frappe.SecurityException as e:
                response = "Incorrect PIN."
                ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = response)
                raise ucl.exceptions.UnauthorizedException(str(e))
            except frappe.AuthenticationError as e:
                response = "Incorrect PIN."
                message = frappe._(response)
                ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = response)
                invalid_login_attempts = get_login_attempt_tracker(user.name)
                if invalid_login_attempts.login_failed_count > 0:
                    message += " {} invalid {}.".format(
                        invalid_login_attempts.login_failed_count,
                        "attempt"
                        if invalid_login_attempts.login_failed_count == 1
                        else "attempts",
                    )
                raise ucl.exceptions.UnauthorizedException(message)

            token = dict(
                token=ucl.create_user_access_token(user.name)
            )
            app_version_platform = ""
            if data.get("app_version") and data.get("platform"):
                app_version_platform = (
                    data.get("app_version") + " | " + data.get("platform")
                )
            response = "Logged in Successfully"
            ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = response)
            return ucl.responder.respondWithSuccess(
                message=frappe._(response), data=token
            )
        else:
            if not data.get("accept_terms"):
                response = "Please accept Terms of Use and Privacy Policy."
                ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = response)
                raise ucl.exceptions.UnauthorizedException(
                    _(response)
                )

        ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = response)
        # # check if dummy account
        # is_dummy_account = lms.validate_spark_dummy_account(data.get("mobile"))

        # if not is_dummy_account:
        #     lms.create_user_token(
        #         entity=data.get("mobile"),
        #         token=lms.random_token(length=4, is_numeric=True),
        #     )

        # frappe.db.commit()
        # return utils.respondWithSuccess(message=frappe._("OTP Sent"))
    except ucl.exceptions.APIException as e:
        frappe.db.rollback()
        ucl.log_api_error()
        return e.respond()
    except frappe.SecurityException as e:
        frappe.db.rollback()
        ucl.log_api_error()
        return ucl.responder.respondUnauthorized(message=str(e))
    

@frappe.whitelist(allow_guest=True)
def get_user_details(**kwargs):
    try:
        try:
            user = ucl.__user()
        except UserNotFoundException:
            user = None
            raise ucl.exceptions.UserNotFoundException()
            
        api_log_doc = ucl.log_api(method = "User details", request_time = datetime.now(), request = str(user))
      
        if user:
            user_doc = frappe.get_doc("User", user.name).as_dict()
            if frappe.db.exists("Partner", {"user_id": user.name}):
                partner = ucl.__partner(user.name)
                partner_doc = frappe.get_doc("Partner", partner.name)
                user_doc.partner = partner_doc.as_dict()
                response = "User details" + "\n" + str(user_doc)
                return ucl.responder.respondWithSuccess(
                message=frappe._("User details"), data = user_doc
            )
            else:
                user_doc = frappe.get_doc("User", user.name).as_dict()
                user_doc.partner = None
                response = "User details" + "\n" + str(user_doc)
                return ucl.responder.respondWithSuccess(
                message=frappe._("User details"), data = user_doc
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
def verify_user(token, user):
    token_document = frappe.db.get_all(
        "User Token",
        filters={
            "entity": user,
            "token_type": "Email Verification Token",
            "token": token,
            # "used": 0,
        },
        fields=["*"],
    )

    url = frappe.utils.get_url("/everify")
    if token_document:
        if token_document[0].used == 0:
            url = frappe.utils.get_url("/everify?success")
            frappe.db.set_value("User Token", token_document[0].name, "used", 1)
            usr = frappe.get_doc("User", user)
            ucl.create_partner(first_name = usr.full_name, mobile = usr.mobile_no, email = usr.name, user = usr.name)
            frappe.db.commit()

        elif token_document[0].used == 1:
            url = frappe.utils.get_url("/everify?already-verified")

    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = url


@frappe.whitelist(allow_guest=True)
def get_lender_list():
    try:
        try:
            lender = ucl.lender_list()
            return ucl.responder.respondWithSuccess(
                    message=frappe._("List"), data=lender
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
def get_bank_list():
    try:
        try:
            bank = ucl.bank_list()
            return ucl.responder.respondWithSuccess(
                    message=frappe._("List"), data=bank
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
def get_pincode_list():
    try:
        try:
            pincode = ucl.pincode_list()
            return ucl.responder.respondWithSuccess(
                    message=frappe._("List"), data=pincode
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
def get_employer_list():
    try:
        try:
            employer = ucl.employer_list()
            return ucl.responder.respondWithSuccess(
                    message=frappe._("List"), data=employer
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
def terms_of_use_nd_privacy_policy():
    try:
        ucl.validate_http_method("GET")
        ucl_setting = frappe.get_single("UCL Settings")

        data = {
            "terms_of_use": frappe.utils.get_url(ucl_setting.terms_of_use)
            or "",
            "privacy_policy": frappe.utils.get_url(
                ucl_setting.privacy_policy
            )
        }
        return ucl.responder.respondWithSuccess(message=frappe._("success"), data=data)

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    
@frappe.whitelist(allow_guest=True)
def pan_plus(pan_number):
    import requests
    try:
        ucl_setting = frappe.get_single("UCL Settings")

        url = "https://production.deepvue.tech/v1/verification/pan-plus?pan_number=" + (pan_number)
    
        payload={}
        headers = {'Authorization': ucl_setting.bearer_token,'x-api-key': ucl_setting.deepvue_client_secret,}
        api_log_doc = ucl.log_api(method = "Pan Plus", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers)))

        response = requests.request("GET", url, headers=headers, data=payload)
        ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Third Party", response = response.text)
        return response.json()

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()

    
@frappe.whitelist(allow_guest=True)
def pan_ocr(**kwargs):
    import requests
    try:
        ucl.validate_http_method("POST")
        user = ucl.__user("8888888888")
        partner = ucl.__partner(user.name)

        data = ucl.validate(
            kwargs,
            {
                "document1": ["required"],
                "document2": "",
                "name": "",
                "extension" : ['required']
        })
        pan_file = "{partner}_pan_card_{rand}.{extension}".format(partner = partner.partner_name, rand = randint(1,99), extension = data.get("extension")).replace(" ", "-")
        pan_file_path = frappe.utils.get_files_path(pan_file)
        pan_file_url = frappe.utils.get_url("files/{file_name}".format(file_name = pan_file).replace(" ", "-"))

        base64_encoded_image = data.get("document1")
        decoded_image = base64.b64decode(base64_encoded_image)
        with open(pan_file_path, "wb") as output_image_file:
            output_image_file.write(decoded_image)
        
        images = convert_from_path(pan_file_path)
        image_file = "{partner}_pan_card_{rand}.png".format(partner = partner.partner_name, rand = randint(1,99)).replace(" ", "-")
        for i, image in enumerate(images):
            image.save(image_file, "PNG")
        
        file = frappe.get_doc(
				{
					"doctype": "File",
					"file_name": image_file,
					"attached_to_doctype": "Partner",
					"attached_to_name": partner.name,
                    "attached_to_field" : partner.pan_card_file,
					"content": decoded_image,
					"is_private": False,
				}
			).insert(ignore_permissions=True)
        frappe.db.commit()

        data["document1"] = frappe.utils.get_url(file.file_url)

        # image_path = frappe.utils.get_files_path(pan_file)
        # if os.path.exists(image_path):
        #     os.remove(image_path)
        # image_decode = base64.decodestring(data.get("document1"))
        # image_file = open(pan_file_path, "wb").write(image_decode)
        print(data["document1"])
        ucl_setting = frappe.get_single("UCL Settings")
        url = "https://production.deepvue.tech/v1/documents/extraction/ind_pancard" 
        headers = {'Authorization': ucl_setting.bearer_token,'x-api-key': ucl_setting.deepvue_client_secret,}

        api_log_doc = ucl.log_api(method = "Pan OCR", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers) + "\n" + str(data)))

        ocr_response = requests.request("POST", url, headers=headers, json=data)
        print(ocr_response.json())
        ucl.log_api_error(ocr_response.json())

        if ocr_response.json()['data']:
            id_number = ocr_response.json()["data"]["id_number"]
            pan_plus_response = pan_plus(id_number)

            response = pan_plus_response["data"]
            # response["fathers_name"] = ocr_response.json()['data']["fathers_name"]
            response["pan_type"] = ocr_response.json()['data']["pan_type"]
        else:
            ucl.log_api_error(mess = response)
            response = ocr_response
        ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Third Party", response = str(response))
    
        return ucl.responder.respondWithSuccess(message=frappe._("Document processed successfuly"), data=response)

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    
    
@frappe.whitelist(allow_guest=True)
def aadhaar_ocr(**kwargs):
    import requests
    try:
        ucl.validate_http_method("POST")
        user = ucl.__user()
        partner = ucl.__partner(user.name)

        data = ucl.validate(
            kwargs,
            {
                "document1": ["required"],
                "document2": "",
                "name": ""
        })
        ucl_setting = frappe.get_single("UCL Settings")
        url = "https://production.deepvue.tech/v1/documents/extraction/ind_aadhaar" 
        
        headers = {'Authorization': ucl_setting.bearer_token,'x-api-key': ucl_setting.deepvue_client_secret,}
        api_log_doc = ucl.log_api(method = "Aadhaar OCR", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers) + "\n" + str(data)))
        response = requests.request("POST", url, headers=headers, json=data)
        if response.json()['data']['id_number']:
            id_number = response.json()['data']['id_number']
            if partner.aadhaar_linked and id_number != partner.masked_aadhaar[-4:]:
                raise ucl.exceptions.UnauthorizedException(
                        _("Aadhaar Number does not match the Aadhaar linked with the provided PAN")
                    )

        ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Third Party", response = response.text) 
    
        return ucl.responder.respondWithSuccess(message=frappe._("Document processed successfuly"), data=response.json())

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    
@frappe.whitelist(allow_guest=True)
def face_match(**kwargs):
    import requests
    try:
        ucl.validate_http_method("POST")

        data = ucl.validate(
            kwargs,
            {
            "file_1": "required",
            "file_2": "required" 
        })
        api_log_doc = ucl.log_api(method = "Face Match", request_time = datetime.now(), request = str(data))
        url = "https://production.deepvue.tech/v1/facematch"
        headers = {
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJsaXZlX3N3aXRjaG15bG9hbiIsImV4cCI6MTcwNjA4NTE0MX0.nVE9IlSyxUtFaPoaZYMn-IX-0I5EKXlZDw4VhDwKtN0',
        'x-api-key': '66cb63695be3cb53f991cb907ab6c2d1fdd7d8d651fb834f48fe5a171ec41b2a',
        }
        file = {'file_a': open('/home/dell/ucl-bench/sites/ucl_local/public/files/My_pan.jpeg','rb'),'file_b': open('/home/dell/ucl-bench/sites/ucl_local/public/files/My_pan.jpeg','rb')}
        response = requests.post(url, headers=headers, files=file)
        ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Third Party", response = response.json())
 
        return ucl.responder.respondWithSuccess(message=frappe._("success"), data=response.json())

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    

@frappe.whitelist(allow_guest=True)
def rc_advance(**kwargs):
    import requests
    try:
        ucl.validate_http_method("POST")

        data = ucl.validate(
            kwargs,
            {
            "rc_number": ["required"]
        })
        ucl_setting = frappe.get_single("UCL Settings")
        url = "https://production.deepvue.tech/v1/verification/rc-advanced?rc_number=" + data.get("rc_number")
        payload = {}
        headers = {'Authorization': ucl_setting.bearer_token,'x-api-key': ucl_setting.deepvue_client_secret,}
        api_log_doc = ucl.log_api(method = "RC Advance", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers) + "\n" + str(data)))
        response = requests.request("GET",url, headers=headers, json = payload)
        ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Third Party", response = response.text)

        return ucl.responder.respondWithSuccess(message=frappe._("success"), data=response.json())
    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    

@frappe.whitelist(allow_guest=True)
def penny_drop(**kwargs):
    import requests
    import base64
    try:
        ucl.validate_http_method("POST")

        data = ucl.validate(
            kwargs,
            {
            "beneficiary_account_no" : ["required"],
            "beneficiary_ifsc": ["required"],
            "beneficiary_name": ""
        })
        url = "https://api.digio.in/client/verify/bank_account"
        ucl_setting = frappe.get_single("UCL Settings")

        credentials = f"{ucl_setting.digio_client_id}:{ucl_setting.digio_client_secret}"
        base64_credentials = base64.b64encode(credentials.encode()).decode()
        headers = {
        "Authorization": f"Basic {base64_credentials}",
        "Content-Type": "application/json"
        }
        api_log_doc = ucl.log_api(method = "Penny Drop", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers) + "\n" + str(data)))
        
        response = requests.request("POST",url, headers=headers, json = data)
        ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Third Party", response = response.text)

        return ucl.responder.respondWithSuccess(message=frappe._("success"), data=response.json())

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()