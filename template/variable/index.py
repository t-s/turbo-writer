import webapp2
import dao
import ui

class RequestHandler(webapp2.RequestHandler):
    def get(self):
        template = dao.get_template_by_id(self.request.get("template_id"))
        if not dao.test_template_permitted(
            template): # TODO Test that current user's role includes template-admin permission
            webapp2.abort(401)

        variable_list = list()

        for variable_entity in dao.get_variables(template):
            variable = dict()
            variable["id"] = variable_entity.key.id()
            variable["name"] = variable_entity.name
            variable["is_repeating"] = variable_entity.is_repeating
            variable["input_field"] = variable_entity.input_field
            variable_list.append(variable)

        # Create template and template values, render the page
        jinja_template = ui.get_template(self, "template/variable/index.html")

        jinja_template_values = dao.get_standard_template_values(template)
        jinja_template_values["variables"] = variable_list

        self.response.out.write(jinja_template.render(jinja_template_values))