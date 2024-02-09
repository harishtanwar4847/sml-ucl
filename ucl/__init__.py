import base64
import json
import os
import frappe
from frappe import _
from pdf2image import convert_from_path
import ucl
import random
import re
import string
import ucl.exceptions as exceptions
from datetime import datetime, timedelta
from frappe import _
from traceback import format_exc
from .exceptions import *
import requests
import base64
from random import randint


__version__ = "0.0.1"


user_token_expiry_map = {
    "Login OTP": 10,
    "Forgot Pin OTP": 10,
}

class ValidationError(Exception):
    http_status_code = 422


class ServerError(Exception):
    http_status_code = 500


class FirebaseError(Exception):
    pass


class FirebaseCredentialsFileNotFoundError(FirebaseError):
    pass


class InvalidFirebaseCredentialsError(FirebaseError):
    pass


class FirebaseTokensNotProvidedError(FirebaseError):
    pass


class FirebaseDataNotProvidedError(FirebaseError):
    pass

from ucl.validator.rules import *
from validator import validate as validate_


def validate(data, rules):
	valid, valid_data, errors = validate_(data, rules, return_info=True)

	if not valid:
		from ucl.exceptions import ValidationException
		raise ValidationException(errors=errors)

	return valid_data

def validate_http_method(*methods):
	if frappe.request:
		if frappe.request.method.upper() not in [method.upper() for method in methods]:
			from ucl.exceptions import MethodNotAllowedException
			raise MethodNotAllowedException

@frappe.whitelist(allow_guest=True)
def send_otp(**kwargs):
    try:
        ucl.validate_http_method("POST")

        data = ucl.validate(
            kwargs,
            {
                "mobile": ["required", "decimal", ucl.validator.rules.LengthRule(10)],
                "token_type": "required",
            },
        )
        if frappe.db.exists("User Token", {"entity" : data.get("mobile"), "token_type": data.get("token_type"), "used": 0}):
            user_token = frappe.get_last_doc("User Token", filters={"entity" : data.get("mobile"), "token_type": data.get("token_type"), "used": 0})
            token_mark_as_used(user_token)
        api_log_doc = log_api(method = "Send OTP", request_time = datetime.now(), request = str(data))
        create_user_token(entity=data.get("mobile"), token=random_token(length=4, is_numeric=True), token_type = data.get("token_type"))
        login_consent_doc = frappe.get_doc(
                {
                    "doctype": "User Consent",
                    "mobile": data.get("mobile"),
                    "consent": "Login",
                }
            ).insert(ignore_permissions=True)
        log_api_response(api_log_doc = api_log_doc, api_type = "Internal", response = "OTP Sent")
        # api_log_doc.response_time = datetime.now()
        # api_log_doc.api_type = "Internal"
        # api_log_doc.response = "OTP Sent"
        # api_log_doc.save(ignore_permissions=True)
        # frappe.db.commit()
        return ucl.responder.respondWithSuccess(
                message=frappe._("OTP Sent"),
            )
    except Exception as e:
        log_api_error()
        generateResponse(is_success=False, error=e)
        raise


def create_user_access_token(user_name):
	user_details = frappe.get_doc('User', user_name)
	api_secret = frappe.generate_hash(length=15)
	# if api key is not set generate api key
	if not user_details.api_key:
		api_key = frappe.generate_hash(length=15)
		user_details.api_key = api_key
	user_details.api_secret = api_secret
	user_details.save(ignore_permissions=True)

	return 'token {}:{}'.format(user_details.api_key, api_secret)


def create_user(first_name, last_name, mobile, email):
    try:
        user = frappe.get_doc(
            {
                "doctype": "User",
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "username": mobile,
                "phone": mobile,
                "mobile_no": mobile,
                "send_welcome_email": 0,
                # "new_password": frappe.mock("password"),
                "roles": [
                    {"doctype": "Has Role", "role": "Partner"}
                ]
                # if tester
                # else [{"doctype": "Has Role", "role": "Loan Customer"}],
            }
        ).insert(ignore_permissions=True)

        return user
    except Exception as e:
        raise exceptions.APIException(message=str(e))
    

