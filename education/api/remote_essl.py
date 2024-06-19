import frappe
import pymysql

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
    cursor = db_connection.cursor()

    # Example query to fetch attendance data
    cursor.execute("SELECT * FROM DeviceOperationLogs WHERE DeviceOperationLogId = 1")

    # Fetch all rows
    attendance_data = cursor.fetchall()

    # # Close cursor and connection when done
    cursor.close()
    db_connection.close()

    # # Now you have `attendance_data` that you can process
    return attendance_data