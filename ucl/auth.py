import frappe
import json
from frappe import _
from datetime import datetime, timedelta
import ucl
import re
from .exceptions import *
from frappe.auth import LoginAttemptTracker, get_login_attempt_tracker
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
                "resend": ["required"],
                "is_manual": ["required"],
                "first_name": ["required"],
                "last_name": ["required"],
            },
        )
        api_log_doc = ucl.log_api(method = "Verify Email", request_time = datetime.now(), request = str(data))

        email_regex = (
            r"^([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})"
        )
        if re.search(email_regex, data.get("email")) is None or (
            len(data.get("email").split("@")) > 2
        ):
            raise ucl.exceptions.FailureException(_("Please enter valid email ID."))
        
        if data.get("resend") == 1:
            try:
                user = ucl.__user(data.get("mobile"))
            except UserNotFoundException:
                user = None

            if user:
                ucl.delete_user(user)
        
        ucl.create_user(first_name = data.get("first_name"),last_name = data.get("last_name"),email = data.get("email"),mobile = data.get("mobile"),)

        try:
            user = ucl.__user(data.get("mobile"))
        except UserNotFoundException:
            user = None

        token = dict(
                token=ucl.create_user_access_token(user.name)
            )
        if data.get("is_manual") == 1:
            ucl.create_user_token(
                entity=user.email,
                token=ucl.random_token(),
                token_type="Email Verification Token",
            )
        if data.get("is_manual") == 0:
            ucl.create_partner(first_name = user.full_name, mobile = user.mobile_no, email = user.name, user = user.name)
            
        api_log_doc.response_time = datetime.now()
        api_log_doc.response = "User Created Successfully"
        api_log_doc.save(ignore_permissions=True)

        return ucl.responder.respondWithSuccess(
                message=frappe._("User Created Successfully"), data=token
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
        #     else:
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
        api_log_doc.response_time = datetime.now()

        if not token:
            message = frappe._("Invalid OTP.")
            api_log_doc.response = "Invalid OTP"
            api_log_doc.save(ignore_permissions=True)
            frappe.db.commit()

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
                    )
            raise ucl.exceptions.UnauthorizedException(message)

        if token:
            # frappe.db.begin()
            # if (not is_dummy_account) and (token.expiry <= frappe.utils.now_datetime()):
            if token.expiry <= frappe.utils.now_datetime():
                api_log_doc.response = "OTP Expired"
                api_log_doc.save(ignore_permissions=True)
                frappe.db.commit()

                raise ucl.exceptions.UnauthorizedException("OTP Expired")
            
            
            if user:
                user_data = {
                        "first_name":user.first_name,
                        "last_name":user.last_name,
                        "email":user.name,
                        "role":frappe.get_roles(user.name)
                    }
                if "Partner" in frappe.get_roles(user.name) or "Partner Associate" in frappe.get_roles(user.name):
                    partner = frappe.get_all("Partner", filters={'user_id': user.name}, fields = ["*"])
                    user_data['partner'] = partner
            
            else:
                user_data = "User not found"

            # if not is_dummy_account:
            #     token.used = 1
            #     token.save(ignore_permissions=True)

            app_version_platform = ""
            if data.get("app_version") and data.get("platform"):
                app_version_platform = (
                    data.get("app_version") + " | " + data.get("platform")
                )
            # lms.add_firebase_token(
            #     data.get("firebase_token"), app_version_platform, user.name
            # )
            ucl.token_mark_as_used(token)
            api_log_doc.response = "OTP Verified" + "\n" + str(data)
            api_log_doc.save(ignore_permissions=True)
            frappe.db.commit()
            return ucl.responder.respondWithSuccess(message=frappe._("OTP Verified"), data = user_data)

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
                "email": ["required"],
                "authtoken": ["required"],
                "pin": ["required", "decimal", ucl.validator.rules.LengthRule(4)],
            },
        )

        api_log_doc = ucl.log_api(method = "Set Pin", request_time = datetime.now(), request = str(data))
        api_log_doc.response_time = datetime.now()
        frappe.db.commit()
        email_regex = (
            r"^([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})"
        )
        if re.search(email_regex, data.get("email")) is None or (
            len(data.get("email").split("@")) > 2
        ):  
            api_log_doc.response = "Please enter valid email ID."
            api_log_doc.save(ignore_permissions=True)
            frappe.db.commit()
            raise ucl.exceptions.FailureException(_("Please enter valid email ID."))

        try:
            user = frappe.get_doc("User", data.get("email"))
        except frappe.DoesNotExistError:
            raise ucl.exceptions.UserNotFoundException()

        if not user.enabled:
            api_log_doc.response = "User disabled or missing"
            api_log_doc.save(ignore_permissions=True)
            frappe.db.commit()
            raise ucl.exceptions.UnauthorizedException(_("User disabled or missing"))

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
                update_password(data.get("email"), data.get("pin"))
                partner = frappe.get_doc('Partner', {"user_id":user.name})
                if partner:
                    partner.is_pin_set = 1
                    partner.save(ignore_permissions=True)
                api_log_doc.response = "User PIN has been updated."
                api_log_doc.save(ignore_permissions=True)
                frappe.db.commit()

                return ucl.responder.respondWithSuccess(
                    message=frappe._("User PIN has been updated.")
                )

        else:
            api_log_doc.response = "Please Enter value for pin."
            api_log_doc.save(ignore_permissions=True)
            frappe.db.commit()
            raise ucl.exceptions.RespondFailureException(
                _("Please Enter value for pin.")
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
                "email": ["required"],
                "otp": ["required", "decimal", ucl.validator.rules.LengthRule(4)],
                "new_pin": ["required", "decimal", ucl.validator.rules.LengthRule(4)],
                "retype_pin": [
                    "required",
                    "decimal",
                    ucl.validator.rules.LengthRule(4),
                ],
            },
        )
        api_log_doc = ucl.log_api(method = "Verify Forgot Pin OTP", request_time = datetime.now(), request = str(data))
        api_log_doc.response_time = datetime.now()
        email_regex = (
            r"^([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})"
        )
        if re.search(email_regex, data.get("email")) is None or (
            len(data.get("email").split("@")) > 2
        ):
            api_log_doc.response = "Please enter valid email ID."
            api_log_doc.save(ignore_permissions=True)
            frappe.db.commit()
            raise ucl.exceptions.FailureException(_("Please enter valid email ID."))

        try:
            user = frappe.get_doc("User", data.get("email"))
        except frappe.DoesNotExistError:
            raise ucl.exceptions.UserNotFoundException()

        if not user.enabled:
            api_log_doc.response = "User disabled or missing"
            api_log_doc.save(ignore_permissions=True)
            frappe.db.commit()
            raise ucl.exceptions.UnauthorizedException(_("User disabled or missing"))

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
            api_log_doc.response = "Invalid Forgot Pin OTP"
            api_log_doc.save(ignore_permissions=True)
            frappe.db.commit()
            raise ucl.exceptions.ForbiddenException(_("Invalid Forgot Pin OTP"))

        # frappe.db.begin()

        if token:
            if token.expiry <= frappe.utils.now_datetime():
                api_log_doc.response = "OTP Expired"
                api_log_doc.save(ignore_permissions=True)
                frappe.db.commit()
                raise ucl.exceptions.UnauthorizedException(_("OTP Expired"))

        if data.get("otp") and data.get("new_pin") and data.get("retype_pin"):
            if data.get("retype_pin") == data.get("new_pin"):
                update_password(data.get("email"), data.get("retype_pin"))
                api_log_doc.response = "User PIN has been updated."
                api_log_doc.save(ignore_permissions=True)
                frappe.db.commit()

                return ucl.responder.respondWithSuccess(
                    message=frappe._("User PIN has been updated.")
                )

            else:
                api_log_doc.response = "Please retype correct pin."
                api_log_doc.save(ignore_permissions=True)
                frappe.db.commit()
                raise ucl.exceptions.RespondFailureException(
                    _("Please retype correct pin.")
                )

        elif not data.get("retype_pin") or not data.get("new_pin"):
            api_log_doc.response = "Please Enter value for new pind and retype pin."
            api_log_doc.save(ignore_permissions=True)
            frappe.db.commit()
            raise ucl.exceptions.RespondFailureException(
                _("Please Enter value for new pind and retype pin.")
            )

        # if not is_dummy_account:
        ucl.token_mark_as_used(token)

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
                "mobile": ["required", "decimal", ucl.validator.rules.LengthRule(10)],
                "pin": [ucl.validator.rules.LengthRule(4)],
                "firebase_token": [ucl.validator.rules.RequiredIfPresent("pin")],
                # "accept_terms": "decimal|between:0,1",
                "platform": "",
                "app_version": "",
            },
        )

        api_log_doc = ucl.log_api(method = "Login", request_time = datetime.now(), request = str(data))
        api_log_doc.response_time = datetime.now()
        if data.get("firebase_token"):
            reg = ucl.regex_special_characters(
                search=data.get("firebase_token"),
                regex=re.compile("[@!#$%^&*()<>?/\|}{~`]"),
            )
            if reg:
                api_log_doc.response = "Special Characters not allowed."
                api_log_doc.save(ignore_permissions=True)
                frappe.db.commit()
                raise ucl.exceptions.FailureException(
                    _("Special Characters not allowed.")
                )

        try:
            user = ucl.__user(data.get("mobile"))
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
                api_log_doc.response = "Incorrect PIN."
                api_log_doc.save(ignore_permissions=True)
                frappe.db.commit()
                raise ucl.exceptions.UnauthorizedException(str(e))
            except frappe.AuthenticationError as e:
                message = frappe._("Incorrect PIN.")
                api_log_doc.response = "Incorrect PIN."
                api_log_doc.save(ignore_permissions=True)
                frappe.db.commit()
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
            api_log_doc.response = "Logged in Successfully"
            api_log_doc.save(ignore_permissions=True)
            frappe.db.commit()
            return ucl.responder.respondWithSuccess(
                message=frappe._("Logged in Successfully"), data=token
            )
        else:
            if not data.get("accept_terms"):
                api_log_doc.response = "Please accept Terms of Use and Privacy Policy."
                api_log_doc.save(ignore_permissions=True)
                frappe.db.commit()
                raise ucl.exceptions.UnauthorizedException(
                    _("Please accept Terms of Use and Privacy Policy.")
                )

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
        ucl.validate_http_method("GET")

        data = ucl.validate(
            kwargs,
            {
                "authtoken": ["required"],
            },
        )
        api_log_doc = ucl.log_api(method = "User details", request_time = datetime.now(), request = str(data))
        api_log_doc.response_time = datetime.now()

        res = re.findall(r'\w+', data.get("authtoken"))
        try:
            if frappe.db.exists("User", {"api_key": res[1]}):
                user = frappe.get_doc('User',{'api_key': res[1]})
                if res[2] == user.get_password('api_secret'):
                    print(user)
                    if frappe.db.exists("Partner", {"user_id": user.name}):
                        partner = frappe.get_all("Partner", filters={'user_id': user.name}, fields = ["*"])
                        api_log_doc.response = "Partner details" + "\n" + str(partner)
                        api_log_doc.save(ignore_permissions=True)
                        frappe.db.commit()
                        return ucl.responder.respondWithSuccess(
                        message=frappe._("Partner details"), data = partner
                    )
                    else:
                        api_log_doc.response = "Partner Not Found for existing user"
                        api_log_doc.save(ignore_permissions=True)
                        frappe.db.commit()
                        return ucl.responder.respondWithFailure(
                            message=frappe._("Partner Not Found for existing user")
                        )
                else:
                    api_log_doc.response = "User Not Found"
                    api_log_doc.save(ignore_permissions=True)
                    frappe.db.commit()
                    return ucl.responder.respondWithFailure(
                        message=frappe._("User Not Found")
                    )
            else:
                api_log_doc.response = "User Not Found"
                api_log_doc.save(ignore_permissions=True)
                frappe.db.commit()
                return ucl.responder.respondWithFailure(
                    message=frappe._("User Not Found")
                )
        except UserNotFoundException:
            user = None
            raise ucl.exceptions.UserNotFoundException()
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
def pan_plus(**kwargs):
    import requests
    try:
        ucl.validate_http_method("POST")

        data = ucl.validate(
            kwargs,
            {
            "pan_number": ["required"]
        })
        api_log_doc = ucl.log_api(method = "Pan Plus", request_time = datetime.now(), request = str(data))

        url = "https://production.deepvue.tech/v1/verification/panadvanced?pan_number={}".format(data.get("pan_number"))
    
        payload={}
        headers = {
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJsaXZlX3N3aXRjaG15bG9hbiIsImV4cCI6MTcwNjE3ODI1MH0.u8Bu3BbsbW4k7EZ-shd8FV0lhTsikbd9TT0KWByDmMo',
        'x-api-key': '66cb63695be3cb53f991cb907ab6c2d1fdd7d8d651fb834f48fe5a171ec41b2a',
        }
        response = requests.request("GET", url, headers=headers, data=payload)
        api_log_doc.response_time = datetime.now()
        api_log_doc.response = response.text
        api_log_doc.save(ignore_permissions=True)    
        return ucl.responder.respondWithSuccess(message=frappe._("Pan Verified Successfully."), data=response.text)

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()

    
@frappe.whitelist(allow_guest=True)
def pan_ocr(**kwargs):
    import requests
    try:
        ucl.validate_http_method("POST")

        data = ucl.validate(
            kwargs,
            {
            "pan_url": ["required"]
        })
        api_log_doc = ucl.log_api(method = "Pan OCR", request_time = datetime.now(), request = str(data))
        url = "https://production.deepvue.tech/v1/documents/extraction/ind_pancard" 
        payload={
            "document1": data.get("pan_url"),
            "document2": "string",
            "name": "string"
        }
        headers = {
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJsaXZlX3N3aXRjaG15bG9hbiIsImV4cCI6MTcwNjE3ODI1MH0.u8Bu3BbsbW4k7EZ-shd8FV0lhTsikbd9TT0KWByDmMo',
        'x-api-key': '66cb63695be3cb53f991cb907ab6c2d1fdd7d8d651fb834f48fe5a171ec41b2a',
        }
        response = requests.request("POST", url, headers=headers, json=payload)
        api_log_doc.response_time = datetime.now()
        api_log_doc.response = response.text
        api_log_doc.save(ignore_permissions=True)
    
        return ucl.responder.respondWithSuccess(message=frappe._("Document processed successfuly"), data=response.text)

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    

