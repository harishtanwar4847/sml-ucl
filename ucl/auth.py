import frappe
import json
from frappe import _
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
        # validation
        ucl.validate_http_method("POST")
        
        data = ucl.validate(
            kwargs,
            {
                "mobile": ["required"],
                "email": ["required"],
                # "is_manual": ["required"],
                "first_name": ["required"],
                "last_name": ["required"],
            },
        )

        email_regex = (
            r"^([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})"
        )
        if re.search(email_regex, data.get("email")) is None or (
            len(data.get("email").split("@")) > 2
        ):
            # return utils.respondWithFailure(
            #     status=422,
            #     message=frappe._("Please enter valid email ID"),
            # )
            raise ucl.exceptions.FailureException(_("Please enter valid email ID."))
        
        ucl.create_user(first_name = data.get("first_name"),last_name = data.get("last_name"),email = data.get("email"),mobile = data.get("mobile"),)

        try:
            user = ucl.__user(data.get("mobile"))
        except UserNotFoundException:
            user = None

        token = dict(
                token=ucl.create_user_access_token(user.name)
            )
        
        ucl.create_user_token(
            entity=user.email,
            token=ucl.random_token(),
            token_type="Email Verification Token",
        )

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
def resend_verification_email(email):
    try:
        user_token = frappe.get_last_doc(
            "User Token",
            filters={"entity": email, "token_type": "Email Verification Token"},
        )
        if not user_token.used:
            doc = frappe.get_doc("User", email).as_dict()
            doc["url"] = frappe.utils.get_url(
                "/api/method/lms.auth.verify_user?token={}&user={}".format(
                    user_token.token, email
                )
            )
            frappe.enqueue_doc(
                "Notification",
                "User Email Verification",
                method="send",
                doc=doc,
            )
            frappe.msgprint(
                msg="Verification email resent Successfully",
                title="Email Verification",
                indicator="green",
            )
        else:
            ucl.create_user_token(
                entity=email,
                token=ucl.random_token(),
                token_type="Email Verification Token",
            )
            frappe.msgprint(
                msg="Verification email sent Successfully",
                title="Email Verification",
                indicator="green",
            )
    except Exception as e:
        ucl.log_api_error()
        frappe.log_error(
            frappe.get_traceback() + "\nResend Email Info:\n" + json.dumps(email),
            e.args,
        )
    


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
            # for firebase token "-_:" these characters are excluded from regex string
            reg = ucl.regex_special_characters(
                search=data.get("firebase_token"),
                regex=re.compile("[@!#$%^&*()<>?/\|}{~`]"),
            )
            if reg:
                # raise ucl.exceptions.FailureException(
                #     _("Special Characters not allowed.")
                # )
                return ucl.responder.respondWithFailure(
                    status=422,
                    message=frappe._("Special Characters not allowed."),
                )
                

        # try:
        #     is_dummy_account = lms.validate_spark_dummy_account(data.get("mobile"))
        #     if not is_dummy_account:
            token = ucl.verify_user_token(
                entity=data.get("mobile"), token=data.get("otp"), token_type="OTP"
            )
        #     else:
        #         token = lms.validate_spark_dummy_account_token(
        #             data.get("mobile"), data.get("otp")
        #         )
        # except InvalidUserTokenException:
        #     token = None

        try:
            user = ucl.__user(data.get("mobile"))
        except UserNotFoundException:
            user = None

        if not token:
            message = frappe._("Invalid OTP.")
            if user:
                # frappe.local.login_manager.update_invalid_login(user.name)
                # try:
                #     frappe.local.login_manager.check_if_enabled(user.name)
                # except frappe.SecurityException as e:
                #     return utils.respondUnauthorized(message=str(e))
                LoginAttemptTracker(user_name=user.name).add_failure_attempt()
                if not user.enabled:
                    # return utils.respondUnauthorized(message="User disabled or missing")
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

            # return utils.respondUnauthorized(message=message)
            raise ucl.exceptions.UnauthorizedException(message)

        if token:
            # frappe.db.begin()
            # if (not is_dummy_account) and (token.expiry <= frappe.utils.now_datetime()):
            if token.expiry <= frappe.utils.now_datetime():
                # return utils.respondUnauthorized(message=frappe._("OTP Expired."))
                raise ucl.exceptions.UnauthorizedException("OTP Expired")

            if not user:
                # return utils.respondNotFound(message=frappe._("User not found."))
                raise ucl.exceptions.NotFoundException(_("User not found"))

            # try:
            #     frappe.local.login_manager.check_if_enabled(user.name)
            # except frappe.SecurityException as e:
            #     return utils.respondUnauthorized(message=str(e))
            if not user.enabled:
                # return utils.respondUnauthorized(message="User disabled or missing")
                raise ucl.exceptions.UnauthorizedException("User disabled or missing")

            # customer = lms.__customer(user.name)
            # try:
            #     user_kyc = lms.__user_kyc(user.name)
            #     user_kyc.pan_no = lms.user_details_hashing(user_kyc.pan_no)
            #     for i in user_kyc.bank_account:
            #         i.account_number = lms.user_details_hashing(i.account_number)
            # except UserKYCNotFoundException:
            #     user_kyc = {}

            # res = {
            #     "token": utils.create_user_access_token(user.name),
            #     "customer": customer,
            #     "user_kyc": user_kyc,
            # }

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
            # lms.auth.login_activity(customer)
            frappe.db.commit()
            return ucl.responder.respondWithSuccess()

    except ucl.exceptions.APIException as e:
        frappe.db.rollback()
        ucl.log_api_error()
        return e.respond()
    except frappe.SecurityException as e:
        frappe.db.rollback()
        ucl.log_api_error()
        return ucl.respondUnauthorized(message=str(e))
        # raise lms.exceptions.UnauthorizedException(str(e))

