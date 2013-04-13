import webapp2
import dao
import ui

class RequestHandler(webapp2.RequestHandler):
    def get(self):
        if not dao.test_current_user_registered():
            webapp2.abort(401)

        # Create template and template values, render the page
        jinja_template = ui.get_template(self, "my_account/preferences.html")

        jinja_template_values = dao.get_standard_site_values()
        self.response.out.write(jinja_template.render(jinja_template_values))

    def post(self):
        # Process UI preference
        ui_parameter = self.request.get("ui")
        if ui_parameter:
            self.response.set_cookie("ui", ui_parameter)
        self.redirect("/")
