from service.ui_service import UIService

# USER INTERFACE

def from_string(request_handler, template):
    ui_service = UIService(request_handler)
    return ui_service.from_string(template)

def get_template(request_handler, relative_name):
    ui_service = UIService(request_handler)
    return ui_service.get_template(relative_name)
