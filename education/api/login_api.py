from __future__ import unicode_literals
import frappe
from frappe import auth

import json
from frappe.utils import floor, flt, today, cint
from frappe import _

@frappe.whitelist( allow_guest=True )
def login(usr, pwd):
    try:
        login_manager = frappe.auth.LoginManager()
        login_manager.authenticate(user=usr, pwd=pwd)
        login_manager.post_login()

    except frappe.exceptions.AuthenticationError:
        frappe.clear_messages()
        frappe.local.response["message"] = {
            "success_key": 0,
            "error": {
                "code": 401,
                "message":"Invalid Username / Password"
            },
            "data": {}
        }
        return #Ture
    
    
    api_generate = generate_keys(frappe.session.user)
    user = frappe.get_doc('User', frappe.session.user)

    students = []
    stuprogdata = []
    stugrpdata = []
    instructor = []
    driver = []

    if (user.user_category == "Student"):
        students = frappe.db.get_list("Student",fields=["name", "first_name","gender"])

        for stu in students:
            students_program = frappe.db.get_list("Program Enrollment", 
                                filters={"student": stu["name"]},
                                fields=["student","program"])
            if students_program:
                stuprogdata.append(students_program)
            
            students_group = frappe.db.get_list("Student Group", 
                                filters={"student": stu["name"]},
                                fields=["name"])
            if students_group:
                for stugrp in students_group:
                    studentgrp = '{"student_id":"'+str(stu["name"])+'",'
                    studentgrp += '"section":"'+str(stugrp["name"])+'"}'
                stugrpdata.append(json.loads(studentgrp))
    else:
        employee = frappe.db.get_list("Employee", 
                                      filters={"user_id": user.email},
                                      fields=["name", "custom_is_teaching_staff"])
        if employee[0].custom_is_teaching_staff == 1:
            instructor = frappe.db.get_list("Instructor",
                                    filters={"employee": employee[0].name},
                                    fields=["name", "instructor_name", "status", "department", "employee"])
        else:
            try:
                driver = frappe.db.sql("""
                            select name, full_name, status, cell_number, employee
                            from 
                            `tabDriver` 
                            where 
                            employee = %s
                            """, 
                            (employee[0].name),
                                as_dict=1,
                            )
            except Exception as e:
                frappe.msgprint(_("Error: {0}".format(e), raise_exception=True))    
            # driver = frappe.db.get_list("Driver",
            #                         filters={"employee": employee[0].name},
            #                         fields=["name", "full_name", "status", "cell_number", "employee"])


    # Query company[school] table to get the value for initial_setup field.
    # initial_setup is used to determine the school setup has been completed or not.
    # If setup completed, the count of all the table is not necessary.
    list_company = frappe.db.get_list("Company", fields=['company_name', 'custom_initial_setup'],)
    company_name = list_company[0].company_name
    custom_initial_setup = list_company[0].custom_initial_setup
    
    company_list = frappe.db.get_list("Company", filters={"company_name": company_name}, fields=["company_name","custom_latitude","custom_longitude", "custom_surrounding_meters"])
    
    todayDate = frappe.utils.getdate()
    currentYear = todayDate.year
    currentMonth = todayDate.month

# Calculate the academic year
    if (currentMonth > 4) :
        academicYear = str(currentYear) + "-" + str(currentYear+1)
    else:
        academicYear = str(currentYear-1) + "-" + str(currentYear)
    
    dbAcademicYear = frappe.db.get_list("Academic Year",
                        filters={"academic_year_name": academicYear},
                        fields=["academic_year_name"])

        
    frappe.response["message"] = {
            "successs": 1,
            "error": {
                "code": 200,
                "message": "Authentication Success"
            },
            "data": {
                "sid": frappe.session.sid,
                "api_key":user.api_key,
                "api_secret":api_generate,
                "username":user.username,
                "fullname":user.full_name,
                "firstname":user.first_name,
                "email":user.email,
                "user_image":user.user_image,
                "custom_initial_setup":custom_initial_setup,
                "childrens":students,
                "program":stuprogdata,
                "section":stugrpdata,
                "school":company_list,
                "academic_year": dbAcademicYear,
                "instructor": instructor,
                "driver": driver,
                "roles":user.roles
                }
            }

def generate_keys(user):
    user_details = frappe.get_doc('User', user)
    api_secret = frappe.generate_hash(length=15)

    if not user_details.api_key:
        api_key = frappe.generate_hash(length=15)
        user_details.api_key = api_key

    user_details.api_secret = api_secret
    user_details.save()
    

    return api_secret

