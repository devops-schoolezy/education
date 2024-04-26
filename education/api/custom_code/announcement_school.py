import frappe

@frappe.whitelist()
def school_mail(institution,doc,image,event,announcement_date,message):
    student_list = frappe.db.get_list("Student", filters = {"custom_institution":institution}, fields = 'student_email_id')
    frappe.msgprint(student_list)
    for students in student_list:
        frappe.sendmail(recipients=students.student_email_id, subject=event, message= "Dear Parents, \n  {0} is on {1}\n.{2}\n        Thank You".format(event,announcement_date,message),attachments=[frappe.attach_print("Announcement", doc, file_name=image)])
        frappe.msgprint("Mail Send")
        frappe.msgprint(student_list)
