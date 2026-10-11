frappe.ui.form.on("Migration Tools", {
    refresh(frm) {
        const run = (label, method, args) =>
            frm.add_custom_button(
                label,
                () => {
                    frappe.call({ method, args, freeze: true, callback: () => frm.reload_doc() });
                },
                __("Run")
            );
        run(__("Apply default roles"), "school_demo.migration.apply_default_roles");
        run(__("Map legacy fees"), "school_demo.migration.map_legacy_fees");
        run(__("Recover files"), "school_demo.migration.recover_files", { backup_folder: frm.doc.backup_folder });
    },
});
