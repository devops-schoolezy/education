from erpnext.accounts.doctype.process_payment_reconciliation.process_payment_reconciliation import trigger_job_for_doc, trigger_reconciliation_for_queued_docs
import frappe
from education.education.api import get_current_enrollment
from erpnext.accounts.doctype.payment_entry.payment_entry import (
    get_company_defaults,
    get_payment_entry,
)
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
)
from erpnext.accounts.party import get_party_account, get_party_bank_account
from erpnext.accounts.utils import get_account_currency
from frappe.utils.data import nowdate

# frappe.utils.logger.set_log_level("DEBUG")
# logger = frappe.logger("fees", allow_site=True, file_count=10)

@frappe.whitelist()
def get_components(fees_id):
    data = frappe.db.sql("""
    SELECT
        fees_category,
        description,
        amount
    FROM `tabFee Component` fc
    WHERE fc.parent = %s order by fc.idx
    """, fees_id, as_dict=1)

    return data

# @frappe.whitelist()
def create_payment_entry_against_fees(doc, submit=True):
    if doc.include_payment == 0 and not doc.custom_mode_of_payment and not doc.custom_payment_reference:
        return

    """create entry"""
    frappe.flags.ignore_account_permission = True

    # doc = frappe.get_doc(doc.reference_doctype, doc.reference_name)
    
    # party_account = get_party_account("Customer", doc.get("customer"), doc.company)

    # party_account_currency = doc.get("party_account_currency") or get_account_currency(
    #     party_account
    # )

    # bank_amount = doc.grand_total
    # party_amount = doc.grand_total

    payment_entry = get_payment_entry(
        'Fees',
        doc.name,
        # party_amount=party_amount,
        # bank_account=doc.payment_account,
        # bank_amount=bank_amount,
        party_type='Student',
        payment_type='Receive',
        reference_date=nowdate()
    )
    # logger.debug(payment_entry)
    if not doc.custom_payment_reference_date:
      doc.custom_payment_reference_date = nowdate()

    payment_entry.update(
        {
            "mode_of_payment": doc.custom_mode_of_payment,
            "reference_no": doc.custom_payment_reference,
            "reference_date": doc.custom_payment_reference_date,
            "remarks": "Payment Entry against Fees {0}".format(doc.name),
        }
    )
    
    # Update dimensions
    payment_entry.update(
        {
            "cost_center": doc.get("cost_center"),
        }
    )
    
    for dimension in get_accounting_dimensions():
        payment_entry.update({dimension: doc.get(dimension)})

    if payment_entry.difference_amount:
        company_details = get_company_defaults(doc.company)

        payment_entry.append(
            "deductions",
            {
                "account": company_details.exchange_gain_loss_account,
                "cost_center": company_details.cost_center,
                "amount": payment_entry.difference_amount,
            },
        )
    
    if submit:
        payment_entry.insert(ignore_permissions=True)
        payment_entry.submit()
        # logger.debug("done.....")
    else:
        payment_entry.insert(ignore_permissions=True)

    return payment_entry

# call this via hook on before_validate
# to add program enrollment details while creating fees.
# @frappe.whitelist()
def add_program_enrollment(doc, method):
    # logger.debug(doc.student)
    # logger.debug(doc.program_enrollment)
    if not doc.program_enrollment and doc.student:    
        program_enrollment = get_current_enrollment(doc.student)
        # logger.debug(program_enrollment)
        if program_enrollment:
            doc.program_enrollment = program_enrollment.program_enrollment
            if not doc.academic_year:
                doc.academic_year = program_enrollment.academic_year
            if not doc.program:
                doc.program = program_enrollment.program
            if not doc.student_name:
                doc.student_name = program_enrollment.student_name
        else:
            frappe.throw("Program Enrollment not found for the student: {}".format(doc.student))

# @frappe.whitelist()
def payment_reconcile(doc, method):
    # Create a new Process Payment Reconciliation document
    reconciliation = frappe.get_doc({
        "doctype": "Process Payment Reconciliation",
        "company": doc.company,
        "party_type": doc.party_type,
        "party": doc.party,
        "receivable_payable_account": doc.paid_from
    })

    # Add references to the Fees linked with this payment entry
    # for reference in doc.references:
    #     if reference.reference_doctype == "Fees":
    #         reconciliation.append("references", {
    #             "reference_doctype": reference.reference_doctype,
    #             "reference_name": reference.reference_name,
    #             "allocated_amount": reference.allocated_amount,
    #         })

    # Save the document
    reconciliation.insert(ignore_permissions=True)
    reconciliation.submit()
    # frappe.db.commit()

    #trigger the job in background
    trigger_reconciliation_for_queued_docs()
    # trigger_job_for_doc(reconciliation)
    # return
    # pass



@frappe.whitelist()
def calculate_fees_summary_per_class():
    fees_summary = {}

    # Fetch all Fees records
    fees_records = frappe.get_all("Fees", fields=["name", "program", "grand_total"])

    for record in fees_records:
        class_name = record.program  # Replace with the actual field name
        grand_total = record.grand_total

        if class_name not in fees_summary:
            fees_summary[class_name] = {
                "total_fees_charged": 0,
                "total_fees_received": 0
            }

        # Add to total fees charged
        fees_summary[class_name]["total_fees_charged"] += grand_total

        # Fetch all Payment Entries linked to this fee
        payment_entries = frappe.get_all("Payment Entry Reference", 
                                         filters={"reference_name": record.name},
                                         fields=["allocated_amount"])

        # Add up all part payments received
        for payment in payment_entries:
            fees_summary[class_name]["total_fees_received"] += payment.allocated_amount

    return fees_summary

