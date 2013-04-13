import webapp2
import dao
import ui
from google.appengine.api import users

class RequestHandler(webapp2.RequestHandler):
    def get(self):
        if not dao.test_current_user_registered():
            webapp2.abort(401)

        # Display the webpage
        self.render()

    def post(self):
        if not dao.test_current_user_registered():
            webapp2.abort(401)

        current_user = users.get_current_user()
        current_email = current_user.email().lower()

        # Attempt to create a new template
        try:
            name = self.request.get("name").strip()
            if not name:
                raise Exception("You must provide a name for your template")
            for template in dao.get_private_templates_by_name(name):
                if dao.test_email_is_template_owner(template, current_email):
                    raise Exception("Sorry, you already own a template by that name")

            # Create the new Project entity
            template = dao.Project(name=name, project_type=dao.PRIVATE_TEMPLATE, description=self.request.get("description"))
            template_key = template.put()

            # Create a ProjectUser entity, making the current user owner of the new template
            dao.ProjectUser(email=dao.get_current_site_user().email, is_owner=True, parent=template_key).put()

            self.redirect("/template?template_id={}".format(template_key.id()))
            return
        except Exception as e:
            error_msg = "Creating template failed: {}".format(e)

        # Display the webpage
        self.render(error_msg)

    def render(self, error_msg=None):
        # Create Jinja template and template values, render the page
        jinja_template = ui.get_template(self, "template_admin/new_template.html")

        jinja_template_values = dao.get_standard_site_values()
        jinja_template_values["error_msg"] = error_msg
        jinja_template_values["name"] = self.request.get("name")
        jinja_template_values["description"] = self.request.get("description")

        self.response.out.write(jinja_template.render(jinja_template_values))