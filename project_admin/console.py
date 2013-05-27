import re
import webapp2
import dao
import ui
from service.interview_service import InterviewService

interview_name_pattern = re.compile(r'(.*)_(.*)')


class RequestHandler(webapp2.RequestHandler):
    def get_checklist_info(self, interview):
        checklist_count = 0
        checklist_complete = 0
        for checklist_item in interview.checklist_items:
            checklist_count += 1
            match = dao.parse_checklist_item(checklist_item)
            if interview.name.startswith(u'write_') and match.group(2) == u'T':
                checklist_complete += 1
            if interview.name.startswith(u'review_') and match.group(3) == u'T':
                checklist_complete += 1
        return u'{} of {} checkmarks'.format(checklist_complete, checklist_count)

    def get(self):
        project = dao.get_project_by_id(self.request.get(u'project_id'))
        if not dao.test_project_permissions(project, [dao.PROJECT_OWN, dao.PROJECT_MANAGE]):
            webapp2.abort(401)

        interview_service = InterviewService(project)

        assignments = dict()
        for interview_name in interview_service.get_root_interview_names():
            match = interview_name_pattern.match(interview_name)
            if match:
                interview = interview_service.get_interview_by_name(interview_name)
                interview_type = match.group(1)
                assignment_name = match.group(2)
                if assignment_name in assignments:
                    assignment = assignments[assignment_name]
                else:
                    assignment = dict()
                    assignment[u'name'] = assignment_name
                    assignments[assignment_name] = assignment
                if interview_type == "assign_writer":
                    assignment["assign_writer_interview_name"] = interview.name
                elif interview_type == "assign_reviewer":
                    assignment["assign_reviewer_interview_name"] = interview.name
                elif interview_type == "write":
                    assignment["ready_to_review"] = interview.completed
                    checklist_info = self.get_checklist_info(interview)
                    assignment["draft_status"] = u'Draft completed: {}'.format(
                        checklist_info) if interview.completed else u'Draft not completed'
                    assignment["write_interview_name"] = interview.name
                    assignment[
                        "writer"] = interview.assigned_email if interview.assigned_email else u'(not assigned yet)'
                elif interview_type == "review":
                    checklist_info = self.get_checklist_info(interview)
                    assignment["review_status"] = u'Review completed: {}'.format(
                        checklist_info) if interview.completed else u'Review not completed'
                    assignment["review_interview_name"] = interview.name
                    assignment[
                        "reviewer"] = interview.assigned_email if interview.assigned_email else u'(not assigned yet)'

        # Display the webpage
        self.render(project, assignments.values())

    def render(self, project, assignments):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'project_admin/console.html')

        jinja_template_values = dao.get_standard_project_values(project)
        jinja_template_values[u'project'] = project
        jinja_template_values[u'assignments'] = assignments

        self.response.out.write(jinja_template.render(jinja_template_values))