@frappe.whitelist(allow_guest=True)
def set_pin(**kwargs):
    try:
        ucl.validate_http_method("POST")

        data = ucl.validate(
            kwargs,
            {
                "email": ["required"],
                # "authtoken": ["required"],
                "pin": ["required", "decimal", ucl.validator.rules.LengthRule(4)],
            },
        )
        # email validation
        # email_regex = r"^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,}$"
        email_regex = (
            r"^([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})"
        )
        if re.search(email_regex, data.get("email")) is None or (
            len(data.get("email").split("@")) > 2
        ):
            # return utils.respondWithFailure(
            #     status=422,
            #     message=frappe._("Please enter valid email ID"),
            # )
            raise ucl.exceptions.FailureException(_("Please enter valid email ID."))

        try:
            user = frappe.get_doc("User", data.get("email"))
        except frappe.DoesNotExistError:
            # raise utils.respondNotFound(
            #     message=frappe._("Please use registered email.")
            # )
            raise ucl.exceptions.NotFoundException(_("Please use registered email."))

        if not user.enabled:
            # return utils.respondUnauthorized(message="User disabled or missing")
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
                # update pin
                update_password(data.get("email"), data.get("pin"))
                frappe.db.commit()

                return ucl.responder.respondWithSuccess(
                    message=frappe._("User PIN has been updated.")
                )

            else:
                # return utils.respondWithFailure(
                #     status=417, message=frappe._("Please retype correct pin.")
                # )
                raise ucl.exceptions.RespondFailureException(
                    _("Please Type correct pin.")
                )

        elif not data.get("pin"):
            # return utils.respondWithFailure(
            #     status=417,
            #     message=frappe._("Please Enter value for new pin and retype pin."),
            # )
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
def request_forgot_pin_otp(**kwargs):
    try:
        ucl.validate_http_method("POST")

        data = ucl.validate(
            kwargs,
            {"email": ["required"]},
        )
        # email validation
        # email_regex = r"^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,}$"
        email_regex = (
            r"^([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})"
        )
        if re.search(email_regex, data.get("email")) is None or (
            len(data.get("email").split("@")) > 2
        ):
            # return utils.respondWithFailure(
            #     status=422,
            #     message=frappe._("Please enter valid email ID"),
            # )
            raise ucl.exceptions.FailureException(_("Please enter valid email ID."))

        try:
            user = frappe.get_doc("User", data.get("email"))
        except frappe.DoesNotExistError:
            # raise utils.respondNotFound(
            #     message=frappe._("Please use registered email.")
            # )
            raise ucl.exceptions.NotFoundException(_("Please use registered email."))

        if not user.enabled:
            # return utils.respondUnauthorized(message="User disabled or missing")
            raise ucl.exceptions.UnauthorizedException(_("User disabled or missing"))

        # is_dummy_account = lms.validate_spark_dummy_account(
        #     user.username, data.get("email"), check_valid=True
        # )
        # if not is_dummy_account:
        old_token_name = frappe.get_all(
            "User Token",
            filters={"entity": user.email, "token_type": "Forgot Pin OTP"},
            order_by="creation desc",
            fields=["*"],
        )
        if old_token_name:
            old_token = frappe.get_doc("User Token", old_token_name[0].name)
            ucl.token_mark_as_used(old_token)

        # frappe.db.begin()
        ucl.create_user_token(
            entity=user.email,
            token_type="Forgot Pin OTP",
            token=ucl.random_token(length=4, is_numeric=True),
        )
        frappe.db.commit()
        return ucl.responder.respondWithSuccess(message="Forgot Pin OTP sent")
    except ucl.exceptions.APIException as e:
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
        # email validation
        # email_regex = r"^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,}$"
        email_regex = (
            r"^([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})"
        )
        if re.search(email_regex, data.get("email")) is None or (
            len(data.get("email").split("@")) > 2
        ):
            # return utils.respondWithFailure(
            #     status=422,
            #     message=frappe._("Please enter valid email ID"),
            # )
            raise ucl.exceptions.FailureException(_("Please enter valid email ID."))

        try:
            user = frappe.get_doc("User", data.get("email"))
        except frappe.DoesNotExistError:
            # raise utils.respondNotFound(
            #     message=frappe._("Please use registered email.")
            # )
            raise ucl.exceptions.NotFoundException(_("Please use registered email."))

        if not user.enabled:
            # return utils.respondUnauthorized(message="User disabled or missing")
            raise ucl.exceptions.UnauthorizedException(_("User disabled or missing"))

        try:
            # is_dummy_account = ucl.validate_spark_dummy_account(
            #     user.username, data.get("email"), check_valid=True
            # )
            # if not is_dummy_account:
                token = ucl.verify_user_token(
                    entity=data.get("email"),
                    token=data.get("otp"),
                    token_type="Forgot Pin OTP",
                )
            # else:
            #     token = ucl.validate_spark_dummy_account_token(
            #         user.username, data.get("otp"), token_type="Forgot Pin OTP"
            #     )
        except InvalidUserTokenException:
            # raise utils.respondForbidden(message=frappe._("Invalid Forgot Pin OTP."))
            raise ucl.exceptions.ForbiddenException(_("Invalid Forgot Pin OTP"))

        # frappe.db.begin()

        if token:
            if token.expiry <= frappe.utils.now_datetime():
                # return utils.respondUnauthorized(message=frappe._("OTP Expired."))
                raise ucl.exceptions.UnauthorizedException(_("OTP Expired"))

        if data.get("otp") and data.get("new_pin") and data.get("retype_pin"):
            if data.get("retype_pin") == data.get("new_pin"):
                # update pin
                update_password(data.get("email"), data.get("retype_pin"))
                frappe.db.commit()

                return ucl.responder.respondWithSuccess(
                    message=frappe._("User PIN has been updated.")
                )

            else:
                # return utils.respondWithFailure(
                #     status=417, message=frappe._("Please retype correct pin.")
                # )
                raise ucl.exceptions.RespondFailureException(
                    _("Please retype correct pin.")
                )

        elif not data.get("retype_pin") or not data.get("new_pin"):
            # return utils.respondWithFailure(
            #     status=417,
            #     message=frappe._("Please Enter value for new pin and retype pin."),
            # )
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
        if data.get("firebase_token"):
            # for firebase token "-_:" these characters are excluded from regex string
            reg = ucl.regex_special_characters(
                search=data.get("firebase_token"),
                regex=re.compile("[@!#$%^&*()<>?/\|}{~`]"),
            )
            if reg:
                # return utils.respondWithFailure(
                #     status=422,
                #     message=frappe._("Special Characters not allowed."),
                # )
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
                print(user)
                frappe.local.login_manager.authenticate(
                    user=user.name, pwd=data.get("pin")
                )
            except frappe.SecurityException as e:
                # raise utils.respondUnauthorized(message=str(e))
                raise ucl.exceptions.UnauthorizedException(str(e))
            except frappe.AuthenticationError as e:
                message = frappe._("Incorrect PIN.")
                invalid_login_attempts = get_login_attempt_tracker(user.name)
                if invalid_login_attempts.login_failed_count > 0:
                    message += " {} invalid {}.".format(
                        invalid_login_attempts.login_failed_count,
                        "attempt"
                        if invalid_login_attempts.login_failed_count == 1
                        else "attempts",
                    )
                # return utils.respondUnauthorized(message=message)
                raise ucl.exceptions.UnauthorizedException(message)

            # customer = lms.__customer(user.name)
            # try:
            #     user_kyc = lms.__user_kyc(user.name)
            # except UserKYCNotFoundException:
            #     user_kyc = {}

            # if user_kyc:
            #     user_kyc = lms.user_kyc_hashing(user_kyc)

            token = dict(
                token=ucl.create_user_access_token(user.name)
            )
            app_version_platform = ""
            if data.get("app_version") and data.get("platform"):
                app_version_platform = (
                    data.get("app_version") + " | " + data.get("platform")
                )
            # lms.add_firebase_token(
            #     data.get("firebase_token"), app_version_platform, user.name
            # )
            # ucl.auth.login_activity(customer)
            return ucl.responder.respondWithSuccess(
                message=frappe._("Logged in Successfully"), data=token
            )
        else:
            if not data.get("accept_terms"):
                # return utils.respondUnauthorized(
                #     message=frappe._("Please accept Terms of Use and Privacy Policy.")
                # )
                raise ucl.exceptions.UnauthorizedException(
                    _("Please accept Terms of Use and Privacy Policy.")
                )

            # save user login consent
        #     login_consent_doc = frappe.get_doc(
        #         {
        #             "doctype": "User Consent",
        #             "mobile": data.get("mobile"),
        #             "consent": "Login",
        #         }
        #     )
        #     login_consent_doc.insert(ignore_permissions=True)

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
        # raise lms.exceptions.UnauthorizedException(str(e))
    

