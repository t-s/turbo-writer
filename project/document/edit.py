import webapp2
import dao
import ui


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        if not dao.test_project_permissions(project, [dao.PROJECT_OWN, dao.PROJECT_MANAGE]):
            webapp2.abort(401)

        document_entity = dao.get_document_by_id(project, self.request.get(u'document_id'))
        error_msg = None if document_entity else u'Unable to access specified document'

        # Display the webpage
        self.render(project, document_entity, error_msg)

    def post(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        if not dao.test_project_permissions(project, [dao.PROJECT_OWN, dao.PROJECT_MANAGE]):
            webapp2.abort(401)

        document_entity = dao.get_document_by_id(project, self.request.get(u'document_id'))
        error_msg = None if document_entity else u'Unable to access specified document'

        # Handle delete request
        if document_entity and self.request.get(u'delete'):
            try:
                document_entity.key.delete()
                dao.touch_project_documents(project)
                self.redirect("/project/document?project_id={}".format(project.key.id()))
                return
            except Exception as e:
                error_msg = u'Deleting document from project failed: {}'.format(e)

        # Handle update request
        if document_entity and self.request.get(u'update'):
            try:
                document_entity.description = self.request.get(u'description')
                document_entity.style_name = self.request.get(u'doc_style')
                document_entity.put()
                dao.touch_project_documents(project)
                self.redirect("/project/document?project_id={}".format(project.key.id()))
                return
            except Exception as e:
                error_msg = u'Updating document failed: {}'.format(e)

        # Display the webpage
        self.render(project, document_entity, error_msg)

    def render(self, project, document_entity, error_msg):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'project/document/edit.html')

        jinja_template_values = dao.get_standard_project_values(project)
        jinja_template_values[u'error_msg'] = error_msg
        jinja_template_values[u'document_id'] = document_entity.key.id()
        jinja_template_values[u'name'] = document_entity.name
        jinja_template_values[u'description'] = document_entity.description
        jinja_template_values[u'doc_style'] = document_entity.style_name
        jinja_template_values[u'doc_style_names'] = dao.get_style_names(project)

        self.response.out.write(jinja_template.render(jinja_template_values))