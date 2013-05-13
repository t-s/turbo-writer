import webapp2
import dao
import ui


class RequestHandler(webapp2.RequestHandler):
    def get(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        if not dao.test_project_permissions(project, [dao.PROJECT_OWN, dao.PROJECT_MANAGE]):
            webapp2.abort(401)

        document_list = list()

        for document_entity in dao.get_documents(project):
            document = dict()
            document[u'id'] = document_entity.key.id()
            document[u'key'] = document_entity.key
            document[u'name'] = document_entity.name
            document[u'description'] = document_entity.description
            document[u'style'] = document_entity.style_name
            document_list.append(document)

        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'project/document/index.html')

        jinja_template_values = dao.get_standard_project_values(project)
        jinja_template_values[u'documents'] = document_list

        self.response.out.write(jinja_template.render(jinja_template_values))