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
        css = self.request.get("css")

        if not name:
            error_msg = "You must specify a name for your style definition"
        else:
            style_entity = dao.get_style_by_name(template, name)
            if style_entity:
                error_msg = "Adding style failed: Duplicate style name in template"
            else:
                try:
                    dao.Style(name=str(name), description=str(description),css=str(css), parent=template.key).put()

                    html_generator_service = HtmlGeneratorService(template)
                    html_generator_service.generate_all_html()

                    self.redirect("/template/style?template_id={}".format(template.key.id()))
                    return
                except Exception as e:
                    error_msg = "Adding style failed: {}".format(e)

        # Display the webpage
        self.render(template, error_msg)

    def render(self, template, error_msg=None):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, "template/style/add.html")

        jinja_template_values = dao.get_standard_template_values(template)
        jinja_template_values["error_msg"] = error_msg
        jinja_template_values["name"] = self.request.get("name")
        jinja_template_values["description"] = self.request.get("description")
        jinja_template_values["css"] = self.request.get("css")

        self.response.out.write(jinja_template.render(jinja_template_values))