import re
import webapp2
import dao
import ui

indexed_name_pattern = re.compile(r'(.*)\[(.*)\]')
image_element_pattern = re.compile(r'\*\*\* INSERT "(.*?)" \(image/.*?\)(.*?)HERE \*\*\*')


class RequestHandler(webapp2.RequestHandler):
    def generate_html_document(self, project, document):
        inner_template_values = dict()
        inner_template_values[u'project'] = project
        self.generate_variable_values(project, inner_template_values)
        inner_template = ui.from_string(self, document.content)
        return inner_template.render(inner_template_values)

    def generate_variable_values(self, project, inner_template_values):
        indexed_variable_max_indices = dict()
        for variable in dao.get_variables(project):
            indexed_variable_match_object = indexed_name_pattern.match(variable.name)
            if indexed_variable_match_object:
                variable_name = indexed_variable_match_object.group(1)
                variable_index = indexed_variable_match_object.group(2)
                old_max_index = indexed_variable_max_indices[
                    variable_name] if variable_name in indexed_variable_max_indices else None
                if not old_max_index or int(variable_index) > old_max_index:
                    indexed_variable_max_indices[variable_name] = int(variable_index)
            else:
                content = variable.content if variable.content else u''
                inner_template_values[variable.internal_name] = content
        for variable_name in iter(indexed_variable_max_indices):
            count_name = u'{}_count'.format(variable_name)
            # Because of how "range" works, count needs to be max index + 1
            count = int(indexed_variable_max_indices[variable_name]) + 1
            inner_template_values[count_name] = count

    def get(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        if not dao.test_project_permissions(project, []):
            webapp2.abort(401)

        document = dao.get_document_by_id(project, self.request.get(u'document_id'))
        html_document = self.generate_html_document(project, document)
        html_document = self.replace_image_elements(project, html_document)

        # Deliver HTTP response
        jinja_template = ui.get_template(self, u'project/produce_document.html')
        jinja_template_values = dao.get_standard_project_values(project)
        jinja_template_values[u'project'] = project
        jinja_template_values[u'document'] = document
        jinja_template_values[u'html_document'] = html_document
        self.response.out.write(jinja_template.render(jinja_template_values))

    def replace_image_elements(self, project, document):
        while True:
            match = image_element_pattern.search(document)
            if match:
                before = document[:match.start()]
                after = document[match.end():]
                attachment = dao.get_attachment_by_filename(project, match.group(1))
                if attachment:
                    document = u'{}<img src="/project_admin/attachment_download?project_id={}&attachment_id={}" {}>{}'.format(
                        before, project.key.id(), attachment.key.id(), match.group(2), after)
                else:
                    document = u'{}<br/>***UNABLE TO FIND ATTACHMENT "{}"***<br/>{}'.format(before, match.group(1),
                                                                                            after)
            else:
                return document
