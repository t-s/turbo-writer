import webapp2
import dao
import ui
from service.html_generator_service import HtmlGeneratorService

class RequestHandler(webapp2.RequestHandler):
    def get(self):
        template = dao.get_template_by_id(self.request.get("template_id"))
        if not dao.test_template_permitted(
            template): # TODO Test that current user's role includes template-admin permission
            webapp2.abort(401)

        # Display the webpage
        self.render(template)

    def post(self):
        template = dao.get_template_by_id(self.request.get("template_id"))
        if not dao.test_template_permitted(
            template): # TODO Test that current user's role includes template-admin permission
            webapp2.abort(401)

        name = self.request.get("name")
        description = self.request.get("description")
        variable_type = self.request.get("type")

        if not name:
            error_msg = "You must specify a name for your assignment definition"
        elif not variable_type:
            error_msg = "You must specify whether this is a single or repeating variable"
        else:
            assignment_entity = dao.get_assignment_by_name(template, name)
            if assignment_entity:
                error_msg = "Adding assignment failed: Duplicate assignment name in template"
            else:
                try:
                    assignment_entity = dao.Assignment(name=str(name), description=str(description), is_repeating=(variable_type == "repeating"),
                        parent=template.key)
                    assignment_entity.put()

                    html_generator_service = HtmlGeneratorService(template)
                    html_generator_service.generate_interview_html(assignment_entity)

                    self.redirect("/template/assignment?template_id={}".format(template.key.id()))
                    return
                except Exception as e:
                    error_msg = "Adding assignment failed: {}".format(e)

        # Display the webpage
        self.render(template, error_msg)

    def render(self, template, error_msg=None):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, "template/assignment/add.html")

        jinja_template_values = dao.get_standard_template_values(template)
        jinja_template_values["error_msg"] = error_msg
        jinja_template_values["name"] = self.request.get("name")
        jinja_template_values["description"] = self.request.get("description")
        jinja_template_values["type"] = self.request.get("type")

        self.response.out.write(jinja_template.render(jinja_template_values))