# def delete_user(user):
#     if not frappe.db.exists("Partner", {"user_id": user.name}):
#         frappe.db.sql("delete from `tabUser` where name = %s", user.name)
#         frappe.db.commit()
#     else:
#         ucl.responder.respondWithFailure(
#             message=frappe._("Partner already present with this Mobile No. Please use a different Mobile No"),
#         )

    
def create_partner(first_name, mobile, email, user):
    try:
        partner = frappe.get_doc(
            {
                "doctype": "Partner",
                "email_id": email,
                "user_id": user,
                "partner_name": first_name,
                "mobile_number": mobile
            }
        ).insert(ignore_permissions=True)
        frappe.db.commit()
        return partner
    except Exception as e:
        raise exceptions.APIException(message=str(e))


def __user(input=None):
    # get session user if input is not provided
    if not input:
        res = frappe.get_all("User", or_filters={"email": frappe.session.user})
        # input = frappe.session.user
    else:
        res = frappe.get_all("User", or_filters={"mobile_no": input})

    if len((res)) == 0:
        raise exceptions.UserNotFoundException

    return frappe.get_doc("User", res[0].name)


def random_token(length=10, is_numeric=False):
    if is_numeric:
        sample_str = "".join((random.choice(string.digits) for i in range(length)))
    else:
        letters_count = random.randrange(length)
        digits_count = length - letters_count
        sample_str = "".join(
            (random.choice(string.ascii_letters) for i in range(letters_count))
        )
        sample_str += "".join(
            (random.choice(string.digits) for i in range(digits_count))
        )
    # Convert string to list and shuffle it to mix letters and digits
    sample_list = list(sample_str)
    random.shuffle(sample_list)
    final_string = "".join(sample_list)
    return final_string


def verify_user_token(entity, token, token_type):
    filters = {"entity": entity, "token": token, "token_type": token_type, "used": 0}

    token_name = frappe.db.get_value("User Token", filters, "name")

    if not token_name:
        raise InvalidUserTokenException("Invalid {}".format(token_type))

    return frappe.get_doc("User Token", token_name)


def token_mark_as_used(token):
    if token.used == 0:
        token.used = 1
        token.save(ignore_permissions=True)
        frappe.db.commit()

def create_user_token(entity, token, token_type, app_version_platform=""):
    doc_data = {
        "doctype": "User Token",
        "entity": entity,
        "token": token,
        "token_type": token_type,
    }

    expiry_in_minutes = user_token_expiry_map.get(token_type, None)
    if expiry_in_minutes:
        # expire previous OTPs
        frappe.db.sql(
            """
			update `tabUser Token` set expiry = CURRENT_TIMESTAMP
			where entity = '{entity}' and token_type = '{token_type}' and used = 0 and expiry > CURRENT_TIMESTAMP;
		""".format(
                entity=entity, token_type=token_type
            )
        )
        doc_data["expiry"] = frappe.utils.now_datetime() + timedelta(
            minutes=expiry_in_minutes
        )

    if app_version_platform:
        doc_data["app_version_platform"] = app_version_platform
        doc_data["partner_id"] = frappe.db.get_value(
            "Partner", {"user_id": entity}, "name"
        )

    user_token = frappe.get_doc(doc_data)
    user_token.save(ignore_permissions=True)

    return user_token


def add_firebase_token(firebase_token, app_version_platform, user=None):
    if not user:
        user = frappe.session.user

    if frappe.db.exists("User Token", {"token_type": "Firebase Token"}):
        old_token = frappe.get_last_doc("User Token",filters={"token_type": "Firebase Token"})
        if old_token:
            token_mark_as_used(old_token)

    get_user_token = frappe.db.get_value(
        "User Token",
        {"token_type": "Firebase Token", "token": firebase_token, "entity": user},
    )
    if get_user_token:
        return

    create_user_token(
        entity=user,
        token=firebase_token,
        token_type="Firebase Token",
        app_version_platform=app_version_platform,
    )

def appErrorLog(title, error):
    d = frappe.get_doc(
        {
            "doctype": "Error Log",
            "title": str("User:") + str(title + " " + "App Error"),
            "error": format_exc(),
        }
    )
    d = d.insert(ignore_permissions=True)
    return d


def generateResponse(is_success=True, status=200, message=None, data={}, error=None):
    response = {}
    if is_success:
        response["status"] = int(status)
        response["message"] = message
        response["data"] = data
    else:
        appErrorLog(frappe.session.user, str(error))
        response["status"] = 500
        response["message"] = message or "Something Went Wrong"
        response["data"] = data
    return response

def log_api(method, request_time, request):
    try:
        method = method
        request_time = request_time
        request = request
        log = frappe.get_doc(
            dict(doctype="API Log", api_name = method, request_time = datetime.now(), request = request)
        ).insert(ignore_permissions=True)
        frappe.db.commit()

        return log

    except Exception:
        frappe.log_error(
            message=frappe.get_traceback(),
            title=_("API Log Error"),
        )

