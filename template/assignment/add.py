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
        variable_type = self.request.get(u'type')

        if not name:
            error_msg = u'You must specify a name for your assignment definition'
        elif not variable_type:
            error_msg = u'You must specify whether this is a single or repeating assignment'
        else:
            assignment_entity = dao.get_assignment_by_name(template, name)
            if assignment_entity:
                error_msg = u'Adding assignment failed: Duplicate assignment name in template'
            else:
                try:
                    assignment_entity = dao.Assignment(name=name, description=description,
                                                       is_repeating=(variable_type == u'repeating'),
                                                       parent=template.key)
                    assignment_entity.put()
                    self.redirect(u'/template/assignment?template_id={}'.format(template.key.id()))
                    return
                except Exception as e:
                    error_msg = u'Adding assignment failed: {}'.format(e)

        # Display the webpage
        self.render(template, error_msg)

    def render(self, template, error_msg=None):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'template/assignment/add.html')

        jinja_template_values = dao.get_standard_template_values(template)
        jinja_template_values[u'error_msg'] = error_msg
        jinja_template_values[u'name'] = self.request.get(u'name')
        jinja_template_values[u'description'] = self.request.get(u'description')
        jinja_template_values[u'type'] = self.request.get(u'type')

        self.response.out.write(jinja_template.render(jinja_template_values))