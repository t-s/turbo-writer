import webapp2
import dao
import ui

class RequestHandler(webapp2.RequestHandler):
    def get(self):
        if not dao.test_current_user_registered():
            webapp2.abort(401)

        jinja_template = ui.get_template(self, "project_admin/new_project.html")
        jinja_template_values = dao.get_standard_site_values()

        public_template_list = list()
        for template in dao.get_public_templates():
            template_view = dict()
            template_view["template_id"] = template.key.id()
            template_view["name"] = template.name
            template_view["description"] = template.description
            template_view["document_count"] = dao.get_document_count(template)
            template_view["interview_count"] = dao.get_interview_count(template)
            public_template_list.append(template_view)
        jinja_template_values["public_templates"] = public_template_list

        private_template_list = list()
        for template in dao.get_private_templates():
            template_view = dict()
            template_view["template_id"] = template.key.id()
            template_view["name"] = template.name
            template_view["description"] = template.description
            template_view["document_count"] = dao.get_document_count(template)
            template_view["interview_count"] = dao.get_interview_count(template)
            private_template_list.append(template_view)
        jinja_template_values["private_templates"] = private_template_list

        self.response.out.write(jinja_template.render(jinja_template_values))