@frappe.whitelist(allow_guest=True)
def save_pan_details(**kwargs):
    try:
        api_log_doc = ucl.log_api(method = "Save Pan Details", request_time = datetime.now(), request = str(data))
        
        api_log_doc.response_time = datetime.now()
        api_log_doc.response = "Pan details saved successfully"
        api_log_doc.save(ignore_permissions=True)  
    
        return ucl.responder.respondWithSuccess(message=frappe._("Pan details saved successfully"))

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    
@frappe.whitelist(allow_guest=True)
def aadhaar_ocr(**kwargs):
    import requests
    try:
        ucl.validate_http_method("POST")

        data = ucl.validate(
            kwargs,
            {
            "aadhaar_url": ["required"]
        })
        api_log_doc = ucl.log_api(method = "Aadhaar OCR", request_time = datetime.now(), request = str(data))
        url = "https://production.deepvue.tech/v1/documents/extraction/ind_aadhaar" 
        payload={
            "document1": data.get("aadhaar_url"),
            "document2": "string",
            "name": "string"
        }
        headers = {
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJsaXZlX3N3aXRjaG15bG9hbiIsImV4cCI6MTcwNjA4NTE0MX0.nVE9IlSyxUtFaPoaZYMn-IX-0I5EKXlZDw4VhDwKtN0',
        'x-api-key': '66cb63695be3cb53f991cb907ab6c2d1fdd7d8d651fb834f48fe5a171ec41b2a',
        }
        response = requests.request("POST", url, headers=headers, json=payload)
        api_log_doc.response_time = datetime.now()
        api_log_doc.response = response.text
        api_log_doc.save(ignore_permissions=True)  
    
        return ucl.responder.respondWithSuccess(message=frappe._("Document processed successfuly"), data=response.text)

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
        api_log_doc.response_time = datetime.now()
        api_log_doc.response = response.json()
        api_log_doc.save(ignore_permissions=True)  
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
            "rc_number": "required"
        })
        api_log_doc = ucl.log_api(method = "RC Advance", request_time = datetime.now(), request = str(data))
        url = "https://production.deepvue.tech/v1/verification/rc-advanced?rc_number={}".format(data.get("rc_number"))
        payload = {}
        headers = {
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJsaXZlX3N3aXRjaG15bG9hbiIsImV4cCI6MTcwNjA4NTE0MX0.nVE9IlSyxUtFaPoaZYMn-IX-0I5EKXlZDw4VhDwKtN0',
        'x-api-key': '66cb63695be3cb53f991cb907ab6c2d1fdd7d8d651fb834f48fe5a171ec41b2a',
        }
        response = requests.request("GET",url, headers=headers, json = payload)
        api_log_doc.response_time = datetime.now()
        api_log_doc.response = response.text
        api_log_doc.save(ignore_permissions=True)
        return ucl.responder.respondWithSuccess(message=frappe._("success"), data=response.text)

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
            "beneficiary_account_no" : "required",
            "beneficiary_ifsc": "required",
            "beneficiary_name": ""
        })
        api_log_doc = ucl.log_api(method = "Penny Drop", request_time = datetime.now(), request = str(data))
        url = "https://api.digio.in/client/verify/bank_account"
        payload = {
            "beneficiary_account_no" : data.get("beneficiary_account_no"),
            "beneficiary_ifsc": data.get("beneficiary_ifsc"),
            "beneficiary_name": data.get("beneficiary_name")
            }
        
        username = "AIXIC9J5YKIYDGBTN9LG19TGBRGUYJ38"
        password = "DU8RQISBGDLJ5IQXKJZSWTXERBHWZWUO"
        credentials = f"{username}:{password}"
        base64_credentials = base64.b64encode(credentials.encode()).decode()
        headers = {
        "Authorization": f"Basic {base64_credentials}",
        "Content-Type": "application/json"
        }
        response = requests.request("POST",url, headers=headers, json = payload)
        api_log_doc.response_time = datetime.now()
        api_log_doc.response = response.text
        api_log_doc.save(ignore_permissions=True)
        return ucl.responder.respondWithSuccess(message=frappe._("success"), data=response.text)

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    

@frappe.whitelist(allow_guest=True)
def partner_type():
    try:
        ucl.validate_http_method("POST")

        data = {
            "partner_id": ["required"],
            "partner_type": ["required"]
        }
        api_log_doc = ucl.log_api(method = "Pan Plus", request_time = datetime.now(), request = str(data))
        doc = frappe.get_doc({
        'doctype': 'Partner',
        'partner_id': data.get("partner_id")
        })
        doc.partner_type = data.get("partner_type")
        doc.save(ignore_permissions=True)
        return ucl.responder.respondWithSuccess(message=frappe._("success"), data=data)

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
