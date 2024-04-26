# from _future_ import unicode_literals 
import frappe 
from frappe import auth
 
import json 
from frappe.utils import floor, flt, today, cint 
from frappe import _ 
from frappe.core.doctype.user.user import generate_keys 
# @frappe.whitelist(allow_guest=True) # 
#def sign_up(email: str, full_name: str, redirect_to: str) -> tuple[int, str]: 
##def fun(email,password): # login(email,password) 


@frappe.whitelist(allow_guest=True) 
def login(email,password): 
    try:
        login_manager = frappe.auth.LoginManager() 
        login_manager.authenticate(user=email, pwd=password) 
        login_manager.post_login()
        api_generate = generate_keys(email) 
        user1 = frappe.get_doc('User',email) 
        frappe.db.set_value('User', email, 'api_key', api_generate[1]) 
        frappe.db.set_value('User', email, 'api_secret', api_generate[0]) 
        frappe.db.commit() 
        token = "token "+str(user1.api_key)+":"+str(api_generate[0]) 
        user = frappe.get_doc('User',email) 
        frappe.local.response["message"] = { "success_key": 1, "data": { "user":email, "Role": user.role_profile_name, "type":"Logged In", "token":token, "sid": frappe.session.sid, "system_user":"yes" }} 
    except frappe.exceptions.AuthenticationError:
        frappe.local.response["message"] = { 
                    "success_key": 0, 
                    "error": { "message": "Invalid Credentials, Authentication Failed" } 
                        
            } 

@frappe.whitelist(allow_guest=True) 
def generate_keys(user): 
    user_details = frappe.get_doc("User",user) 
    api_secret = frappe.generate_hash(length=15) 
    if not user_details.api_key: 
        api_key = frappe.generate_hash(length=15) 
        user_details.api_key = api_key 
    else: 
        api_key = user_details.api_key 
        user_details.api_key = api_key 
        user_details.api_secret = api_secret 
        user_details.save() 
    return [api_secret,api_key]