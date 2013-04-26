import re
import webapp2
import dao
import ui
from service.html_generator_service import HtmlGeneratorService


prereq_pattern = re.compile(r'prereq_assignment_name\.(\d)')
change_prereq_position_pattern = re.compile(r'change_prereq_assignment_name_position\.(\d)')
remove_prereq_position_pattern = re.compile(r'remove_prereq_assignment_name_position\.(\d)')

variable_pattern = re.compile(r'variable_name\.(\d)')
change_variable_position_pattern = re.compile(r'change_variable_name_position\.(\d)')
remove_variable_position_pattern = re.compile(r'remove_variable_name_position\.(\d)')

checklist_pattern = re.compile(r'checklist_item\.(\d)')
change_checklist_position_pattern = re.compile(r'change_checklist_item_position\.(\d)')
remove_checklist_position_pattern = re.compile(r'remove_checklist_item_position\.(\d)')


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

        if assignment_entity:
            # Handle request
            assignment_entity.instructions_to_manager = self.request.get(u'instructions_to_manager')
            assignment_entity.instructions_to_writer = self.request.get(u'instructions_to_writer')

            # Handle prerequisite assignments
            prereq_assignment_names = list()
            for argument in self.request.arguments():
                prereq_assignment_name = prereq_pattern.match(argument)
                if prereq_assignment_name:
                    name = dict()
                    name[u'position'] = int(prereq_assignment_name.group(1))
                    name[u'name'] = self.request.get(argument)
                    prereq_assignment_names.append(name)
            prereq_assignment_names.sort(cmp=lambda x, y: cmp(x[u'position'], y[u'position']))
            for argument in self.request.arguments():
                change_prereq_assignment_name_position = change_prereq_position_pattern.match(argument)
                if change_prereq_assignment_name_position:
                    old_position = int(change_prereq_assignment_name_position.group(1))
                    old_index = old_position - 1
                    new_position = int(self.request.get(u'prereq_assignment_name_position.{}'.format(old_position)))
                    if new_position < 1:
                        new_position = 1
                    if new_position > len(assignment_entity.prereq_assignment_names):
                        new_position = len(assignment_entity.prereq_assignment_names)
                    new_index = new_position - 1
                    compressed_names = prereq_assignment_names[:old_index] + prereq_assignment_names[old_index + 1:]
                    new_names = compressed_names[:new_index]
                    new_names.append(prereq_assignment_names[old_index])
                    new_names += compressed_names[new_index:]
                    prereq_assignment_names = new_names
            for argument in self.request.arguments():
                remove_prereq_assignment_name_position = remove_prereq_position_pattern.match(argument)
                if remove_prereq_assignment_name_position:
                    position = int(remove_prereq_assignment_name_position.group(1))
                    del prereq_assignment_names[position - 1]
            assignment_entity.prereq_assignment_names = [name[u'name'] for name in prereq_assignment_names]
            if self.request.get(u'add_prereq_assignment_name'):
                assignment_entity.prereq_assignment_names.append(u'')

            # Handle variable names
            names = list()
            for argument in self.request.arguments():
                variable_name = variable_pattern.match(argument)
                if variable_name:
                    name = dict()
                    name[u'position'] = int(variable_name.group(1))
                    name[u'name'] = self.request.get(argument)
                    names.append(name)
            names.sort(cmp=lambda x, y: cmp(x[u'position'], y[u'position']))
            for argument in self.request.arguments():
                change_variable_name_position = change_variable_position_pattern.match(argument)
                if change_variable_name_position:
                    old_position = int(change_variable_name_position.group(1))
                    old_index = old_position - 1
                    new_position = int(self.request.get(u'variable_name_position.{}'.format(old_position)))
                    if new_position < 1:
                        new_position = 1
                    if new_position > len(assignment_entity.variable_names):
                        new_position = len(assignment_entity.variable_names)
                    new_index = new_position - 1
                    compressed_names = names[:old_index] + names[old_index + 1:]
                    new_names = compressed_names[:new_index]
                    new_names.append(names[old_index])
                    new_names += compressed_names[new_index:]
                    names = new_names
            for argument in self.request.arguments():
                remove_variable_name_position = remove_variable_position_pattern.match(argument)
                if remove_variable_name_position:
                    position = int(remove_variable_name_position.group(1))
                    del names[position - 1]
            assignment_entity.variable_names = [name[u'name'] for name in names]
            if self.request.get(u'add_variable_name'):
                assignment_entity.variable_names.append(u'')

            # Handle checklist items
            items = list()
            for argument in self.request.arguments():
                checklist_item = checklist_pattern.match(argument)
                if checklist_item:
                    item = dict()
                    item[u'position'] = int(checklist_item.group(1))
                    item[u'item'] = self.request.get(argument)
                    items.append(item)
            items.sort(cmp=lambda x, y: cmp(x[u'position'], y[u'position']))
            for argument in self.request.arguments():
                change_checklist_item_position = change_checklist_position_pattern.match(argument)
                if change_checklist_item_position:
                    old_position = int(change_checklist_item_position.group(1))
                    old_index = old_position - 1
                    new_position = int(self.request.get(u'checklist_item_position.{}'.format(old_position)))
                    if new_position < 1:
                        new_position = 1
                    if new_position > len(assignment_entity.checklist_items):
                        new_position = len(assignment_entity.checklist_items)
                    new_index = new_position - 1
                    compressed_items = items[:old_index] + items[old_index + 1:]
                    new_items = compressed_items[:new_index]
                    new_items.append(items[old_index])
                    new_items += compressed_items[new_index:]
                    items = new_items
            for argument in self.request.arguments():
                remove_checklist_item_position = remove_checklist_position_pattern.match(argument)
                if remove_checklist_item_position:
                    position = int(remove_checklist_item_position.group(1))
                    del items[position - 1]
            assignment_entity.checklist_items = [item[u'item'] for item in items]
            if self.request.get(u'add_checklist_item'):
                assignment_entity.checklist_items.append(u'')

            assignment_entity.put()

            html_generator_service = HtmlGeneratorService(template)
            html_generator_service.generate_interview_html(assignment_entity)

        if self.request.get(u'update') and not error_msg:
            self.redirect(u'/template/assignment?template_id={}'.format(template.key.id()))
            return

        # Display the webpage
        self.render(template, assignment_entity, error_msg)

    def render(self, template, assignment_entity, error_msg):
        assignment_names = dao.get_assignment_names(template)
        if assignment_entity.name in assignment_names:
            assignment_names.remove(assignment_entity.name)

        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'template/assignment/structure.html')

        jinja_template_values = dao.get_standard_template_values(template)
        jinja_template_values[u'error_msg'] = error_msg
        jinja_template_values[u'assignment_id'] = assignment_entity.key.id()
        jinja_template_values[u'name'] = assignment_entity.name
        jinja_template_values[u'is_repeating'] = assignment_entity.is_repeating
        jinja_template_values[
            u'instructions_to_manager'] = assignment_entity.instructions_to_manager if assignment_entity.instructions_to_manager else u''
        jinja_template_values[
            u'instructions_to_writer'] = assignment_entity.instructions_to_writer if assignment_entity.instructions_to_writer else u''
        jinja_template_values[
            'prereq_assignment_names'] = assignment_entity.prereq_assignment_names if assignment_entity.prereq_assignment_names else list()
        jinja_template_values[u'variable_names'] = assignment_entity.variable_names
        jinja_template_values[u'checklist_items'] = assignment_entity.checklist_items
        jinja_template_values[u'single_names'] = dao.get_single_names(template)
        jinja_template_values[u'assignment_names'] = assignment_names
        jinja_template_values[u'repeating_names'] = dao.get_repeating_names(template)

        self.response.out.write(jinja_template.render(jinja_template_values))
