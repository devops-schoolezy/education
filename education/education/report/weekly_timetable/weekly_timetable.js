// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Weekly TimeTable"] = {
	"filters": [
		// {
		// 	"fieldname":"academic_year",
		// 	"label": "Academic Year",
		// 	"fieldtype": "Link",
		// 	"options": "Academic Year",
		// 	"reqd": 1
		// },
		{
			"fieldname":"student_group",
			"label": "Student Group",
			"fieldtype": "Link",
			"options": "Student Group",
			"reqd": 1,
			// "get_query": function() {
			// 	return{
			// 		filters: {
			// 			"group_based_on": "Batch",
			// 			"academic_year": frappe.query_report.get_filter_value('academic_year')
			// 		}
			// 	};
			// }
		},
		{
			"fieldname": "start_date",
			"label": "From Date",
			"fieldtype": "Date",
			"default": frappe.datetime.add_days(frappe.datetime.week_start(), 1),
			"reqd": 1
		},
		{
			"fieldname": "end_date",
			"label": "To Date",
			"fieldtype": "Date",
			"default": frappe.datetime.week_end(),
			"reqd": 1
		}
	]
}

