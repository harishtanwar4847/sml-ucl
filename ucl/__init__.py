import frappe
import ucl
import random
import string
import ucl.exceptions as exceptions
from datetime import datetime, timedelta
from traceback import format_exc

__version__ = "0.0.1"


user_token_expiry_map = {
    "Login OTP": 10,
    "Reset Pin OTP": 10,
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

def validate_http_method(*methods):
	if frappe.request:
		if frappe.request.method.upper() not in [method.upper() for method in methods]:
			raise exceptions.MethodNotAllowedException


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


def create_user(first_name, last_name, mobile, email, tester):
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
                "new_password": frappe.mock("password"),
                "roles": [
                    {"doctype": "Has Role", "role": "Loan Customer"},
                    {"doctype": "Has Role", "role": "Spark Tester"},
                ]
                if tester
                else [{"doctype": "Has Role", "role": "Loan Customer"}],
            }
        ).insert(ignore_permissions=True)

        return user
    except Exception as e:
        raise exceptions.APIException(message=str(e))
    

def __user(input=None):
    # get session user if input is not provided
    if not input:
        input = frappe.session.user
    res = frappe.get_all("User", or_filters={"email": input, "username": input})

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


def token_mark_as_used(token):
    if token.used == 0:
        token.used = 1
        token.save(ignore_permissions=True)
        frappe.db.commit()

def create_user_token(entity, token, token_type="OTP", app_version_platform=""):
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
        doc_data["customer_id"] = frappe.db.get_value(
            "Loan Customer", {"user": entity}, "name"
        )

    user_token = frappe.get_doc(doc_data)
    user_token.save(ignore_permissions=True)

    return user_token


def add_firebase_token(firebase_token, app_version_platform, user=None):
    if not user:
        user = frappe.session.user

    
    old_token = frappe.get_last_doc("User Token")
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


def log_api_error(mess=""):
    try:
        """
        Log API error to Error Log

        This method should be called before API responds the HTTP status code
        """

        # AI ALERT:
        # the title and message may be swapped
        # the better API for this is log_error(title, message), and used in many cases this way
        # this hack tries to be smart about whats a title (single line ;-)) and fixes it
        request_parameters = frappe.local.form_dict
        headers = {k: v for k, v in frappe.local.request.headers.items()}
        customer = frappe.get_all("Loan Customer", filters={"user": __user().name})

        if len(customer) == 0:
            message = "Request Parameters : {}\n\nHeaders : {}".format(
                str(request_parameters), str(headers)
            )
        else:
            message = (
                "Customer ID : {}\n\nRequest Parameters : {}\n\nHeaders : {}".format(
                    customer[0].name, str(request_parameters), str(headers)
                )
            )

        title = (
            request_parameters.get("cmd").split(".")[-1].replace("_", " ").title()
            + " API Error"
        )

        error = frappe.get_traceback() + "\n\n" + str(mess) + "\n\n" + message
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
