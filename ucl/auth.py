import frappe
import ucl
import re
from .exceptions import *

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

        # try:
        #     user = ucl.__user(data.get("mobile"))
        # except UserNotFoundException:
        #     user = None

        if not token:
            message = frappe._("Invalid OTP.")
            # if user:
            #     # frappe.local.login_manager.update_invalid_login(user.name)
            #     # try:
            #     #     frappe.local.login_manager.check_if_enabled(user.name)
            #     # except frappe.SecurityException as e:
            #     #     return utils.respondUnauthorized(message=str(e))
            #     LoginAttemptTracker(user_name=user.name).add_failure_attempt()
            #     if not user.enabled:
            #         # return utils.respondUnauthorized(message="User disabled or missing")
            #         raise lms.exceptions.UnauthorizedException(
            #             _("User disabled or missing")
            #         )

            #     invalid_login_attempts = get_login_attempt_tracker(user.name)
            #     if invalid_login_attempts.login_failed_count > 0:
            #         message += " {} invalid {}.".format(
            #             invalid_login_attempts.login_failed_count,
            #             "attempt"
            #             if invalid_login_attempts.login_failed_count == 1
            #             else "attempts",
            #         )

            # return utils.respondUnauthorized(message=message)
            raise ucl.exceptions.UnauthorizedException(message)

        if token:
            # frappe.db.begin()
            # if (not is_dummy_account) and (token.expiry <= frappe.utils.now_datetime()):
            if token.expiry <= frappe.utils.now_datetime():
                # return utils.respondUnauthorized(message=frappe._("OTP Expired."))
                raise ucl.exceptions.UnauthorizedException("OTP Expired")

            # if not user:
            #     # return utils.respondNotFound(message=frappe._("User not found."))
            #     raise lms.exceptions.NotFoundException(_("User not found"))

            # # try:
            # #     frappe.local.login_manager.check_if_enabled(user.name)
            # # except frappe.SecurityException as e:
            # #     return utils.respondUnauthorized(message=str(e))
            # if not user.enabled:
            #     # return utils.respondUnauthorized(message="User disabled or missing")
            #     raise lms.exceptions.UnauthorizedException("User disabled or missing")

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
