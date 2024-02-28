import frappe


def execute():
    las_settings = frappe.get_single("UCL Settings")

    las_settings.update(
        {
            "deepvue_client_id": "live_switchmyloan",
            "deepvue_client_secret": "66cb63695be3cb53f991cb907ab6c2d1fdd7d8d651fb834f48fe5a171ec41b2a",
            "digio_client_id": "AIXIC9J5YKIYDGBTN9LG19TGBRGUYJ38",
            "digio_client_secret": "DU8RQISBGDLJ5IQXKJZSWTXERBHWZWUO",
            "pan_ocr": "https://production.deepvue.tech/v1/documents/extraction/ind_pancard",
            "pan_plus": "https://production.deepvue.tech/v1/verification/pan-plus?pan_number={id_number}",
            "rc_advance": "https://production.deepvue.tech/v1/verification/rc-advanced?rc_number={rc_number}",
            "aadhaar_ocr": "https://production.deepvue.tech/v1/documents/extraction/ind_aadhaar",
            "penny_drop": "https://api.digio.in/client/verify/bank_account",
            "bre": "http://bre.switchmyloan.in/v1/bre/used-car-loans/offers-post-new",
            "get_esign_details": "https://api.digio.in/v2/client/document/{document_id}",
            "esign_request": "https://api.digio.in/v2/client/document/upload",
            "download_esign_document": "https://api.digio.in/v2/client/document/download?document_id={document_id}",
            "glib_client_id": "a6ba4e40dbd79a6c",
            "glib_client_secret": "d3610b04b0fbd5965d9adc5cbb49e3db",
            "create_workorder": "https://switch-my-loan.staging.autosift.cloud/api/work_orders/?report_type={report_type}",
            "add_bank_statement": "https://switch-my-loan.staging.autosift.cloud/api/work_orders/{id}/bank_statement/",
            "process_workorder": "https://switch-my-loan.staging.autosift.cloud/api/work_orders/{id}/process/",
            "retrieve_workorder": "https://switch-my-loan.staging.autosift.cloud/api/work_orders/{id}/",
            "download_report": "https://switch-my-loan.staging.autosift.cloud/api/work_orders/{id}/download/",
            "ibb_token": "tQmqVauvHeV76aQ2wSXUzuRToWDe7GBiMQ58anV",
            "ibb_url": "https://system.indianbluebook.com/api/SwitchMyLoan",
            "enhance_match_register": "https://consumer.experian.in:8443/ECV-P2/content/registerEnhancedMatchMobileOTP.action",
            "full_match_register": "https://consumer.experian.in:8443/ECV-P2/content/registerSingleActionMobileOTP.action",
            "generate_otp" : "https://consumer.experian.in:8443/ECV-P2/content/generateMobileOTP.action",
            "validate_otp": "https://consumer.experian.in:8443/ECV-P2/content/validateMobileOTP.action",
            "privacy_policy": None,
            "terms_of_use": None,
        }
    )
    # TODO: move terms of use and privacy document in public folder and add key for those in above dict
    las_settings.save()
    frappe.db.commit()