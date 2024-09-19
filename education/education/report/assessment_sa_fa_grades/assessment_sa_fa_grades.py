# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from education.education.report.course_wise_assessment_report.course_wise_assessment_report import get_formatted_result
from frappe.utils.pdf import get_pdf

def execute(filters=None):
    columns, data = [], []

    data, course_list = get_data(filters)
    columns = get_column(course_list)
    chart = get_chart(data, course_list)

    return columns, data, None, chart

def get_data(filters):
    data = []
    args = frappe._dict()
    args["academic_year"] = filters.get("academic_year")
    args["assessment_group"] = filters.get("assessment_group")

    args.students = frappe.get_all(
        "Student Group Student", {"parent": filters.get("student_group")}, pluck="student"
    )

    values = get_formatted_result(args, get_course=True)
    assessment_result = values.get("assessment_result")
    course_list = values.get("courses")

    for result in assessment_result:
        exists = [i for i, d in enumerate(data) if d.get("student") == result.student]
        if not len(exists):
            row = frappe._dict()
            row.student = result.student
            row.student_name = result.student_name
            row.assessment_group = result.assessment_group
            row["grade_" + frappe.scrub(result.course)] = result.grade
            row["score_" + frappe.scrub(result.course)] = result.total_score
            row["total_score"] = result.total_score

            data.append(row)
        else:
            index = exists[0]
            data[index]["grade_" + frappe.scrub(result.course)] = result.grade
            data[index]["score_" + frappe.scrub(result.course)] = result.total_score
            data[index]["total_score"] += result.total_score

    # Calculate total score per student after aggregating course scores
    for row in data:
        row["total_score"] = sum(
            row.get("score_" + frappe.scrub(course), 0) for course in course_list
        )

    return data, course_list

def get_column(course_list):
    columns = [
        {
            "fieldname": "student",
            "label": _("Student ID"),
            "fieldtype": "Link",
            "options": "Student",
            "width": 150,
        },
        {
            "fieldname": "student_name",
            "label": _("Student Name"),
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "fieldname": "assessment_group",
            "label": _("Assessment Group"),
            "fieldtype": "Link",
            "options": "Assessment Group",
            "width": 100,
        },
    ]
    for course in course_list:
        columns.append(
            {
                "fieldname": "grade_" + frappe.scrub(course),
                "label": course,
                "fieldtype": "Data",
                "width": 100,
            }
        )
        columns.append(
            {
                "fieldname": "score_" + frappe.scrub(course),
                "label": "Score (" + course + ")",
                "fieldtype": "Float",
                "width": 150,
            }
        )

    # Add the Total Score column at the end
    columns.append(
        {
            "fieldname": "total_score",
            "label": _("Total Score"),
            "fieldtype": "Float",
            "width": 150,
        }
    )

    return columns

def get_chart(data, course_list):
    dataset = []
    students = [row.student_name for row in data]

    for course in course_list:
        dataset_row = {"values": []}
        dataset_row["name"] = course
        for row in data:
            if "score_" + frappe.scrub(course) in row:
                dataset_row["values"].append(row["score_" + frappe.scrub(course)])
            else:
                dataset_row["values"].append(0)

        dataset.append(dataset_row)

    charts = {
        "data": {"labels": students, "datasets": dataset},
        "type": "bar",
        "colors": ["#ff0e0e", "#ff9966", "#ffcc00", "#99cc33", "#339900"],
    }

    return charts

@frappe.whitelist(allow_guest=True)
def generate_consolidated_report(filters=None):
    if isinstance(filters, str):
        filters = frappe.parse_json(filters)
    data, course_list = get_data(filters)

    consolidated_content = generate_consolidated_report_content(data, course_list,filters)
    pdf = get_pdf(consolidated_content)

    file_name = "Generate_Student_Report.pdf"
    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": file_name,
        "attached_to_doctype": "Student Group",
        "attached_to_name": filters.get('student_group'),
        "content": pdf,
        "is_private": 1
    })
    file_doc.save()

    return file_doc.file_url

