import re
import webapp2
import dao
import ui

email_pattern = re.compile(r'^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$')


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        template = dao.get_template_by_id(self.request.get(u'template_id'))
        if not dao.test_template_permitted(
                template):  # TODO Test that current user's role includes template-admin permission
            webapp2.abort(401)

        # Build list of TemplateRoles from the datastore
        template_role_list = list()

        # Build list of site role checkboxes and whether they should be checked
        view_role_list = list()
        for template_role in template_role_list:
            role = {u'name': template_role, u'checked': False}
            view_role_list.append(role)

        # Display the webpage
        self.render(template, view_role_list)

    def post(self):
        template = dao.get_template_by_id(self.request.get(u'template_id'))
        if not dao.test_template_permitted(
                template):  # TODO Test that current user's role includes template-admin permission
            webapp2.abort(401)

        # Build list of TemplateRoles from the datastore
        template_role_list = list()

        # Validate the submitted email address
        submitted_email = self.request.get(u'email')
        if submitted_email == u'':
            error_msg = None
        elif email_pattern.match(submitted_email):
            if dao.test_email_in_template(template, submitted_email):
                error_msg = u'Already a member of this template team: {}'.format(submitted_email)
            else:
                # Attempt to add a new TemplateUser entity
                template_roles = list()
                for template_role in template_role_list:
                    if self.request.get(template_role):
                        template_roles.append(template_role)
                try:
                    dao.ProjectUser(email=submitted_email.lower(), parent=template.key).put()
                    self.redirect(u'/template_admin/template_user_admin?template_id={}'.format(template.key.id()))
                    return
                except Exception as e:
                    error_msg = u'Adding member to template team failed: {}'.format(e)
        else:
            error_msg = u'Invalid email: {}'.format(submitted_email)

        # Build list of template role checkboxes and whether they should be checked
        view_role_list = list()
        for template_role in template_role_list:
            role = {u'name': template_role, u'checked': self.request.get(template_role)}
            view_role_list.append(role)

        # Display the webpage
        self.render(template, view_role_list, error_msg)

    def render(self, template, view_role_list, error_msg=None):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'template_admin/template_user_add.html')

        jinja_template_values = dao.get_standard_template_values(template)
        jinja_template_values[u'error_msg'] = error_msg
        jinja_template_values[u'email'] = self.request.get(u'email')
        jinja_template_values[u'roles'] = view_role_list

        self.response.out.write(jinja_template.render(jinja_template_values))