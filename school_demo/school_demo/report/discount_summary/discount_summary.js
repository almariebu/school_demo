frappe.query_reports["Discount Summary"] = {
    filters: [
        { fieldname: "school_year", label: __("School Year"), fieldtype: "Data" },
        { fieldname: "semester", label: __("Semester"), fieldtype: "Select", options: "\n1st Semester\n2nd Semester\nSummer" },
        { fieldname: "discount_type", label: __("Discount Type"), fieldtype: "Data" },
    ],
};
