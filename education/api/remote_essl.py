import frappe
import pymysql
import json
from datetime import datetime
from frappe.utils import cint, cstr, flt, formatdate, getdate, now

frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("remote_essl", allow_site=True, file_count=10)

@frappe.whitelist( allow_guest=True )
def get_essl_data():
    # Replace with your actual connection details
    db_connection = pymysql.connect(
        host="13.201.252.13",
        port=3306,
        user="remote_user",
        password="?5e{>xdQZX9{b",
        database="essl"
    )
    attendance_data = ""
    
    device_id_list_str = ''
    deviceLists = getDeviceList()

    # logger.debug(deviceLists)

    cursor = db_connection.cursor()

    for id in deviceLists:
        # if len(device_id_list_str) != 0:
        #     device_id_list_str += ','
        # device_id_list_str += f"'{id.device_id}'"
        
        current_datetime = now()
        lastSynchedTime = ""
        shiftTypeDetails = getLastSynchedTime(id.shift_type)
        # logger.debug(shiftTypeDetails)

        if shiftTypeDetails[0].last_sync_of_checkin:
            lastSynchedTime = shiftTypeDetails[0].last_sync_of_checkin
        else:
            lastSynchedTime = current_datetime

        # logger.debug(lastSynchedTime)
        sql_query = f"SELECT dlp.DeviceLogId, dlp.DownloadDate, dlp.DeviceId, dlp.UserId, dlp.LogDate, dlp.Direction, emp.EmployeeCode FROM DeviceLogs_Processed dlp, Employees emp WHERE dlp.DeviceId = {id.device_id} AND dlp.LogDate > '{lastSynchedTime}' AND dlp.UserId = emp.EmployeeCodeInDevice"
        # logger.debug(sql_query)
        # Example query to fetch attendance data
        cursor.execute(sql_query)

        # Fetch all rows
        attendance_data = cursor.fetchall()

        # Convert each tuple to a dictionary
        json_data = []
        device_user_ids = set()
        for row in attendance_data:
            # Replace column names with actual names from your query
            row_dict = {"DeviceLogId": row[0], "DownloadDate": row[1],  
                        "DeviceId": row[2], "UserId": row[3], 
                        "LogDate": row[4], "Direction": row[5],
                        "EmployeeCode": row[6]}
            json_data.append(row_dict)
            device_user_ids.add(row[3])

        # logger.debug(f"json_data = {json_data}")
        # logger.debug(device_user_ids)
        if json_data and device_user_ids:
            # Convert the list of dictionaries to JSON string
            final_json = json.dumps(json_data, default=datetime_handler)
            
            # Load the JSON string into a Python object
            data = json.loads(final_json)
            device_ids_mapped_to_emp_ids = []
            if isinstance(data, list):
                device_ids_mapped_to_emp_ids = frappe.db.sql(
                    """select
                        name, employee_name, attendance_device_id from tabEmployee
                    where
                        attendance_device_id in (%s)
                    """
                    % ", ".join(["%s"] * len(device_user_ids)),
		            tuple(device_user_ids),
                    as_dict=1,
                )

                # logger.debug(f"Emp IDs = {device_ids_mapped_to_emp_ids}")
                for attendance in data:
                    employee_id = ""
                    for emp_detail in device_ids_mapped_to_emp_ids:
                        if (emp_detail.attendance_device_id == attendance["UserId"]):
                            employee_id = emp_detail.name
                            break
                    # logger.debug(f"employee_id = {employee_id}")

                    if employee_id:
                        try:
                            doc = frappe.new_doc("Employee Checkin")
                            doc.employee = employee_id
                            doc.time = attendance["LogDate"]
                            doc.device_id = attendance["UserId"]
                            doc.log_type = attendance["Direction"].upper()
                            #doc.skip_auto_attendance = "1"
                            doc.insert()
                            frappe.db.commit()
                        except Exception as e:
                            logger.debug(f"Error: {e}. Employee = {employee_id}")
            else:
                logger.debug("Unexpected JSON format. Expected a list of dictionaries.")

            #Update the last_synched date with current datetime.
            # logger.debug(f"updating sync time to {current_datetime}")
            frappe.db.sql("""
                        UPDATE `tabShift Type` SET last_sync_of_checkin = %s WHERE name = %s
                        """,
                        (current_datetime, id.shift_type)
                        )

    # Close cursor and connection when done
    cursor.close()
    db_connection.close()

    return attendance_data

def datetime_handler(x):
  """Custom handler to convert datetime objects to JSON serializable format."""
  if isinstance(x, datetime):
    return x.isoformat()
  raise TypeError("Unknown type")  # Raise error for other unsupported types (optional)
  return x  # Default behavior for other types

def getDeviceList():
    try:
        deviceLists = frappe.db.sql("""
                                    select device_id, shift_type
                                    from 
                                    `tabEssl` 
                                """,
                                as_dict=1
                                )
        return deviceLists
    except Exception as e:
        return e

def getLastSynchedTime(shiftName):
    try:
        lastSynchedTime = frappe.db.sql("""
                                    select name, last_sync_of_checkin
                                    from 
                                    `tabShift Type` 
                                    where 
                                    name = %s
                                """,
                                (shiftName),
                                as_dict=1
                                )
        return lastSynchedTime
    except Exception as e:
        return e