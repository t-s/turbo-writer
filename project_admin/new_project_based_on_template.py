import webapp2
from google.appengine.api import users

import dao
import ui
from service.html_generator_service import HtmlGeneratorService


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

        # Attempt to create a new project
        try:
            name = self.request.get(u'name').strip()
            if not name:
                raise Exception(u'You must provide a name for your project')
            for project in dao.get_projects_by_name(name):
                if dao.test_email_is_project_owner(project, current_email):
                    raise Exception(u'Sorry, you already own a project by that name')

            # Create the new Project entity
            project = dao.Project(name=name, project_type=dao.PROJECT, description=self.request.get(u'description'))
            project_key = project.put()

            # Create a ProjectUser entity, making the current user owner of the new project
            dao.ProjectUser(email=dao.get_current_site_user().email, permissions=[dao.PROJECT_OWN],
                            parent=project_key).put()

            # Get the selected template ID
            template_id = self.request.get(u'template_id')

            if template_id:
                # Generate HTML for the template
                template_entity = dao.get_template_by_id(template_id)
                html_generator_service = HtmlGeneratorService(template_entity)
                html_generator_service.generate_all_html()

                # Copy entities owned by the template entity into the project
                for assignment_entity in dao.get_assignments(template_entity):
                    assignment_entity.clone(project).put()

                for document_entity in dao.get_documents(template_entity):
                    template_document_entity = document_entity.clone(project)
                    template_document_entity.put()
                    for document_item_entity in dao.get_document_items(document_entity):
                        document_item_entity.clone(template_document_entity).put()

                for interview_entity in dao.get_interviews(template_entity):
                    cloned_interview_entity = interview_entity.clone(project)
                    if cloned_interview_entity.auto_assign:
                        cloned_interview_entity.assigned_email = current_email
                    cloned_interview_entity.put()

                for style_entity in dao.get_styles(template_entity):
                    style_entity.clone(project).put()

                for variable_entity in dao.get_variables(template_entity):
                    variable_entity.clone(project).put()

            self.redirect("/project?project_id={}".format(project_key.id()))
            return
        except Exception as e:
            error_msg = u'Creating project failed: {}'.format(e)

        # Display the webpage
        self.render(error_msg)

    def render(self, error_msg=None):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'project_admin/new_project_based_on_template.html')

        jinja_template_values = dao.get_standard_site_values()
        jinja_template_values[u'template_id'] = self.request.get(u'template_id')
        jinja_template_values[u'error_msg'] = error_msg
        jinja_template_values[u'name'] = self.request.get(u'name')
        jinja_template_values[u'description'] = self.request.get(u'description')

        self.response.out.write(jinja_template.render(jinja_template_values))