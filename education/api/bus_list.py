import frappe
from frappe import auth

transport = []
# frappe.utils.logger.set_log_level("DEBUG")
# logger = frappe.logger("buses_api", allow_site=True, file_count=10)

@frappe.whitelist(allow_guest=True)
def bus_details(user):
    # logger.debug(user)
    try:
        # secret_key = frappe.get_request_header('X-Secret-Key')
        # if not secret_key or secret_key != frappe.local.conf.api_secret_key:
        #     frappe.throw("Invalid or missing secret key.", frappe.PermissionError)
        students = frappe.db.get_list("Student", filters={"user": user},)
        # logger.debug(f"stu= {students}")
        employee = []
        if students:
            # logger.debug(students)
            student_id_list = [student["name"] for student in students]
            transport = frappe.db.sql("""
                SELECT distinct v.vehicle_no, a.license_plate
                FROM `tabVehicles` v, `tabTrackezy Map` m, `tabVehicle Alias` a
                WHERE v.parent = m.name AND 
                a.vehicle_no = v.vehicle_no AND
                m.student IN (%s)
                """ % ", ".join(["%s"] * len(student_id_list)), tuple(student_id_list), as_dict=1,)
        else:
            employee = frappe.db.get_list("Employee", filters={"user_id": user})
            # logger.debug(f"emp= {employee[0].name}")
            if employee:
                transport = frappe.db.sql("""
                    SELECT distinct v.vehicle_no, a.license_plate
                    FROM `tabVehicles` v, `tabTrackezy Map` m, `tabVehicle Alias` a
                    WHERE v.parent = m.name AND 
                    a.vehicle_no = v.vehicle_no AND
                    m.employee = (%s)
                    """, employee[0].name, as_dict=1,)
                # logger.debug(f"tra= {transport}") 
    except frappe.exceptions.AuthenticationError:
        frappe.clear_messages()
        frappe.local.response["message"] = {
            "success_key":0,
            "message":"Can not find students buses!"
        }
        return
    user = frappe.get_doc('User', frappe.session.user)
    frappe.response["data"] = {
       "transport": transport
    }
 