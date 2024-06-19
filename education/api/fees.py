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