# Copyright (c) 2024, Developers and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.document import Document
from ucl import *

import ucl


class UserToken(Document):
    def after_insert(self):
        if self.token_type in [
            "OTP",
            "Pledge OTP",
            "Withdraw OTP",
            "Unpledge OTP",
            "Sell Collateral OTP",
            "Lien OTP",
            "Invoke OTP",
            "Revoke OTP",
        ]:
            token_type = self.token_type.replace(" ", "")
            # if self.token_type in [
            #     "Pledge OTP",
            #     "Unpledge OTP",
            # ]:
            #     doc = frappe.get_all(
            #         "User KYC", filters={"user": frappe.session.user}, fields=["*"]
            #     )[0]
            #     # doc["doctype"] = "User KYC"
            #     # doc["otp_info"] = {
            #     #     "token_type": self.token_type.replace(" ", ""),
            #     #     "token": self.token,
            #     # }
            #     # frappe.enqueue_doc(
            #     #     "Notification",
            #     #     "OTP for Spark Loans",
            #     #     method="send",
            #     #     doc=doc,
            #     # )
            #     if doc:
            #         email_otp = frappe.db.sql(
            #             "select message from `tabNotification` where name='OTP for Spark Loans';"
            #         )[0][0]
            #         email_otp = email_otp.replace("investor_name", doc.fullname)
            #         email_otp = email_otp.replace("token_type", token_type)
            #         email_otp = email_otp.replace("token", self.token)
            #         frappe.enqueue(
            #             method=frappe.sendmail,
            #             recipients=[doc.email],
            #             sender=None,
            #             subject="OTP for Spark Loans",
            #             message=email_otp,
            #             queue="short",
            #             delayed=False,
            #             job_name="Spark OTP on Email",
            #         )
            # else:
            #     doc = frappe.get_all(
            #         "User", filters={"username": self.entity}, fields=["*"]
            #     )
            #     if doc:
            #         # doc[0]["doctype"] = "User"
            #         # doc[0]["otp_info"] = {
            #         #     "token_type": self.token_type.replace(" ", ""),
            #         #     "token": self.token,
            #         # }
            #         # frappe.enqueue_doc(
            #         #     "Notification",
            #         #     "Other OTP for Spark Loans",
            #         #     method="send",
            #         #     doc=doc[0],
            #         # )
            #         email_otp = frappe.db.sql(
            #             "select message from `tabNotification` where name='Other OTP for Spark Loans';"
            #         )[0][0]
            #         email_otp = email_otp.replace("investor_name", doc[0].full_name)
            #         email_otp = email_otp.replace("token_type", token_type)
            #         email_otp = email_otp.replace("token", self.token)
            #         frappe.enqueue(
            #             method=frappe.sendmail,
            #             recipients=[doc[0].email],
            #             sender=None,
            #             subject="OTP for Spark Loans",
            #             message=email_otp,
            #             queue="short",
            #             delayed=False,
            #             job_name="Spark OTP on Email",
            #         )

            # # las_settings = frappe.get_single("LAS Settings")
            # # app_hash_string = (las_settings.app_identification_hash_string,)
            # # "Your {token_type} for UCL is {token}. Do not share your {token_type} with anyone.{app_hash_string}"
            # expiry_in_minutes = ucl.user_token_expiry_map.get(self.token_type, None)
            # # mess = frappe._(
            # #     """Dear Customer,
            # #     Your {token_type} for Spark Loans is {token}. Do not share your {token_type} with anyone.{app_hash_string} Your OTP is valid for {expiry_in_minutes} minutes.
            # #     -Spark Loans""").format(
            # #     token_type=self.token_type.replace(" ",""),
            # #     token=self.token,
            # #     app_hash_string=app_hash_string,
            # #     expiry_in_minutes=expiry_in_minutes,
            # # )

            # mess = frappe._(
            #     "Dear Customer, Your {token_type} for Spark Loans is {token}. Do not share your {token_type} with anyone. Your OTP is valid for 10 minutes -Spark Loans"
            # ).format(
            #     token_type=self.token_type.replace(" ", ""),
            #     token=self.token,
            #     # expiry_in_minutes=expiry_in_minutes,
            # )

            # frappe.enqueue(method=send_sms, receiver_list=[self.entity], msg=mess)
        if self.token_type == "Email Verification Token":
            doc = frappe.get_doc("User", self.entity).as_dict()
            doc["url"] = frappe.utils.get_url(
                "/api/method/ucl.auth.verify_user?token={}&user={}".format(
                    self.token, self.entity
                )
            )
            frappe.enqueue_doc(
                "Notification",
                "User Email Verification",
                method="send",
                # now=True,
                doc=doc,
            )
        elif self.token_type == "Forgot Pin OTP":
            pass
            # partner = frappe.get_all(
            #     "Partner", filters={"user_id": self.entity}, fields=["*"]
            # )[0]
            # expiry_in_minutes = ucl.user_token_expiry_map.get(self.token_type, None)

            # # if customer.choice_kyc:
            # #     doc = frappe.get_doc("User KYC", customer.choice_kyc).as_dict()
            # #     full_name = doc.fullname
            # #     if doc.mob_num:
            # #         mob_num = doc.mob_num
            # #     else:
            # #         mob_num = doc.ckyc_mob_no
            # # else:
            # #     doc = frappe.get_doc("User", self.entity).as_dict()
            # #     full_name = doc.full_name
            # #     mob_num = doc.phone

            # # doc["otp_info"] = {
            # #     "token_type": self.token_type,
            # #     "token": self.token,
            # #     "expiry_in_minutes": expiry_in_minutes,
            # # }
            # user_doc = frappe.get_doc("User", self.entity).as_dict()
            # # user_doc["otp_info"] = {
            # #     "token_type": self.token_type.replace(" ", ""),
            # #     "token": self.token,
            # # }

            # # frappe.enqueue_doc(
            # #     "Notification",
            # #     "Other OTP for Spark Loans",
            # #     method="send",
            # #     doc=user_doc,
            # # )
            # if doc:
            #     email_otp = frappe.db.sql(
            #         "select message from `tabNotification` where name='Other OTP for Spark Loans';"
            #     )[0][0]
            #     email_otp = email_otp.replace("investor_name", full_name)
            #     email_otp = email_otp.replace(
            #         "token_type", self.token_type.replace(" ", "")
            #     )
            #     email_otp = email_otp.replace("token", self.token)
            #     frappe.enqueue(
            #         method=frappe.sendmail,
            #         recipients=[doc.email],
            #         sender=None,
            #         subject="OTP for Spark Loans",
            #         message=email_otp,
            #         queue="short",
            #         delayed=False,
            #         job_name="Spark OTP on Email",
            #     )

            # """changes as per latest email notification list-sent by vinayak - email verification final 2.0"""
            # # mess = _(
            # #     """<html><body><h3>Dear Customer,<h3><br>
            # # Your {token_type} for Spark Loans is {token}. Do not share your {token_type} with anyone.<br>
            # # Your OTP is valid for {expiry_in_minutes} minutes<br>
            # # -Spark Loans</body></html>"""
            # # ).format(
            # #     token_type=doc.get("otp_info").get("token_type").replace(" ", ""),
            # #     token=doc.get("otp_info").get("token"),
            # #     expiry_in_minutes=doc.get("otp_info").get("expiry_in_minutes"),
            # # )

            # # frappe.enqueue(
            # #     method=frappe.sendmail,
            # #     recipients=[doc.email if doc.email else doc.user],
            # #     sender=None,
            # #     subject="Forgot Pin Notification",
            # #     message=mess,
            # # )

            # msg = frappe._(
            #     "Dear Customer, Your {token_type} for Spark Loans is {token}. Do not share your {token_type} with anyone. Your OTP is valid for 10 minutes -Spark Loans"
            # ).format(
            #     token_type=self.token_type.replace(" ", ""),
            #     token=self.token,
            #     # expiry_in_minutes=expiry_in_minutes,
            # )
            # if msg:
            #     receiver_list = [str(customer.phone)]
            #     if mob_num:
            #         receiver_list.append(str(mob_num))

            #     receiver_list = list(set(receiver_list))

            #     frappe.enqueue(method=send_sms, receiver_list=receiver_list, msg=msg)

