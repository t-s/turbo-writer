import webapp2
import dao
import ui


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        if not dao.test_site_permission(dao.SITE_ADMIN_USERS):
            webapp2.abort(401)

        # Display the webpage
        self.render(None)

    def post(self):
        if not dao.test_site_permission(dao.SITE_ADMIN_USERS):
            webapp2.abort(401)

        # Get specified Project entity
        name = self.request.get(u'name')
        project_or_template_type = self.request.get(u'project_or_template_type')
        selected_project = None
        error_msg = None
        for project in dao.get_projects_or_templates_by_name(name):
            if project.project_type == project_or_template_type:
                if not selected_project:
                    selected_project = project
                else:
                    error_msg = u'Name/type not unique; functionality not supported'
        if not selected_project:
            error_msg = u'Name/type not found'

        if not error_msg and self.request.get(u'delete'):
            # Handle delete request
            try:
                dao.delete_project(selected_project)
                self.redirect("/")
                return
            except Exception as e:
                error_msg = u'Deleting project or template failed: {}'.format(e)

        # Display the webpage
        self.render(error_msg)

    def render(self, error_msg):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'site_admin/project_or_template_delete.html')

        jinja_template_values = dao.get_standard_site_values()
        jinja_template_values[u'error_msg'] = error_msg
        jinja_template_values[u'name'] = self.request.get(u'name')
        jinja_template_values[u'project_or_template_type'] = self.request.get(u'project_or_template_type')

        self.response.out.write(jinja_template.render(jinja_template_values))