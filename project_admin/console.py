import re
import webapp2
import dao
import ui
from service.interview_service import InterviewService

interview_name_pattern = re.compile(r'(.*)_(.*)')


class RequestHandler(webapp2.RequestHandler):
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
                assignment[
                    interview_type] = interview.assigned_email if interview.assigned_email else u'(not assigned yet)'

        # Display the webpage
        self.render(project, assignments.values())

    def render(self, project, assignments):
        # Create template and template values, render the page
        jinja_template = ui.get_template(self, u'project_admin/console.html')

        jinja_template_values = dao.get_standard_project_values(project)
        jinja_template_values[u'project'] = project
        jinja_template_values[u'assignments'] = assignments

        self.response.out.write(jinja_template.render(jinja_template_values))
