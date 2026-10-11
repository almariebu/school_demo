import os
import shutil

import frappe
from frappe.tests.utils import FrappeTestCase

from school_demo import migration
from school_demo.tests import utils


class TestDefaultRoles(FrappeTestCase):
    def test_adds_defaults_once_and_keeps_existing_roles(self):
        user = utils.make_user("clerk.migration@example.ph", ["Teacher"]).name
        if not frappe.db.exists("Designation Role Map", "Test Clerk"):
            frappe.get_doc({"doctype": "Designation Role Map", "designation": "Test Clerk", "roles": [{"role": "Registrar"}]}).insert()
        frappe.get_doc({"doctype": "Staff Member", "user": user, "designation": "Test Clerk"}).insert()
        first = migration.apply_default_roles()
        self.assertGreaterEqual(first["users_updated"], 1)
        roles = frappe.get_all("Has Role", {"parent": user, "parenttype": "User"}, pluck="role")
        self.assertIn("Registrar", roles)
        self.assertIn("Teacher", roles)
        self.assertEqual(migration.apply_default_roles()["users_updated"], 0)


class TestFeeMapping(FrappeTestCase):
    def test_unmapped_codes_are_reported_and_left_unmapped(self):
        frappe.db.delete("Legacy Fee")
        frappe.db.delete("Fee Code Map")
        frappe.get_doc({"doctype": "Fee Code Map", "old_code": "T-OLD-1", "new_fee": "Tuition"}).insert()
        for code in ("T-OLD-1", "T-OLD-2"):
            frappe.get_doc({"doctype": "Legacy Fee", "old_code": code, "amount": 100}).insert()
        result = migration.map_legacy_fees()
        self.assertEqual((result["mapped"], result["unmapped_codes"]), (1, ["T-OLD-2"]))
        self.assertEqual(frappe.db.get_value("Legacy Fee", {"old_code": "T-OLD-1"}, ["mapped_fee", "status"]), ("Tuition", "Mapped"))
        self.assertEqual(frappe.db.get_value("Legacy Fee", {"old_code": "T-OLD-2"}, "status"), "Unmapped")


class TestFileRecovery(FrappeTestCase):
    FOLDER = "test-recovery"

    def setUp(self):
        self.files = frappe.get_site_path("public", "files")
        self.backup = frappe.get_site_path("private", "backups", self.FOLDER)
        os.makedirs(self.files, exist_ok=True)
        os.makedirs(self.backup, exist_ok=True)
        names = ("t-missing.txt", "t-kept.txt", "t-gone.txt")
        frappe.db.delete("File", {"file_name": ["in", list(names)]})
        self.paths = {}
        for name in names:  # File.insert saves its own copy (suffixing the name), so use the url it assigns
            tmp = os.path.join(self.files, f"src-{name}")
            with open(tmp, "w") as fh:
                fh.write(f"original {name}")
            doc = frappe.get_doc({"doctype": "File", "file_name": name, "file_url": f"/files/src-{name}", "is_private": 0}).insert()
            self.paths[name] = frappe.get_site_path("public", "files", os.path.basename(doc.file_url))
            os.remove(tmp)
        for name in ("t-missing.txt", "t-gone.txt"):
            os.remove(self.paths[name])
        for name in ("t-missing.txt", "t-kept.txt"):  # t-gone.txt is deliberately absent from the backup
            with open(os.path.join(self.backup, os.path.basename(self.paths[name])), "w") as fh:
                fh.write("from backup")
        self.addCleanup(shutil.rmtree, self.backup, True)
        self.addCleanup(lambda: [os.path.exists(p) and os.remove(p) for p in self.paths.values()])

    def test_recovers_missing_keeps_existing_and_reports_the_rest(self):
        result = migration.recover_files(self.FOLDER)
        self.assertEqual(open(self.paths["t-missing.txt"]).read(), "from backup")
        self.assertEqual(open(self.paths["t-kept.txt"]).read(), "original t-kept.txt")
        self.assertGreaterEqual(result["recovered"], 1)
        self.assertGreaterEqual(result["kept"], 1)
        self.assertGreaterEqual(result["not in backup"], 1)
        self.assertEqual(migration.recover_files(self.FOLDER)["recovered"], 0)

    def test_backup_folder_cannot_escape_private_backups(self):
        for bad in ("../public", "a/b", "..", ""):
            with self.assertRaises(frappe.ValidationError):
                migration.recover_files(bad)
        with self.assertRaises(frappe.ValidationError):
            migration.recover_files("no-such-folder")
