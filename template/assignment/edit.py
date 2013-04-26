import webapp2
import dao
import ui
from service.html_generator_service import HtmlGeneratorService


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        template = dao.get_template_by_id(self.request.get(u'template_id'))
        if not dao.test_template_permitted(
                template):  # TODO Test that current user's role includes template-admin permission
            webapp2.abort(401)

        assignment_entity = dao.get_assignment_by_id(template, self.request.get(u'assignment_id'))
        error_msg = None if assignment_entity else u'Unable to access specified assignment'

        # Display the webpage
        self.render(template, assignment_entity, error_msg)

    def post(self):
        template = dao.get_template_by_id(self.request.get(u'template_id'))
        if not dao.test_template_permitted(
                template):  # TODO Test that current user's role includes template-admin permission
            webapp2.abort(401)

        assignment_entity = dao.get_assignment_by_id(template, self.request.get(u'assignment_id'))
        error_msg = None if assignment_entity else u'Unable to access specified assignment'

        # Handle delete request
        if assignment_entity and self.request.get(u'delete'):
            try:
                assignment_entity.key.delete()
                # Delete associated generated interviews
                for interview_entity in dao.get_interviews_by_assignment_name(template, assignment_entity.name):
                    interview_entity.key.delete()
                self.redirect(u'/template/assignment?template_id={}'.format(template.key.id()))
                return
            except Exception as e:
                error_msg = u'Deleting assignment from template failed: {}'.format(e)

        # Handle update request
        if assignment_entity and self.request.get(u'update'):
            try:
                assignment_entity.description = self.request.get(u'description')
                assignment_entity.is_repeating = (self.request.get(u'type') == u'repeating')
                assignment_entity.put()

                html_generator_service = HtmlGeneratorService(template)
                html_generator_service.generate_interview_html(assignment_entity)

                self.redirect(u'/template/assignment?template_id={}'.format(template.key.id()))
                return
            except Exception as e:
                error_msg = u'Updating assignment failed: {}'.format(e)

        # Display the webpage
        self.render(template, assignment_entity, error_msg)

    def render(self, template, assignment_entity, error_msg):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'template/assignment/edit.html')

        jinja_template_values = dao.get_standard_template_values(template)
        jinja_template_values[u'error_msg'] = error_msg
        jinja_template_values[u'assignment_id'] = assignment_entity.key.id()
        jinja_template_values[u'name'] = assignment_entity.name
        jinja_template_values[u'description'] = assignment_entity.description
        jinja_template_values[u'type'] = u'repeating' if assignment_entity.is_repeating else u'single'

        self.response.out.write(jinja_template.render(jinja_template_values))