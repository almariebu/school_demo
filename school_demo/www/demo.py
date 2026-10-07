import frappe

from school_demo.setup.demo_constants import CASE_STUDIES, DEMO_PASSWORD, DEMO_USERS

no_cache = 1


def get_context(context):
    context.title = "School Demo"
    context.no_breadcrumbs = True
    context.logins = DEMO_USERS
    context.password = DEMO_PASSWORD
    context.case_studies = CASE_STUDIES
    # logins only exist on sites seeded with `school_demo_seed`
    context.seeded = bool(frappe.conf.get("school_demo_seed"))
    context.desk_url = "/app/school-demo"
