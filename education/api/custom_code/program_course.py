import frappe

@frappe.whitelist()
def get_course(program):
    course_list = frappe.get_all("Program Course", 
                                fields=["course"],
                                filters = {"parent" : program})
    return course_list
