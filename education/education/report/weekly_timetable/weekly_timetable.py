# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import get_first_day_of_week

def execute(filters=None):
	columns, data = [], []

	filters = frappe._dict(filters or {})
	columns = get_columns()
	data = get_data(filters)

	return columns, data

def get_columns():
	columns = [
		{
			"fieldtype": "Link",
			"fieldname": "student_group",
			"options": "Student Group",
			"label": "Student Group",
			"width":150
		},
		{
			"fieldname":"schedule_date",
			"label":"Schedule Date",
			"options":"",
			"fieldtype":"Date",
			"width":150
		},
		{
			"fieldname":"from_time",
			"label":"From Time",
			"options":"",
			"fieldtype":"Time",
			"width":150
		},
		{
			"fieldname":"to_time",
			"label":"To Time",
			"options":"",
			"fieldtype":"Time",
			"width":150
		},
		{
			"fieldtype": "Link",
			"fieldname": "course",
			"options": "Course",
			"label": "Course",
			"width":150
		},
		{
			"fieldtype": "Link",
			"fieldname": "instructor",
			"options": "Instructor",
			"label": "Instructor",
			"width":150
		},
		{
			"fieldtype": "Link",
			"fieldname": "room",
			"options": "Room",
			"label": "Room",
			"width":150
		}
	]
	
	return columns 

def get_data(filters=None):
	filters = frappe._dict(filters or {})

	start = filters.start_date
	end = filters.end_date
	section = filters.student_group
	data = get_course_schedule(start, end, section)
	return data

def get_course_schedule(start, end, section):

	data = frappe.db.sql(
		"""select course, schedule_date,
			from_time, to_time,
			room, student_group, instructor,
			to_char(schedule_date, 'Day') as day
		from `tabCourse Schedule`
		where ( schedule_date between %(start)s and %(end)s )
		and student_group = %(section)s
		order by schedule_date asc""",
		{"start": start, "end": end, "section": section},
		as_dict=True
	)

	return data