@frappe.whitelist(allow_guest=True)
def get_user_details(**kwargs):
    try:
        ucl.validate_http_method("POST")

        data = ucl.validate(
            kwargs,
            {
                "authtoken": ["required"],
            },
        )

        res = re.findall(r'\w+', data.get("authtoken"))
        print(res[1])
        print(res[2])
        # if frappe.db.exists("User", "harish.tanwar@atriina.com"):
        try:
            if frappe.db.exists("User", {"api_key": res[1]}):
                print("user exist")
                user = frappe.get_doc('User',{'api_key': res[1]})
                print(user)
                if frappe.db.exists("Partner", {"user_id": user.name}):
                    partner = frappe.get_doc('Partner',{'user_id': user.name})
                    print(partner)
                    return ucl.responder.respondWithSuccess(
                    message=frappe._("Partner details"), data = "data"
                )
                else:
                    return ucl.responder.respondWithFailure(
                        message=frappe._("Partner Not Found for existing user")
                    )
            else:
                return ucl.responder.respondWithFailure(
                    message=frappe._("User Not Found")
                )
        except UserNotFoundException:
            user = None
            raise ucl.exceptions.UserNotFoundException()
        # if data.get("firebase_token"):
        #     # for firebase token "-_:" these characters are excluded from regex string
        #     reg = ucl.regex_special_characters(
        #         search=data.get("firebase_token"),
        #         regex=re.compile("[@!#$%^&*()<>?/\|}{~`]"),
        #     )
        #     if reg:
        #         # return utils.respondWithFailure(
        #         #     status=422,
        #         #     message=frappe._("Special Characters not allowed."),
        #         # )
        #         raise ucl.exceptions.FailureException(
        #             _("Special Characters not allowed.")
        #         )

        # try:except UserNotFoundException:
            # user = None
        #     user = ucl.__user(data.get("mobile"))
        # except UserNotFoundException:
        #     user = None

        # # frappe.db.begin()
        # if data.get("pin"):
        #     try:
        #         frappe.local.login_manager.authenticate(
        #             user=user.name, pwd=data.get("pin")
        #         )
        #     except frappe.SecurityException as e:
        #         # raise utils.respondUnauthorized(message=str(e))
        #         raise ucl.exceptions.UnauthorizedException(str(e))
        #     except frappe.AuthenticationError as e:
        #         message = frappe._("Incorrect PIN.")
        #         invalid_login_attempts = get_login_attempt_tracker(user.name)
        #         if invalid_login_attempts.login_failed_count > 0:
        #             message += " {} invalid {}.".format(
        #                 invalid_login_attempts.login_failed_count,
        #                 "attempt"
        #                 if invalid_login_attempts.login_failed_count == 1
        #                 else "attempts",
        #             )
        #         # return utils.respondUnauthorized(message=message)
        #         raise ucl.exceptions.UnauthorizedException(message)

        #     # customer = lms.__customer(user.name)
        #     # try:
        #     #     user_kyc = lms.__user_kyc(user.name)
        #     # except UserKYCNotFoundException:
        #     #     user_kyc = {}

        #     # if user_kyc:
        #     #     user_kyc = lms.user_kyc_hashing(user_kyc)

        #     token = dict(
        #         token=ucl.create_user_access_token(user.name)
        #     )
        #     app_version_platform = ""
        #     if data.get("app_version") and data.get("platform"):
        #         app_version_platform = (
        #             data.get("app_version") + " | " + data.get("platform")
        #         )
        #     # lms.add_firebase_token(
        #     #     data.get("firebase_token"), app_version_platform, user.name
        #     # )
        #     # ucl.auth.login_activity(customer)
        #     return ucl.responder.respondWithSuccess(
        #         message=frappe._("Logged in Successfully"), data=token
        #     )
        # else:
        #     if not data.get("accept_terms"):
        #         # return utils.respondUnauthorized(
        #         #     message=frappe._("Please accept Terms of Use and Privacy Policy.")
        #         # )
        #         raise ucl.exceptions.UnauthorizedException(
        #             _("Please accept Terms of Use and Privacy Policy.")
        #         )

        #     # save user login consent
        # #     login_consent_doc = frappe.get_doc(
        # #         {
        # #             "doctype": "User Consent",
        # #             "mobile": data.get("mobile"),
        # #             "consent": "Login",
        # #         }
        # #     )
        # #     login_consent_doc.insert(ignore_permissions=True)

        # # # check if dummy account
        # # is_dummy_account = lms.validate_spark_dummy_account(data.get("mobile"))

        # # if not is_dummy_account:
        # #     lms.create_user_token(
        # #         entity=data.get("mobile"),
        # #         token=lms.random_token(length=4, is_numeric=True),
        # #     )

        # # frappe.db.commit()
        # # return utils.respondWithSuccess(message=frappe._("OTP Sent"))
    except ucl.exceptions.APIException as e:
        frappe.db.rollback()
        ucl.log_api_error()
        return e.respond()
    except frappe.SecurityException as e:
        frappe.db.rollback()
        ucl.log_api_error()
        return ucl.responder.respondUnauthorized(message=str(e))
        # raise lms.exceptions.UnauthorizedException(str(e))
    

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
            print(usr.full_name)
            print(usr.mobile_no)
            print(usr.name)
            ucl.create_partner(first_name = usr.full_name, mobile = usr.mobile_no, email = usr.name, user = usr.name)
            # partner = ucl.get_partner(user)
            # partner.is_email_verified = 1
            # partner.save(ignore_permissions=True)
            frappe.db.commit()

        elif token_document[0].used == 1:
            url = frappe.utils.get_url("/everify?already-verified")

    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = url

    # webbrowser.open(url, new=1)
    # if len(token_document) == 0:
    #     return frappe.respond_as_web_page(
    #         frappe._("Something went wrong"),
    #         frappe._("Your token is invalid."),
    #         indicator_color="red",
    #     )

    # if (
    #     len(token_document) > 0
    #     and token_document[0].expiry < frappe.utils.now_datetime()
    # ):
    #     return frappe.respond_as_web_page(
    #         frappe._("Something went wrong"),
    #         frappe._("Verification link has been Expired!"),
    #         indicator_color="red",
    #     )

    # frappe.db.set_value("User Token", token_document[0].name, "used", 1)
    # customer = lms.get_customer(user)
    # customer.is_email_verified = 1
    # customer.save(ignore_permissions=True)
    # frappe.db.commit()

    """changes as per latest email notification list-sent by vinayak - email verification final 2.0"""
    # doc = frappe.get_doc("User", user)

    # frappe.enqueue_doc("Notification", "User Welcome Email", method="send", doc=doc)

    # mess = frappe._(
    #     "Dear"
    #     + " "
    #     + customer.first_name
    #     + ",\nYour registration at Spark.Loans was successfull!\nWelcome aboard."
    # )
    # mess = frappe._("Welcome aboard. Your registration at Spark.Loans was successfull!")
    # frappe.enqueue(method=send_sms, receiver_list=[doc.phone], msg=mess)

    # frappe.respond_as_web_page(
    #     frappe._("Success"),
    #     frappe._("Your email has been successfully verified."),
    #     indicator_color="green",
    # )

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