import os
import jinja2
import dao

def get_indexed_variable(project, variable_name, index):
    return dao.get_indexed_variable(project, variable_name, index)

class UIService():
    def __init__(self, request_handler):
        self.request_handler = request_handler

    def from_string(self, template):
        ui = self.request_handler.request.cookies.get("ui")
        if not ui:
            ui = "turbo"
        jinja_environment = jinja2.Environment(
            loader=jinja2.FileSystemLoader(os.path.dirname(os.path.dirname(__file__)) + "/ui/{}".format(ui)))
        jinja_environment.globals["get_indexed_variable"] = get_indexed_variable
        jinja_environment.globals["ui"] = ui
        return jinja_environment.from_string(template)

    def get_template(self, relative_name):
        ui = self.request_handler.request.cookies.get("ui")
        if not ui:
            ui = "turbo"
        jinja_environment = jinja2.Environment(
            loader=jinja2.FileSystemLoader(os.path.dirname(os.path.dirname(__file__)) + "/ui/{}".format(ui)))
        jinja_environment.globals["get_indexed_variable"] = get_indexed_variable
        jinja_environment.globals["ui"] = ui
        return jinja_environment.get_template(relative_name)