def log_api_response(api_log_doc, api_type, response):
    api_log_doc.response_time = datetime.now()
    api_log_doc.api_type = api_type
    api_log_doc.response = response
    api_log_doc.save(ignore_permissions=True)
    frappe.db.commit()



def log_api_error(mess=""):
    try:
        request_parameters = frappe.local.form_dict
        headers = {k: v for k, v in frappe.local.request.headers.items()}

        title = (
            request_parameters.get("cmd").split(".")[-1].replace("_", " ").title()
            + " API Error"
        )

        error = frappe.get_traceback() + "\n\n" + str(mess) + "\n\n"
        log = frappe.get_doc(
            dict(doctype="API Error Log", error=frappe.as_unicode(error), method=title)
        ).insert(ignore_permissions=True)
        frappe.db.commit()

        return log

    except Exception:
        frappe.log_error(
            message=frappe.get_traceback(),
            title=_("API Error Log Error"),
        )

def regex_special_characters(search, regex=None):
    if regex:
        regex = regex
    else:
        regex = re.compile("[@_!#$%^&*()<>?/\|}{~:`]")

    if regex.search(search) != None:
        return True
    else:
        return False
    
def random_token(length=10, is_numeric=False):
    import random
    import string

    if is_numeric:
        sample_str = "".join((random.choice(string.digits) for i in range(length)))
    else:
        letters_count = random.randrange(length)
        digits_count = length - letters_count

        sample_str = "".join(
            (random.choice(string.ascii_letters) for i in range(letters_count))
        )
        sample_str += "".join(
            (random.choice(string.digits) for i in range(digits_count))
        )

    # Convert string to list and shuffle it to mix letters and digits
    sample_list = list(sample_str)
    random.shuffle(sample_list)
    final_string = "".join(sample_list)
    return final_string


def create_log(log, file_name):
    try:
        log_file = frappe.utils.get_files_path("{}.json".format(file_name))
        logs = None
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                logs = f.read()
            f.close()
        logs = json.loads(logs or "[]")
        logs.append(log)
        with open(log_file, "w") as f:
            f.write(json.dumps(logs))
        f.close()
    except json.decoder.JSONDecodeError:
        log_text_file = (
            log_file.replace(".json", "") + str(frappe.utils.now_datetime()) + ".txt"
        ).replace(" ", "-")
        with open(log_text_file, "w") as txt_f:
            txt_f.write(logs + "\nLast Log \n" + str(log))
        txt_f.close()
        os.remove(log_file)
        frappe.log_error(
            message=frappe.get_traceback()
            + "\n\nFile name -\n{}\n\nLog details -\n{}".format(file_name, str(log)),
            title="Create Log JSONDecodeError",
        )
    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback()
            + "\n\nFile name -\n{}\n\nLog details -\n{}".format(file_name, str(log)),
            title="Create Log Error",
        )


def validate_receiver_nos(receiver_list):
    validated_receiver_list = []
    for d in receiver_list:
        # remove invalid character
        for x in [" ", "-", "(", ")"]:
            d = d.replace(x, "")

        validated_receiver_list.append(d)

    if not validated_receiver_list:
        frappe.throw(_("Please enter valid mobile nos"))

    return validated_receiver_list


def send_sms(receiver_list, msg, sender_name="", success_msg=True):

    import json

    from six import string_types

    if isinstance(receiver_list, string_types):
        receiver_list = json.loads(receiver_list)
        if not isinstance(receiver_list, list):
            receiver_list = [receiver_list]

    receiver_list = validate_receiver_nos(receiver_list)

    arg = {
        "receiver_list": receiver_list,
        "message": frappe.safe_decode(msg).encode("utf-8"),
        "success_msg": success_msg,
    }

    if frappe.db.get_value("SMS Settings", None, "sms_gateway_url"):
        send_via_gateway(arg)
    else:
        frappe.msgprint(_("Please Update SMS Settings"))


def send_via_gateway(arg):
    ss = frappe.get_doc("SMS Settings", "SMS Settings")
    headers = get_headers(ss)

    args = {ss.message_parameter: arg.get("message")}
    for d in ss.get("parameters"):
        if not d.header:
            args[d.parameter] = d.value

    success_list = []
    for d in arg.get("receiver_list"):
        args[ss.receiver_parameter] = d
        status = send_request(ss.sms_gateway_url, args, headers, ss.use_post)

        if 200 <= status < 300:
            success_list.append(d)

    if len(success_list) > 0:
        args.update(arg)
        create_sms_log(args, success_list)
        if arg.get("success_msg"):
            frappe.msgprint(
                _("SMS sent to following numbers: {0}").format(
                    "\n" + "\n".join(success_list)
                )
            )


