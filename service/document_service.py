# import re
# import dao
# import ui
#
# indexed_name_pattern = re.compile(r'(.*)\[(.*)\]')
#
#
# class DocumentService:
#     def generate_document(self, project, document):
#         inner_template_values = dict()
#         inner_template_values[u'project'] = project
#         self.generate_variable_values(project, inner_template_values)
#         inner_template = ui.from_string(self, document.content)
#         return inner_template.render(inner_template_values)
#
#     def generate_variable_values(self, project, inner_template_values):
#         indexed_variable_max_indices = dict()
#         for variable in dao.get_variables(project):
#             indexed_variable_match_object = indexed_name_pattern.match(variable.name)
#             if indexed_variable_match_object:
#                 variable_name = indexed_variable_match_object.group(1)
#                 variable_index = indexed_variable_match_object.group(2)
#                 old_max_index = indexed_variable_max_indices[
#                     variable_name] if variable_name in indexed_variable_max_indices else None
#                 if not old_max_index or int(variable_index) > old_max_index:
#                     indexed_variable_max_indices[variable_name] = int(variable_index)
#             else:
#                 content = variable.content if variable.content else u''
#                 inner_template_values[variable.internal_name] = content
#         for variable_name in iter(indexed_variable_max_indices):
#             count_name = u'{}_count'.format(variable_name)
#             # Because of how "range" works, count needs to be max index + 1
#             count = int(indexed_variable_max_indices[variable_name]) + 1
#             inner_template_values[count_name] = count
#
