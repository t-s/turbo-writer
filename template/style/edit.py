import webapp2
import dao
import ui
from service.html_generator_service import HtmlGeneratorService

class RequestHandler(webapp2.RequestHandler):
    def get(self):
        template = dao.get_template_by_id(self.request.get("template_id"))
        if not dao.test_template_permitted(template): # TODO Test that current user's role includes template-admin permission
            webapp2.abort(401)

        style_entity = dao.get_style_by_id(template, self.request.get("style_id"))
        error_msg = None if style_entity else "Unable to access specified style"

        # Display the webpage
        self.render(template, style_entity, error_msg)

    def post(self):
        template = dao.get_template_by_id(self.request.get("template_id"))
        if not dao.test_template_permitted(template): # TODO Test that current user's role includes template-admin permission
            webapp2.abort(401)

        style_entity = dao.get_style_by_id(template, self.request.get("style_id"))
        error_msg = None if style_entity else "Unable to access specified style"

        # Handle delete request
        if style_entity and self.request.get("delete"):
            try:
                style_entity.key.delete()

                html_generator_service = HtmlGeneratorService(template)
                html_generator_service.generate_all_html()

                self.redirect("/template/style?template_id={}".format(template.key.id()))
                return
            except Exception as e:
                error_msg = "Deleting style from template failed: {}".format(e)

        # Handle update request
        if style_entity and self.request.get("update"):
            try:
                style_entity.description = str(self.request.get("description"))
                style_entity.css = str(self.request.get("css"))
                style_entity.put()

                html_generator_service = HtmlGeneratorService(template)
                html_generator_service.generate_all_html()

                self.redirect("/template/style?template_id={}".format(template.key.id()))
                return
            except Exception as e:
                error_msg = "Updating style failed: {}".format(e)

        # Display the webpage
        self.render(template, style_entity, error_msg)

    def render(self, template, style_entity, error_msg):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, "template/style/edit.html")

        jinja_template_values = dao.get_standard_template_values(template)
        jinja_template_values["error_msg"] = error_msg
        jinja_template_values["style_id"] = style_entity.key.id()
        jinja_template_values["name"] = style_entity.name
        jinja_template_values["description"] = style_entity.description
        jinja_template_values["css"] = style_entity.css

        self.response.out.write(jinja_template.render(jinja_template_values))