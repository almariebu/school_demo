import frappe


def after_install():
    """Seed demo data on install when the site opts in via `school_demo_seed` in site_config.json."""
    if not frappe.conf.get("school_demo_seed"):
        return
    try:
        from school_demo.setup.demo_data import seed

        seed()
    except Exception:
        # never block app installation because of demo data
        frappe.log_error(title="School Demo: seed failed during install")
        print("School Demo: seeding failed, see Error Log. Run `bench --site <site> execute school_demo.setup.demo_data.seed`.")
