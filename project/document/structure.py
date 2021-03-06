import re
import webapp2
import dao
import ui

change_pattern = re.compile(r'change_position\.(\d*)')
remove_pattern = re.compile(r'remove_position\.(\d*)')


class RequestHandler(webapp2.RequestHandler):
    def compute_positions(self, project, new_items):
        position = 0
        for item in new_items:
            position += 1
            item.position = position
            item.put()
            dao.touch_project_documents(project)

    def get(self):
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

        if document_entity:
            # Handle add request
            item_type = None
            if self.request.get(u'add_text'):
                item_type = dao.TEXT
            elif self.request.get(u'add_single_variable'):
                item_type = dao.SINGLE_VARIABLE
            elif self.request.get(u'add_repeating_variable'):
                item_type = dao.REPEATING_VARIABLE
            if item_type:
                try:
                    dao.DocumentItem(item_type=item_type, position=dao.get_document_item_count(document_entity) + 1,
                                     parent=document_entity.key).put()
                    dao.touch_project_documents(project)
                except Exception as e:
                    error_msg = u'Adding document item failed: {}'.format(e)

            # Handle request
            items = [item for item in dao.get_document_items(document_entity)]
            # Update items
            for item in items:
                index = item.position - 1
                if item.item_type == dao.SINGLE_VARIABLE:
                    item.variable_name = self.request.get(u'single_name.{}'.format(index))
                elif item.item_type == dao.REPEATING_VARIABLE:
                    item.variable_name = self.request.get(u'repeating_name.{}'.format(index))
                elif item.item_type == dao.TEXT:
                    item.text = self.request.get(u'text.{}'.format(index))
                item.style_name = self.request.get(u'style_name.{}'.format(index))
                item.flow_control = self.request.get(u'flow_control.{}'.format(index))
                try:
                    item.put()
                    dao.touch_project_documents(project)
                except Exception as e:
                    error_msg = u'Updating document failed: {}'.format(e)
                    break
            for request in self.request.arguments():
                # Handle change-position request
                change_position = change_pattern.match(request)
                if change_position:
                    old_index = int(change_position.group(1))
                    new_position_string = None
                    try:
                        new_position_string = self.request.get(u'position.{}'.format(old_index))
                        new_position = int(new_position_string)
                    except:
                        error_msg = u'Invalid position specified: {}'.format(new_position_string)
                        break
                    if new_position < 1:
                        new_position = 1
                    if new_position > len(items):
                        new_position = len(items)
                    new_index = new_position - 1
                    compressed_items = items[:old_index] + items[old_index + 1:]
                    new_items = compressed_items[:new_index]
                    new_items.append(items[old_index])
                    new_items += compressed_items[new_index:]
                    self.compute_positions(project, new_items)
                    # Handle remove request
                remove_position = remove_pattern.match(request)
                if remove_position:
                    index = int(remove_position.group(1))
                    item = items[index]
                    item.key.delete()
                    new_items = items[:index] + items[index + 1:]
                    self.compute_positions(project, new_items)

        if self.request.get(u'update') and not error_msg:
            self.redirect("/project/document?project_id={}".format(project.key.id()))
            return

        # Display the webpage
        self.render(project, document_entity, error_msg)

    def render(self, project, document_entity, error_msg):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'project/document/structure.html')

        jinja_template_values = dao.get_standard_project_values(project)
        jinja_template_values[u'error_msg'] = error_msg
        jinja_template_values[u'document_id'] = document_entity.key.id()
        jinja_template_values[u'name'] = document_entity.name
        jinja_template_values[u'items'] = dao.get_document_items(document_entity)
        jinja_template_values[u'single_names'] = dao.get_single_names(project)
        jinja_template_values[u'repeating_names'] = dao.get_repeating_names(project)
        jinja_template_values[u'style_names'] = dao.get_style_names(project)

        self.response.out.write(jinja_template.render(jinja_template_values))