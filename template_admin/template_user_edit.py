import webapp2
import dao
import ui

class RequestHandler(webapp2.RequestHandler):
    def get(self):
        template = dao.get_template_by_id(self.request.get("template_id"))
        if not dao.test_template_permitted(
            template): # TODO Test that current user's role includes template-admin permission
            webapp2.abort(401)

        # Get specified TemplateUser entity
        template_user_id = self.request.get("template_user_id")
        template_user = dao.get_template_user_by_id(template, template_user_id)
        error_msg = None if template_user else "Unable to access specified template user"

        # Build list of TemplateRoles from the datastore
        template_role_list = list()

        # Display the webpage
        self.render(template, template_user_id, template_user, template_role_list, error_msg)

    def post(self):
        template = dao.get_template_by_id(self.request.get("template_id"))
        if not dao.test_template_permitted(
            template): # TODO Test that current user's role includes template-admin permission
            webapp2.abort(401)

        # Build list of TemplateRoles from the datastore
        template_role_list = list()

        # Get specified TemplateUser entity
        template_user_id = self.request.get("template_user_id")
        template_user = dao.get_template_user_by_id(template, template_user_id)
        error_msg = None if template_user else "Unable to access specified team member"

        # Handle delete request
        if template_user and self.request.get("delete"):
            try:
                template_user.key.delete()
                self.redirect("/template_admin/template_user_admin?template_id={}".format(template.key.id()))
                return
            except Exception as e:
                error_msg = "Deleting member from template team failed: {}".format(e)

        # Handle update request
        if template_user and self.request.get("update"):
            # Attempt to update the TemplateUser entity's roles
            template_roles = list()
            for template_role in template_role_list:
                if self.request.get(template_role):
                    template_roles.append(template_role)
            template_user.template_roles = template_roles
            try:
                template_user.put()
                self.redirect("/template_admin/template_user_admin?template_id={}".format(template.key.id()))
                return
            except Exception as e:
                error_msg = "Updating team member failed: {}".format(e)

        # Display the webpage
        self.render(template, template_user_id, template_user, template_role_list, error_msg)

    def render(self, template, template_user_id, template_user, template_role_list, error_msg):
        # Build list of template role checkboxes and whether they should be checked
        view_role_list = list()
        if template_user:
            for template_role in template_role_list:
                role = {"name": template_role,
                        "checked": "checked" if template_role in template_user.template_roles else ""}
                view_role_list.append(role)

        # Create template and template values, render the page
        jinja_template = ui.get_template(self, "template_admin/template_user_edit.html")

        jinja_template_values = dao.get_standard_template_values(template)
        jinja_template_values["template_user_id"] = template_user_id
        jinja_template_values["error_msg"] = error_msg
        jinja_template_values["template"] = template
        jinja_template_values["email"] = template_user.email if template_user else "(unknown)"
        jinja_template_values["roles"] = view_role_list

        self.response.out.write(jinja_template.render(jinja_template_values))