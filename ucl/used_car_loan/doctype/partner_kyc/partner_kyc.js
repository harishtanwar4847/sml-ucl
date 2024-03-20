// Copyright (c) 2024, Developers and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Partner KYC", {
// 	refresh(frm) {
//         $('.modal-actions').hide();
// 	},

//     before_workflow_action: (frm) => {
//         if (frm.selected_workflow_action === "Reject") {

//             var me = this;
//             var d = new frappe.ui.Dialog({
//                 title: __('Reason for Reject'),
//                 fields: [
//                     {
//                         "fieldname": "reason_for_reject",
//                         "fieldtype": "Text",
//                         "reqd": 1,
//                     }
//                 ],
//                 primary_action: function () {
//                     var data = d.get_values();
//                     let reason_for_reject = 'Reason for Reject: ' + data.reason_for_reject;
//                     if (window.timeout) {
//                         clearTimeout(window.timeout)
//                         delete window.timeout
//                     }
//                     window.timeout = setTimeout(function () {
//                         frm.set_value("reason_of_rejection", data.reason_for_reject)
//                         frm.refresh_field("reason_of_rejection")
//                         frm.save()
//                     }, 2500)

//                     frappe.call({
//                         method: "frappe.desk.form.utils.add_comment",
//                         args: {
//                             reference_doctype: frm.doc.doctype,
//                             reference_name: frm.doc.name,
//                             content: __(reason_for_reject),
//                             comment_email: frappe.session.user,
//                             comment_by: frappe.session.user_fullname
//                         },
//                         callback: function (r) {
//                             frm.reload_doc();
//                             d.hide();
//                         }
//                     });
//                 }
//             });
//             d.show();
//         }

//     },
// });
