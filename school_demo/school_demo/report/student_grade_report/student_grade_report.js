frappe.query_reports["Student Grade Report"] = {
    filters: [
        { fieldname: "academic_year", label: __("Academic Year"), fieldtype: "Data" },
        { fieldname: "class_list", label: __("Class List"), fieldtype: "Link", options: "Class List" },
    ],
};
