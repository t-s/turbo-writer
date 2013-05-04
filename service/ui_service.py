import os
import jinja2
import dao

enterprise_logo = os.environ[u'ENTERPRISE_LOGO'] if u'ENTERPRISE_LOGO' in os.environ.keys() else None


def get_indexed_variable(project, variable_name, index):
    return dao.get_indexed_variable(project, variable_name, index)


class UIService():
    def __init__(self, request_handler):
        self.request_handler = request_handler

    def from_string(self, template):
        ui = self.request_handler.request.cookies.get(u'ui')
        if not ui:
            ui = u'turbo'
        jinja_environment = jinja2.Environment(
            loader=jinja2.FileSystemLoader(os.path.dirname(os.path.dirname(__file__)) + u'/ui/{}'.format(ui)))
        jinja_environment.globals[u'get_indexed_variable'] = get_indexed_variable
        jinja_environment.globals[u'ui'] = ui
        if enterprise_logo:
            jinja_environment.globals[u'enterprise_logo'] = enterprise_logo
        return jinja_environment.from_string(template)

    def get_template(self, relative_name):
        ui = self.request_handler.request.cookies.get(u'ui')
        if not ui:
            ui = u'turbo'
        jinja_environment = jinja2.Environment(
            loader=jinja2.FileSystemLoader(os.path.dirname(os.path.dirname(__file__)) + u'/ui/{}'.format(ui)))
        jinja_environment.globals[u'get_indexed_variable'] = get_indexed_variable
        jinja_environment.globals[u'ui'] = ui
        if enterprise_logo:
            jinja_environment.globals[u'enterprise_logo'] = enterprise_logo
        return jinja_environment.get_template(relative_name)
