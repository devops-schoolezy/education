import json
from erpnext.accounts.doctype.account.account import get_account_currency
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions
from erpnext.accounts.party import get_party_account
import frappe
from erpnext.accounts.doctype.payment_request.payment_request import \
    make_payment_entry
from frappe.utils import get_url
from frappe.utils.data import nowdate
from payments.utils import get_payment_gateway_controller
# from razorpay_integration.api import get_razorpay_checkout_url

from erpnext.accounts.doctype.payment_entry.payment_entry import (
	InvalidPaymentEntry,
	get_company_defaults,
	get_payment_entry,
	get_reference_details,
)

	
frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("schoolezy_raz_payment", allow_site=True, file_count=10)

controller = get_payment_gateway_controller("Razorpay")

@frappe.whitelist(allow_guest=True)
def make_payment(doctype, docname):

	logger.debug(f"docname = {docname}")
	student_fees_ref_doc = frappe.get_doc(doctype, docname)
    
	# make order
	payment_request = frappe.get_doc(dict({
		'doctype': 'Payment Request',
		'payment_request_type': 'Inward',
		'party_type': 'Student',
		'party': student_fees_ref_doc.student,
		'reference_doctype': doctype,
		'reference_name': student_fees_ref_doc.name,
		'grand_total': student_fees_ref_doc.outstanding_amount,
		'currency': 'INR'
	})).insert(ignore_permissions=True)
	
	student_details = frappe.db.get_value("Student", student_fees_ref_doc.student, ["student_mobile_number", "student_email_id"], as_dict=1)
	contact = student_details.student_mobile_number
	email = student_details.student_email_id
	#Add +91 to existing contact. else razorpay will not open with prefill data
	# if contact is None:
	# 	contact = '+919999999999'
	# else:
	# 	contact = "+91" + contact
	# if email is None:
	# 	email = 'razorpay@schoolezy.in'

	logger.debug(f"contact = {contact}")
	logger.debug(f"email = {email}")
	redirect_url = get_url(f"./app/fees/{student_fees_ref_doc.name}")
	logger.debug(f"redirect_url = {redirect_url}")

	payment_details = {
		"key_id": frappe.db.get_single_value("Razorpay Settings", "api_key"),
		"name": frappe.db.get_single_value("Website Settings", "app_name"),
		"amount": student_fees_ref_doc.outstanding_amount,
		"title": ("Fee Payment for {0}").format(student_fees_ref_doc.student_name),
		"description": ("Payment for {0}").format(student_fees_ref_doc.student),
		"reference_doctype": doctype,
		"reference_docname": student_fees_ref_doc.name,
		"payer_email": email,
		"payer_name": student_fees_ref_doc.student_name,
		"order_id": payment_request.name,
		"currency": "INR",
		"redirect_to":redirect_url,
		"payment_gateway": "Razorpay",
		"prefill": {
			"name": student_fees_ref_doc.student_name,
			"email": email,
			"contact": contact,
		},
	}

	# Redirect the user to this url
	url = controller.get_payment_url(**payment_details)
	logger.debug(f"url1 = {url}")
	return url

def on_payment_authorized(self, status):
	logger.debug("on_payment_authorized called")
	integration_request = frappe.get_all(
							"Integration Request",
							filters={"status": "Authorized", "integration_request_service": "Razorpay", 
										"reference_docname": self.name},
							fields=["name", "data"],
							order_by='creation desc'
						)
	data = frappe._dict(json.loads(integration_request[0].data))
	logger.debug(f"Payment ID = {data.razorpay_payment_id}")
	logger.debug(f"order ID = {data.order_id}")

	payment_req_doc = frappe.get_doc('Payment Request', data.order_id, ignore_permissions=True)
	payment_req_doc.submit()
	payment_entry = create_payment_entry_against_fees(payment_req_doc, data, submit=True)

	logger.debug(f"All done.......{payment_entry.name}")
	pass

def create_payment_entry_against_fees(doc, gateway_data, submit=True):
	"""create entry"""
	frappe.flags.ignore_account_permission = True

	ref_doc = frappe.get_doc(doc.reference_doctype, doc.reference_name)
	
	party_account = get_party_account("Customer", ref_doc.get("customer"), ref_doc.company)

	party_account_currency = ref_doc.get("party_account_currency") or get_account_currency(
		party_account
	)

	bank_amount = doc.grand_total
	if (
		party_account_currency == ref_doc.company_currency and party_account_currency != doc.currency
	):
		party_amount = ref_doc.get("base_rounded_total") or ref_doc.get("base_grand_total")
	else:
		party_amount = doc.grand_total

	payment_entry = get_payment_entry(
		doc.reference_doctype,
		doc.reference_name,
		party_amount=party_amount,
		bank_account=doc.payment_account,
		bank_amount=bank_amount,
		party_type='Student',
		payment_type='Receive',
		reference_date=nowdate()
	)

	payment_entry.update(
		{
			"mode_of_payment": doc.mode_of_payment,
			"reference_no": gateway_data.razorpay_payment_id,
			"reference_date": nowdate(),
			"remarks": "Payment Entry against Fees {0} via Payment Request {1}. Razorpay Order ID is {2} and Payment ID is {3}".format(
				 doc.reference_name, doc.name, gateway_data.order_id, gateway_data.razorpay_payment_id
			),
		}
	)
	
	# Update dimensions
	payment_entry.update(
		{
			"cost_center": doc.get("cost_center"),
			"project": doc.get("project"),
		}
	)
	
	for dimension in get_accounting_dimensions():
		payment_entry.update({dimension: doc.get(dimension)})

	if payment_entry.difference_amount:
		company_details = get_company_defaults(ref_doc.company)

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
	else:
		payment_entry.insert(ignore_permissions=True)

	return payment_entry
