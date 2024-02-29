import frappe


def execute():
    sms_settings = frappe.get_single("SMS Settings")

    sms_settings.sms_gateway_url = "http://bulkpush.mytoday.com/BulkSms/SingleMsgApi"
    sms_settings.message_parameter = "Text"
    sms_settings.receiver_parameter = "To"
    sms_settings.parameters = []

    parameter_list = [{"parameter": "username", "value": "9920706289"}, {"parameter": "password", "value": "SML2021@123"}, {"parameter": "feedid", "value": "385302"}, {"parameter": "aysnc", "value": 0}, {"parameter": "short", "value": 0}, {"parameter": "senderid", "value": "SML"}]
    for i in parameter_list:
        sms_settings.append("parameters",i)
    sms_settings.save()
    frappe.db.commit()