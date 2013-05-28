import webapp2
import dao
import ui


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        template = dao.get_template_by_id(self.request.get(u'template_id'))
        if not dao.test_template_permissions(template, [dao.TEMPLATE_OWN, dao.TEMPLATE_EDIT]):
            webapp2.abort(401)

        # Display the webpage
        self.render(template)

    def post(self):
        template = dao.get_template_by_id(self.request.get(u'template_id'))
        if not dao.test_template_permissions(template, [dao.TEMPLATE_OWN, dao.TEMPLATE_EDIT]):
            webapp2.abort(401)
        error_msg = None

        # Handle contribute request
        if self.request.get(u'contribute'):
            try:
                name = self.request.get(u'name').strip()
                if not name:
                    raise Exception(u'You must provide a name for the public template')
                if dao.get_public_template_by_name(name):
                    raise Exception(u'Sorry, that name is taken')

                new_template = dao.Project(name=name, project_type=dao.PUBLIC_TEMPLATE, status=dao.STATUS_PENDING,
                                           description=self.request.get(u'description'))
                new_template.put()

                for assignment_entity in dao.get_assignments(template):
                    assignment_entity.clone(new_template).put()

                for document_entity in dao.get_documents(template):
                    template_document_entity = document_entity.clone(new_template)
                    template_document_entity.put()
                    for document_item_entity in dao.get_document_items(document_entity):
                        document_item_entity.clone(template_document_entity).put()

                for interview_entity in dao.get_interviews(template):
                    cloned_interview_entity = interview_entity.clone(new_template)
                    cloned_interview_entity.put()

                for style_entity in dao.get_styles(template):
                    style_entity.clone(new_template).put()

                for variable_entity in dao.get_variables(template):
                    variable_entity.clone(new_template).put()

                self.redirect("/template?template_id={}".format(template.key.id()))
                return
            except Exception as e:
                error_msg = u'Contributing project failed: {}'.format(e)

        # Display the webpage
        self.render(template, error_msg)

    def render(self, template, error_msg=None):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'template_admin/contribute.html')

        jinja_template_values = dao.get_standard_template_values(template)
        jinja_template_values[u'template'] = template
        jinja_template_values[u'error_msg'] = error_msg
        jinja_template_values[u'name'] = self.request.get(u'name')

        self.response.out.write(jinja_template.render(jinja_template_values))