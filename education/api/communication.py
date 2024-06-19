import frappe

@frappe.whitelist(allow_guest=True)
def mycommunication(reference_name):
    try:
        communications = frappe.db.sql("""
                                    select content, communication_date, sender_full_name 
                                    from 
                                    `tabCommunication` 
                                    where 
                                    reference_name = %s
                                """, 
                                (reference_name),
                                    as_dict=1,
                                )

        return communications

    except Exception as e:
        frappe.msgprint(_("Error: {0}".format(e), raise_exception=True))    


