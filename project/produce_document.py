import re
import webapp2
import dao
import ui
from service.document_service import DocumentService


class RequestHandler(webapp2.RequestHandler):
    def generate_variable_values(self, project, inner_template_values):
        indexed_variable_max_indices = dict()
        for variable in dao.get_variables(project):
            indexed_variable_match_object = re.match("(.*)\[(.*)\]", variable.internal_name)
            if indexed_variable_match_object:
                variable_name = indexed_variable_match_object.group(1)
                variable_index = indexed_variable_match_object.group(2)
                old_max_index = indexed_variable_max_indices[
                    variable_name] if variable_name in indexed_variable_max_indices else None
                if not old_max_index or variable_index > old_max_index:
                    indexed_variable_max_indices[variable_name] = variable_index
            else:
                if variable.input_field == dao.FILE and variable.blob_key and variable.filename:
                    content = "\n<!--B-KEY:{}-->\n[Insert \"{}\" here]\n".format(variable.blob_key, variable.filename)
                else:
                    content = variable.content
                inner_template_values[variable.internal_name] = content
        for variable_name in iter(indexed_variable_max_indices):
            count_name = "{}_count".format(variable_name)
            # Because of how "range" works, count needs to be max index + 1
            count = int(indexed_variable_max_indices[variable_name]) + 1
            inner_template_values[count_name] = count

    def get(self):
        project = dao.get_project_by_id(self.request.get("project_id"))

        if not dao.test_project_permitted(project):
            webapp2.abort(401)

        document = dao.get_document_by_id(project, self.request.get("document_id"))

        # Render HTML document
        inner_template_values = dict()

        inner_template_values["project"] = project

        self.generate_variable_values(project, inner_template_values)

        inner_template = ui.from_string(self, document.content)
        html_document = inner_template.render(inner_template_values)

        # Generate document
        document_service = DocumentService()
        document_service.generate_document(project, document, html_document)

        # Deliver HTTP response
        jinja_template = ui.get_template(self, "project/produce_document.html")
        jinja_template_values = dao.get_standard_project_values(project)
        jinja_template_values["project"] = project
        jinja_template_values["document"] = document
        jinja_template_values["html_document"] = html_document
        self.response.out.write(jinja_template.render(jinja_template_values))