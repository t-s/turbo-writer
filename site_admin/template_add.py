import webapp2
import dao
import ui

class RequestHandler(webapp2.RequestHandler):
    def get(self):
        if not dao.test_permission(dao.SITEPERMISSION_ADMINTEMPLATES):
            webapp2.abort(401)

        # Display the webpage
        self.render()

    def post(self):
        if not dao.test_permission(dao.SITEPERMISSION_ADMINTEMPLATES):
            webapp2.abort(401)

        # Attempt to add a new Template entity
        try:
            name = self.request.get("name")
            if not name:
                raise Exception("You must provide a name for the template")
            description = self.request.get("description")
            if not description:
                raise Exception("You must provide a description for the template")
            if dao.get_public_templates_by_name(name):
                raise Exception("That template name is already taken")
            dao.Project(name=name, type=dao.PUBLIC_TEMPLATE, description=description).put()
            self.redirect("/site_admin/template_admin")
            return
        except Exception as e:
            error_msg = "Adding template to Template Gallery failed: {}".format(e)

        # Display the webpage
        self.render(error_msg)

    def render(self, error_msg=None):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, "site_admin/template_add.html")

        jinja_template_values = dao.get_standard_site_values()
        jinja_template_values["error_msg"] = error_msg
        jinja_template_values["name"] = self.request.get("name")
        jinja_template_values["description"] = self.request.get("description")

        self.response.out.write(jinja_template.render(jinja_template_values))