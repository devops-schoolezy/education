from __future__ import unicode_literals
import frappe

import json
from frappe.utils import floor, flt, today, cint
from frappe import _

@frappe.whitelist( allow_guest=True )
def getMyTodaysTimeTable(instructor_name):
    try:
        todayDate = frappe.utils.getdate()
        time_table = frappe.db.get_list("Course Schedule",filters={"instructor": instructor_name,
                                                                   "schedule_date": ["=", todayDate]},
                                                          fields=['student_group', 'instructor', 'program', 'course', 'schedule_date', 'from_time', 'to_time'],
                                                          order_by='from_time')

        response_data = {
        'status': 'success',
        'data': {
            'time_table': time_table
            }
        }

        return response_data

        # Convert the dictionary to JSON
        #response_json = frappe.as_json(time_table)

        #return response_json

    except Exception as e:
        # Handle exceptions here
        error_message = f"An error occurred: {str(e)}"
        response_data = {
            'status': 'failed',
            'message': error_message
        }

        return response_data
