import frappe


@frappe.whitelist(allow_guest=True)
def is_session_valid():
    try:
        user = frappe.session.user
        if user == "Guest":
            return False  # Session invalid
        return True  # Session valid
    except Exception:
        return False  # Any error means session invalid
     

     