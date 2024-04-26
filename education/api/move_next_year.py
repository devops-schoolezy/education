import frappe

from frappe.model.document import Document


@frappe.whitelist( allow_guest = True )
def move_students_to_next_class(current_program,next_program,current_year,next_year):
    current_year_students = frappe.get_all("Program Enrollment", filters = {"program":current_program, "academic_year":current_year}, fields = ["student","academic_year","program"])
   
    for program_enrollment in current_year_students:
        new_program_enrollment = frappe.new_doc("Program Enrollment")
        new_program_enrollment.update({
            "student": program_enrollment.student,
            "academic_year": next_year,
            "program": next_program,
        })    
        new_program_enrollment.save()
        new_program_enrollment.submit()
        frappe.msgprint("Student Enrolled Next Year")