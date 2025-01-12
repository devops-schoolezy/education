from __future__ import unicode_literals
import frappe
from frappe import auth

import json
from frappe import _
frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("login_api", allow_site=True, file_count=10)

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
    transport = []
    emp_id = ""

    # if (user.user_category == "Student"):
    # employee = []
    try:
        # logger.debug(f"entered emp == {user.email}")
        # employee1 = frappe.db.get_list("Employee", 
        #                               filters={"user_id": user.email},
        #                               fields=["name", "custom_is_teaching_staff"])
        # logger.debug(f"employee id = {employee} ---- {len(employee)}")
        emp_id, custom_is_teaching_staff = frappe.db.get_value('Employee', {'user_id': user.email}, ['name', 'custom_is_teaching_staff'])
        # logger.debug(f"employee id1 = {emp_id} ---- {custom_is_teaching_staff}")
    except Exception as e:  
        # logger.debug(f"exception == {e}")  
        emp_id = ""
        custom_is_teaching_staff = 0
        
    if len(emp_id) == 0: 
        # based on permission it will retreive only the students who are accessible
        students = frappe.db.get_list("Student",fields=["name", "first_name","gender"])
        logger.debug(f"students... {len(students)}")

    if len(students) > 0:
        
        student_id_list = [student["name"] for student in students]
        # logger.debug(student_id_list)
        # query = """
        #     SELECT v.vehicle_no AS vehicle
        #     FROM `tabVehicles` v
        #     INNER JOIN `tabTrackezy Map` m ON v.parent = m.name
        #     WHERE m.student IN (%s)
        #     """ % ", ".join(["%s"] * len(student_id_list)), tuple(student_id_list), as_dict=1,
        # logger.debug(query)
        transport = frappe.db.sql("""
            SELECT distinct v.vehicle_no, a.license_plate
            FROM `tabVehicles` v, `tabTrackezy Map` m, `tabVehicle Alias` a
            WHERE v.parent = m.name AND 
            a.vehicle_no = v.vehicle_no AND
            m.student IN (%s)
            """ % ", ".join(["%s"] * len(student_id_list)), tuple(student_id_list), as_dict=1,)
        # transport = frappe.db.sql("""
        #     SELECT v.vehicle_no AS vehicle
        #     FROM `tabVehicles` v
        #     INNER JOIN `tabTrackezy Map` m ON v.parent = m.name
        #     WHERE m.student IN (%s)
        #     """ % ','.join(['%s'] * len(student_id_list)))
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
        if len(emp_id) > 0: 
            if custom_is_teaching_staff == 1:
                instructor = frappe.db.get_list("Instructor",
                                        filters={"employee": emp_id},
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
                                (emp_id),
                                    as_dict=1,
                                )
                except Exception as e:
                    frappe.msgprint(e)    
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
                "transport":transport,
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

