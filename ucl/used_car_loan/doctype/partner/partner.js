// Copyright (c) 2024, Developers and contributors
// For license information, please see license.txt

frappe.ui.form.on("Partner", {
	refresh: function (frm) {
        if (!frm.doc.is_email_verified) {
          frm.add_custom_button("Resend Verification Email", () => {
            console.log(frm.doc.user);
            frappe.call({
              type: "POST",
              method: "ucl.auth.resend_verification_email",
              args: { email: frm.doc.user_id },
            });
          });
        }
      },
});
