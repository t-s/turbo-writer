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

        name = self.request.get(u'name')
        description = self.request.get(u'description')
        doc_style = self.request.get(u'doc_style')

        if not name:
            error_msg = u'You must specify a name for your document definition'
        else:
            document_entity = dao.get_document_by_name(template, name)
            if document_entity:
                error_msg = u'Adding document failed: Duplicate document name in template'
            else:
                try:
                    document_entity = dao.Document(name=name,
                                                   internal_name=dao.convert_name_to_internal_name(name),
                                                   description=description, style_name=doc_style,
                                                   parent=template.key)
                    document_entity.put()
                    self.redirect(u'/template/document?template_id={}'.format(template.key.id()))
                    return
                except Exception as e:
                    error_msg = u'Adding document failed: {}'.format(e)

        # Display the webpage
        self.render(template, error_msg)

    def render(self, template, error_msg=None):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'template/document/add.html')

        jinja_template_values = dao.get_standard_template_values(template)
        jinja_template_values[u'error_msg'] = error_msg
        jinja_template_values[u'name'] = self.request.get(u'name')
        jinja_template_values[u'description'] = self.request.get(u'description')
        jinja_template_values[u'doc_style'] = self.request.get(u'doc_style')
        jinja_template_values[u'doc_style_names'] = dao.get_style_names(template)

        self.response.out.write(jinja_template.render(jinja_template_values))