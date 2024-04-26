import frappe

@frappe.whitelist(allow_guest=True)
def event(limit_start, limit_length):
    try:
        events = frappe.db.get_list("School Event", fields=["name", "status", "start_date","end_date", "message"], order_by="start_date desc", start=limit_start, page_length=limit_length)

        event_data = []
        for event in events:
            eventName = event.name
            attachments = frappe.get_all("File",
                           filters={"attached_to_doctype": "School Event", "attached_to_name": eventName},
                           fields=["file_url", "file_name", "file_size"])
            attachment_data = [{"file_name": attachment["file_name"], "file_url": attachment["file_url"]} for attachment in attachments]    
            event_data.append({
                    "event_name": eventName,
                    "status": event.status,
                    "start_date": event.start_date,
                    "end_date": event.end_date,
                    "message": event.message,
                    "attachments": attachment_data
                    })

        return event_data

    except Exception as e:
        frappe.msgprint(_("Error: {0}".format(e), raise_exception=True))    


