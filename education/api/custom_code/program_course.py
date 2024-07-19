import frappe

@frappe.whitelist()
def get_course(program):
    course_list = []
    #course_list = frappe.get_all("Program Course", 
    #                            fields=["course"],
    #                            filters = {"parent" : program})
    try:
        course_list = frappe.db.sql("""
                                select course
                                from 
                                `tabProgram Course` 
                                where 
                                parent = %s
                                """, 
                                (program),
                                    as_dict=1,
                                )
    except Exception as e:
        frappe.msgprint(e)   
    return course_list