def get_headers(sms_settings=None):
    if not sms_settings:
        sms_settings = frappe.get_doc("SMS Settings", "SMS Settings")

    headers = {"Accept": "text/plain, text/html, */*"}
    for d in sms_settings.get("parameters"):
        if d.header == 1:
            headers.update({d.parameter: d.value})

    return headers


def send_request(gateway_url, params, headers=None, use_post=False):
    import requests

    if not headers:
        headers = get_headers()

    if use_post:
        response = requests.post(gateway_url, headers=headers, data=params)
    else:
        response = requests.get(gateway_url, headers=headers, params=params)
    # SMS LOG
    import json

    frappe.logger().info(params)
    if type(params["sms"]) == bytes:
        params["sms"] = params["sms"].decode("ascii")
    log = {
        "url": gateway_url,
        "params": params,
        "response": response.json(),
    }
    create_log(log, "sms_log")
    # SMS LOG end
    response.raise_for_status()
    return response.status_code


# Create SMS Log
def create_sms_log(args, sent_to):
    sl = frappe.new_doc("SMS Log")
    from frappe.utils import nowdate

    sl.sent_on = nowdate()
    sl.message = args["message"].decode("utf-8")
    sl.no_of_requested_sms = len(args["receiver_list"])
    sl.requested_numbers = "\n".join(args["receiver_list"])
    sl.no_of_sent_sms = len(sent_to)
    sl.sent_to = "\n".join(sent_to)
    sl.flags.ignore_permissions = True
    sl.save()


def __partner(entity=None):
    res = frappe.get_all("Partner", filters={"user_id": entity})
    if len(res) == 0:
        raise PartnerNotFoundException

    return frappe.get_doc("Partner", res[0].name)


def lender_list():
    res = frappe.get_all("Lender", fields = ["name"])
    if len(res) == 0:
        raise NotFoundException

    return list(i['name'] for i in res)

def bank_list():
    res = frappe.get_all("Bank", fields = ["name"])
    if len(res) == 0:
        raise NotFoundException
    
    return list(i['name'] for i in res)

def pincode_list():
    res = frappe.get_all("Pin Code", fields = ["name"])
    if len(res) == 0:
        raise NotFoundException

    return list(i['name'] for i in res)

def employer_list():
    res = frappe.get_all("Employer", fields = ["name"])
    if len(res) == 0:
        raise NotFoundException

    return list(i['name'] for i in res)

def partner_list():
    res = frappe.get_all("Partner", fields = ["name","partner_name"])
    if len(res) == 0:
        raise NotFoundException
    res = [{'partner_code': entry.pop('name'), 'partner_name': entry['partner_name']} for entry in res]
    return res

@frappe.whitelist()
def authorize_deepvue():
    try:
        ucl.validate_http_method("POST")
        ucl_setting = frappe.get_single("UCL Settings")
        url = "https://production.deepvue.tech/v1/authorize"
        payload = {"client_id" : ucl_setting.deepvue_client_id, "client_secret" : ucl_setting.deepvue_client_secret}
        headers = {'Content-Type' : 'application/x-www-form-urlencoded',}
        api_log_doc = ucl.log_api(method = "Deepvue Authorize", request_time = datetime.now(), request = str("URL" + str(url)+ "\n"+ str(headers) + "\n" + str(payload)))
        response = requests.request("POST",url, headers=headers, data = payload)

        if response.status_code == 200:
            ucl_setting.bearer_token = "Bearer " + (response.json())["access_token"]
            ucl_setting.save(ignore_permissions = True)
            frappe.db.commit()
        else:
            return RespondWithFailureException()
        ucl.log_api_response(api_log_doc = api_log_doc, api_type = "Third Party", response = response.text)

    except ucl.exceptions.APIException as e:
        ucl.log_api_error()
        return e.respond()
    
