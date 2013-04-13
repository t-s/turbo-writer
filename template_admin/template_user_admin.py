import webapp2
import dao
import ui

class RequestHandler(webapp2.RequestHandler):
    def get(self):
        template = dao.get_template_by_id(self.request.get("template_id"))
        if not dao.test_template_permitted(template): # TODO Test that current user's role includes template-admin permission
            webapp2.abort(401)

        user_list = list()

        for template_user in dao.get_template_users(template):
            if not template_user.is_owner:
                user = dict()
                user["template_user_id"] = template_user.key.id()
                user["email"] = template_user.email
                user_list.append(user)

        # Create template and template values, render the page
        jinja_template = ui.get_template(self, "template_admin/template_user_admin.html")

        jinja_template_values = dao.get_standard_template_values(template)
        jinja_template_values["users"] = user_list

        self.response.out.write(jinja_template.render(jinja_template_values))