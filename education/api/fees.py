import frappe

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