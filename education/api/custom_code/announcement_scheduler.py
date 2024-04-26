import frappe
from frappe.model.document import Document
from frappe.utils import now

# def all():
#     pass

def scheduler_announcement():
    announcement_list = frappe.db.get_list('Announcement', filters={
        'status': 'Active',
        'announcement_date': ['<', now()]
    })
    
    for announcement in announcement_list:
        frappe.db.set_value('Announcement', announcement.name, 'status','Closed')
        
    frappe.db.commit()
