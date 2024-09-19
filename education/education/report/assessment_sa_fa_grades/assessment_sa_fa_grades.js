// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Assessment SA-FA Grades"] = {
	"filters": [
		{
			"fieldname": "academic_year",
			"label": __("Academic Year"),
			"fieldtype": "Link",
			"options": "Academic Year",
			"reqd": 1
		},
		{
			"fieldname": "student_group",
			"label": __("Student Group"),
			"fieldtype": "Link",
			"options": "Student Group",
			"reqd": 1,
			"get_query": function () {
				return {
					filters: {
						"group_based_on": "Batch",
						"academic_year": frappe.query_report.get_filter_value('academic_year')
					}
				};
			}
		},
		{
			"fieldname": "assessment_group",
			"label": __("Assessment Group"),
			"fieldtype": "Link",
			"options": "Assessment Group",
			"reqd": 1
		}
	],
	"onload": function (report) {
        report.page.add_inner_button(__('Generate Pdf'), function () {
            let filters = report.get_values();
            frappe.call({
                method: "education.education.report.assessment_sa_fa_grades.assessment_sa_fa_grades.generate_consolidated_report",
                args: {
                    filters: filters
                },
                callback: function (r) {
                    if (r.message) {
                        window.open(r.message);
                    } else {
                        frappe.msgprint({
                            message: __("No report was generated."),
                            title: __("Info"),
                            indicator: "blue"
                        });
                    }
                },
                error: function (r) {
                    frappe.msgprint({
                        message: __("An error occurred: ") + r.responseText,
                        title: __("Error"),
                        indicator: "red"
                    });
                }
            });
        });
    }
};