def attach_files(image_bytes,file_name,attached_to_doctype,attached_to_name,attached_to_field,partner=None):
    base64_encoded_image = image_bytes
    decoded_image = base64.b64decode(base64_encoded_image)
    file = frappe.get_doc(
            {
                "doctype": "File",
                "file_name": file_name,
                "attached_to_doctype": attached_to_doctype,
                "attached_to_name": attached_to_name,
                "attached_to_field" : attached_to_field,
                "content" : decoded_image,
                "is_private": False,
            }
        ).insert(ignore_permissions=True)
    frappe.db.commit()
    file_name_url = file.file_url
    # file_url = "https://a30d86f8e3a043.lhr.life{}".format(file_name_url).replace(" ", "-")
    file_url = frappe.utils.get_url("{}".format(file_name_url).replace(" ", "-"))
    return file_url


def get_firebase_tokens(entity):
    token_list = frappe.db.get_all(
        "User Token",
        filters={"entity": entity, "token_type": "Firebase Token", "used": 0},
        fields=["token"],
    )

    return [i.token for i in token_list]

def send_ucl_push_notification(
    fcm_notification={}, message="", loan="", customer=None
):
    try:
        fcm_payload = {}
        tokens = get_firebase_tokens(customer.user)
        if fcm_notification and tokens:
            if message:
                message = message
            else:
                message = fcm_notification.message

            try:
                random_id = random.randint(1, 2147483646)
                current_time = frappe.utils.now_datetime()
                notification_name = (str(random_id) + " " + str(current_time)).replace(
                    " ", "-"
                )
                sound = "default"
                priority = "high"

                fcm_payload = {
                    "registration_ids": tokens,
                    "priority": priority,
                }

                notification = {
                    "title": fcm_notification.title,
                    "body": message,
                    "sound": sound,
                }

                data = {
                    "click_action": "FLUTTER_NOTIFICATION_CLICK",
                    "name": notification_name,
                    "notification_id": str(random_id),
                    "screen": fcm_notification.screen_to_open,
                    "loan_no": loan if loan else "",
                    "title": fcm_notification.title,
                    "body": message,
                    "notification_type": fcm_notification.notification_type,
                    "time": current_time.strftime("%d %b at %H:%M %p"),
                }
                android = {"priority": priority, "notification": {"sound": sound}}
                apns = {
                    "payload": {"aps": {"sound": sound, "contentAvailable": True}},
                    "headers": {
                        "apns-push-type": "background",
                        "apns-priority": "5",
                        "apns-topic": "io.flutter.plugins.firebase.messaging",
                    },
                }

                fcm_payload["notification"] = notification
                fcm_payload["data"] = data
                fcm_payload["android"] = android
                fcm_payload["apns"] = apns

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": "key=AAAAik2VgcI:APA91bGQzHdxdiU6zLleajH16w-J-oMM36vzaH6-C8y4h5IH5Vx6ubBgcaitMrK5MfkA4QjW8sMQ0UsXs8uUTvH40hl_IrTHE45fuFEBr7yE0Z3XU-DQks9EO07ZwajhEkyZEzP83arB",
                }
                url = "https://fcm.googleapis.com/fcm/send" 
                res = requests.post(
                    url=url,
                    data=json.dumps(fcm_payload),
                    headers=headers,
                )
                res_json = json.loads(res.text)
                log = {
                    "url": url,
                    "headers": headers,
                    "request": data,
                    "response": res_json,
                }

                create_log(log, "Send_UCL_Push_Notification_Log")

                # fa.send_android_message(
                #     title=fcm_notification.title,
                #     body=message,
                #     data=data,
                #     tokens=get_firebase_tokens(customer.user),
                #     priority="high",
                # )
                if res.ok and res.status_code == 200:
                    # Save log for UCL Push Notification
                    frappe.get_doc(
                        {
                            "doctype": "UCL Push Notification Log",
                            "name": notification_name,
                            "title": data["title"],
                            "loan_customer": customer.name,
                            "customer_name": customer.full_name,
                            "loan": data["loan_no"],
                            "screen_to_open": data["screen"],
                            "notification_id": data["notification_id"],
                            "notification_type": data["notification_type"],
                            "time": current_time,
                            "click_action": data["click_action"],
                            "message": data["body"],
                            "is_cleared": 0,
                            "is_read": 0,
                        }
                    ).insert(ignore_permissions=True)
                    frappe.db.commit()
            except (
                requests.RequestException,
                TypeError,
                KeyError,
                ValueError,
                FirebaseError,
            ):
                # To log fcm notification Exception into Frappe Error Log
                raise Exception
    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback()
            + "\nNotification Info:\n"
            + json.dumps(fcm_payload if fcm_payload else customer.name),
            title="UCL Push Notification Error",
        )