def generate_consolidated_report_content(data, course_list, filters):
    # Fetch additional details for header information
    academic_year = frappe.db.get_value("Academic Year", filters.get("academic_year"), "academic_year_name")
    assessment_group = frappe.db.get_value("Assessment Group", filters.get("assessment_group"), "assessment_group_name")
    
    student_group = frappe.db.get_value("Student Group", filters.get("student_group"), "student_group_name")
   
    
    # Retrieve the list of assessment groups where the parent assessment group matches the one we retrieved
    parent_assessment_groups = frappe.get_list(
        "Assessment Group",
        filters={"parent_assessment_group": assessment_group},
        fields=["name", "assessment_group_name", "parent_assessment_group"]
    )

    content = ""

    for idx, student in enumerate(data, start=1):
        # Add the title for each student's report
        content += "<h1 style='text-align: center;'>Final Assessment Report</h1>"

        content += """
        <div style='width:100%; overflow:hidden;'>
            <div style='float:left;'>
               <strong style='font-size: 18px;'>Student Name:</strong> {student_name}
            </div>
            <div style='float:right; text-align:right;'>
             <strong style='font-size: 18px;' >Academic Year:</strong> {academic_year}
            </div>
        </div>
        """.format(student_name=student['student_name'], academic_year=academic_year)

        content += """
        <div style='width:100%; overflow:hidden;'>
            <div style='float:left;'>
              <strong style='font-size: 18px;'>Student ID:</strong> {student_id}
            </div>
            <div style='float:right; text-align:right;'>
             <strong style='font-size: 18px;'>Assessment Group:</strong> {assessment_group}
            </div>
        </div>
        """.format(student_id=student['student'], assessment_group=assessment_group)
        content += """
        <div style='width:100%; overflow:hidden;'>
            <div style='float:left;'>
              <strong style='font-size: 18px;'>Class:</strong> {student_group}          
            </div>
           
        </div>
        """.format( student_group=student_group)
 
      

        content += "<table border='1' cellspacing='0' cellpadding='5' style='width:100%; border-collapse: collapse;'>"
        content += "<tr style='background-color: #ffcccc;'>"
        content += "<th height='40'>Subject</th>"
        overall_header_added = False

        # Loop through assessment groups to add dynamic headers
        for group in parent_assessment_groups:
            group_name = group['name']
            content += f"<th height='40'>{group_name} </th>"
            
            # Add 'Overall' header only once
        if not overall_header_added:
            content += f"<th height='40'>Overall</th>"
            overall_header_added = True
                
            content += "</tr>"

        # Populate the table with courses and scores
        for course in course_list:
            content += f"<tr><td height='40'>{course}</td>"
            grade = student.get(f"grade_{frappe.scrub(course)}_{frappe.scrub(group_name)}", "")
            total_scores = []

        

            for group in parent_assessment_groups:
                total_score = frappe.db.get_value("Assessment Result", {
                    "student": student['student'],
                    "course": course,
                    "assessment_group": group['name'],
                    "academic_year": filters.get("academic_year"),
                    "student_group": filters.get("student_group")
                }, "total_score") or ""
                
                grade = frappe.db.get_value("Assessment Result", {
                    "student": student['student'],
                    "course": course,
                    "assessment_group": group['name'],
                    "academic_year": filters.get("academic_year"),
                    "student_group": filters.get("student_group")
                }, "grade") or "-"
                total_scores.append(float(total_score) if total_score else 0)

                content += f"<td height='40'>{grade}</td>"
                overall_score = sum(total_scores)
                overall_grade = get_grade_from_score(overall_score)
            # Add overall score
         
            content += f"<td>{overall_grade}</td>"

            content += "</tr>"

        content += "</table>"
        content += """
       <div style='position: relative; min-height: 100px;'>
       <div style='display: flex; justify-content: space-between; align-items: flex-end; width:100%; margin-top: 50px;'>
       <div style='flex: 1; text-align: left; margin-right: 20px;'> 
            <strong>FA Grading</strong> 
            <table border='1' cellspacing='0' cellpadding='5' style='width:100%; border-collapse: collapse;'>
            <tr style='background-color: #ffcccc;'>
                <th height='40'>Marks</th><th height='40'>Grades</th>
            </tr>
            <tr><td height='40'>37-40</td><td height='40'>A1</td></tr>
            <tr><td height='40'>33-36</td><td height='40'>A2</td></tr>
            <tr><td height='40'>29-32</td><td height='40'>B1</td></tr>
            <tr><td height='40'>25-28</td><td height='40'>B2</td></tr>
            <tr><td height='40'>21-24</td><td height='40'>C1</td></tr>
            <tr><td height='40'>17-20</td><td height='40'>C2</td></tr>
            <tr><td height='40'>13-16</td><td height='40'>D</td></tr>
            <tr><td height='40'>9-12</td><td height='40'>E1</td></tr>
            <tr><td height='40'>8 & Below</td><td height='40'>E2</td></tr>
            </table><br>
        </div>
        <div style='flex: 1; text-align: center; margin-right: 20px;'> 
            <strong>SA Grading</strong> 
            <table border='1' cellspacing='0' cellpadding='5' style='width:100%; border-collapse: collapse;'>
            <tr style='background-color: #ffcccc;'>
                <th height='40'>Marks</th><th height='40'>Grades</th>
            </tr>
            <tr><td height='40'>55-60</td><td height='40'>A1</td></tr>
            <tr><td height='40'>49-54</td><td height='40'>A2</td></tr>
            <tr><td height='40'>43-48</td><td height='40'>B1</td></tr>
            <tr><td height='40'>37-42</td><td height='40'>B2</td></tr>
            <tr><td height='40'>31-36</td><td height='40'>C1</td></tr>
            <tr><td height='40'>25-30</td><td height='40'>C2</td></tr>
            <tr><td height='40'>19-24</td><td height='40'>D</td></tr>
            <tr><td height='40'>13-18</td><td height='40'>E1</td></tr>
            <tr><td height='40'>12 & Below</td><td height='40'>E2</td></tr>
            </table><br>
        </div>
        <div style='flex: 1; text-align: right; '> 
            <strong>Overall Grading</strong> 
            <table border='1' cellspacing='0' cellpadding='5' style='width:100%; border-collapse: collapse;'>
            <tr style='background-color: #ffcccc;'>
                <th height='40'>Marks</th><th height='40'>Grades</th>
            </tr>
            <tr><td height='40'>91-100</td><td height='40'>A1</td></tr>
            <tr><td height='40'>81-90</td><td height='40'>A2</td></tr>
            <tr><td height='40'>71-80</td><td height='40'>B1</td></tr>
            <tr><td height='40'>61-70</td><td height='40'>B2</td></tr>
            <tr><td height='40'>51-60</td><td height='40'>C1</td></tr>
            <tr><td height='40'>41-50</td><td height='40'>C2</td></tr>
            <tr><td height='40'>33-40</td><td height='40'>D</td></tr>
            <tr><td height='40'>21-32</td><td height='40'>E1</td></tr>
            <tr><td height='40'>20 & Below</td><td height='40'>E2</td></tr>
            </table><br>
        </div>
    </div>
</div>
        """

        content += "<table border='1' cellspacing='0' cellpadding='5' style='width:100%; border-collapse: collapse;'>"
        content += "<tr style='background-color: #ffcccc;'>"
        content += "<th height='40'>Attendance</th><th height='40'>Height</th><th height='40'>Weight</th>"
        content += "</tr>" 

        content += f"<tr><td height='50'></td><td height='50'></td><td height='50'></td></tr>"

        content += "</table><br>"       
                                          


        content += """
        <div style='position: relative; min-height: 100px;'>
            <div style='display: flex; justify-content: space-between; align-items: flex-end; width:100%; margin-top: 50px;'>
                <div style='flex: 1; text-align: left;'>
                   <strong>Teacher:</strong> .......................
                </div>
                <div style='flex: 1; text-align: center;'>
                 <strong>Parent:</strong> .........................
                </div>
                <div style='flex: 1; text-align: right;'>
                 <strong>Principal:</strong> .........................
                </div>
            </div>
        </div>
        """

        # Add a page break after each student's report
        content += "<div style='page-break-after: always;'></div>"

    return content

def get_grade_from_score(score):
    # Grading logic based on the provided grading table
    if 91 <= score <= 100:
        return 'A1'
    elif 81 <= score <= 90:
        return 'A2'
    elif 71 <= score <= 80:
        return 'B1'
    elif 61 <= score <= 70:
        return 'B2'
    elif 51 <= score <= 60:
        return 'C1'
    elif 41 <= score <= 50:
        return 'C2'
    elif 33 <= score <= 40:
        return 'D'
    elif 21 <= score <= 32:
        return 'E1'
    elif score <= 20:
        return 'E2'
    else:
        return ''