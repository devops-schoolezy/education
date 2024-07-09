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

        sql_query = f"SELECT dlp.DeviceLogId, dlp.DownloadDate, dlp.DeviceId, dlp.UserId, dlp.LogDate, dlp.Direction, emp.EmployeeCode FROM DeviceLogs_Processed dlp, Employees emp WHERE dlp.DeviceId = {id.device_id} AND dlp.LogDate > '{id.last_synched}' AND dlp.UserId = emp.EmployeeCodeInDevice"
        logger.debug(sql_query)
        
        # Example query to fetch attendance data
        cursor.execute(sql_query)

        # Fetch all rows
        attendance_data = cursor.fetchall()

        # Convert each tuple to a dictionary
        json_data = []
        for row in attendance_data:
            # Replace column names with actual names from your query
            row_dict = {"DeviceLogId": row[0], "DownloadDate": row[1],  
                        "DeviceId": row[2], "UserId": row[3], 
                        "LogDate": row[4], "Direction": row[5],
                        "EmployeeCode": row[6]}
            json_data.append(row_dict)

        if json_data:
            # Convert the list of dictionaries to JSON string
            final_json = json.dumps(json_data, default=datetime_handler)
            # Load the JSON string into a Python object
            data = json.loads(final_json)

            if isinstance(data, list):
                for attendance in data:
                    doc = frappe.new_doc("Employee Checkin")
                    doc.employee = attendance["EmployeeCode"]
                    doc.time = attendance["LogDate"]
                    doc.device_id = attendance["DeviceId"]
                    doc.log_type = attendance["Direction"].upper()
                    #doc.skip_auto_attendance = "1"
                    doc.insert()
            else:
                logger.debug("Unexpected JSON format. Expected a list of dictionaries.")

            #Update the last_synched date with current datetime.
            frappe.db.sql("""
                        UPDATE `tabEssl` SET last_synched = %s WHERE device_id = %s
                        """,
                        (current_datetime, attendance["DeviceId"])
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
                                    select device_id, last_synched
                                    from 
                                    `tabEssl` 
                                """,
                                as_dict=1
                                )
        return deviceLists
    except Exception as e:
        return e
