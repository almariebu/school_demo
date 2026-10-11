"""Post-upgrade clean-up: default roles, legacy fee mapping and non-destructive file recovery.

Each action is safe to run again and records its result in Migration Tools.
"""

import json
import os
import shutil

import frappe
from frappe import _

from school_demo import logic


def _record(result):
    frappe.db.set_single_value("Migration Tools", "last_result", json.dumps(result, indent=1))
    return result


@frappe.whitelist()
def apply_default_roles():
    """Give each staff member the default roles of their designation. Existing roles are kept."""
    frappe.only_for("System Manager")
    defaults = {}
    for row in frappe.get_all("Designation Role Map Role", filters={"parenttype": "Designation Role Map"}, fields=["parent", "role"]):
        defaults.setdefault(row.parent, []).append(row.role)
    users = roles_added = 0
    for staff in frappe.get_all("Staff Member", fields=["user", "designation"]):
        have = frappe.get_all("Has Role", {"parent": staff.user, "parenttype": "User"}, pluck="role")
        add = logic.roles_to_add(have, staff.designation, defaults)
        if add:
            frappe.get_doc("User", staff.user).add_roles(*add)
            users += 1
            roles_added += len(add)
    return _record({"action": "apply_default_roles", "users_updated": users, "roles_added": roles_added})


@frappe.whitelist()
def map_legacy_fees():
    """Point legacy fee codes at the new fee names. Codes with no mapping stay Unmapped and are listed."""
    frappe.only_for(("System Manager", "Finance Officer"))
    mapping = dict(frappe.get_all("Fee Code Map", fields=["old_code", "new_fee"], as_list=True))
    fees = frappe.get_all("Legacy Fee", fields=["name", "old_code"])
    result = logic.map_fee_codes([f.old_code for f in fees], mapping)
    for fee in fees:
        target = result["mapped"].get(fee.old_code)
        frappe.db.set_value("Legacy Fee", fee.name, {"mapped_fee": target, "status": "Mapped" if target else "Unmapped"})
    return _record({"action": "map_legacy_fees", "mapped": sum(f.old_code in result["mapped"] for f in fees),
                    "unmapped_codes": sorted(set(result["unmapped"]))})


@frappe.whitelist()
def recover_files(backup_folder):
    """Restore File attachments whose file is missing on disk, from a folder under private/backups.

    A file that is already on disk is never overwritten.
    """
    frappe.only_for("System Manager")
    try:
        folder = logic.safe_filename(backup_folder or "")
    except logic.LogicError as e:
        frappe.throw(str(e))
    source = frappe.get_site_path("private", "backups", folder)
    if not os.path.isdir(source):
        frappe.throw(_("Backup folder {0} was not found in private/backups.").format(folder))
    backup_names = [n for n in os.listdir(source) if os.path.isfile(os.path.join(source, n))]
    counts = {"recovered": 0, "kept": 0, "not in backup": 0}
    for rec in frappe.get_all("File", filters={"is_folder": 0}, fields=["file_url", "is_private"]):
        url = rec.file_url or ""
        if not url.startswith(("/files/", "/private/files/")):
            continue
        try:
            name = logic.safe_filename(os.path.basename(url))
        except logic.LogicError:
            continue
        target = frappe.get_site_path("private" if rec.is_private else "public", "files", name)
        action = logic.recovery_action(os.path.exists(target), name, backup_names)
        if action == "recovered":
            shutil.copyfile(os.path.join(source, name), target)
        counts[action] += 1
    return _record({"action": "recover_files", "backup_folder": folder, **counts})
