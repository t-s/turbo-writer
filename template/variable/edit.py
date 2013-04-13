import webapp2
import dao
import ui
from service.html_generator_service import HtmlGeneratorService

class RequestHandler(webapp2.RequestHandler):
    def get(self):
        template = dao.get_template_by_id(self.request.get("template_id"))
        if not dao.test_template_permitted(template): # TODO Test that current user's role includes template-admin permission
            webapp2.abort(401)

        variable_entity = dao.get_variable_by_id(template, self.request.get("variable_id"))
        error_msg = None if variable_entity else "Unable to access specified variable"

        # Display the webpage
        self.render(template, variable_entity, error_msg)

    def post(self):
        template = dao.get_template_by_id(self.request.get("template_id"))
        if not dao.test_template_permitted(template): # TODO Test that current user's role includes template-admin permission
            webapp2.abort(401)

        variable_entity = dao.get_variable_by_id(template, self.request.get("variable_id"))
        error_msg = None if variable_entity else "Unable to access specified variable"

        # Handle delete request
        if variable_entity and self.request.get("delete"):
            try:
                variable_entity.key.delete()

                html_generator_service = HtmlGeneratorService(template)
                html_generator_service.generate_all_html()

                self.redirect("/template/variable?template_id={}".format(template.key.id()))
                return
            except Exception as e:
                error_msg = "Deleting variable from template failed: {}".format(e)

        # Handle update request
        if variable_entity and self.request.get("update"):
            try:
                variable_entity.description = str(self.request.get("description"))
                variable_entity.is_repeating = (str(self.request.get("type")) == "repeating")
                variable_entity.input_field = (str(self.request.get("input_field")))
                variable_entity.put()

                html_generator_service = HtmlGeneratorService(template)
                html_generator_service.generate_all_html()

                self.redirect("/template/variable?template_id={}".format(template.key.id()))
                return
            except Exception as e:
                error_msg = "Updating variable failed: {}".format(e)

        # Display the webpage
        self.render(template, variable_entity, error_msg)

    def render(self, template, variable_entity, error_msg):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, "template/variable/edit.html")

        jinja_template_values = dao.get_standard_template_values(template)
        jinja_template_values["error_msg"] = error_msg
        jinja_template_values["variable_id"] = variable_entity.key.id()
        jinja_template_values["name"] = variable_entity.name
        jinja_template_values["description"] = variable_entity.description
        jinja_template_values["type"] = "repeating" if variable_entity.is_repeating else "single"
        jinja_template_values["input_field"] = variable_entity.input_field

        self.response.out.write(jinja_template.render(jinja_template_values))