frappe.pages['hr-manager-dashboard'].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'HR Manager Dashboard',
        single_column: true
    });

    // Load Bootstrap CSS for tabs
    frappe.require('/assets/frappe/node_modules/bootstrap/dist/css/bootstrap.min.css', () => {});

    // Inject base layout
    build_dashboard_layout(wrapper);

    // Initialize tabs
    setTimeout(() => {
        new bootstrap.Tab(document.querySelector('#summary-tab')).show();
    }, 500);

    // Load data for the active tab
    load_data('summary');

    // Add event listener for tab changes
    document.querySelectorAll('#dashboardTabs .nav-link').forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(event) {
            const target = event.target.getAttribute('data-bs-target').replace('#', '');
            load_data(target);
        });
    });

    // load dynamic colors
    setTimeout(() => {
        load_colors();
    }, 1000);
};

function load_data(tab) {
    switch(tab) {
        case 'summary':
            load_stat_cards(['total-employees', 'new-hires', 'exits', 'joining', 'relieving', 'office-staff', 'site-staff']);
            break;
        case 'attendance':
            load_stat_cards(['total-present', 'total-absent', 'late-entry', 'early-exit']);
            render_employee_inout_chart();
            render_attendance_charts();
            break;
        case 'salary':
            load_stat_cards(['total-salary']);
            render_salary_chart();
            break;
        case 'demographics':
            render_outside_country_chart();
            render_gender_ratio_chart();
            render_designation_chart();
            render_nationality_chart();
            break;
        case 'documents':
            document_expiry_details();
            break;
        case 'payroll':
            load_stat_cards(['total-declaration', 'total-salary-structure', 'total-incentive', 'total-outgoing']);
            render_payroll_details();
            break;
        case 'recruitment':
            load_stat_cards(['job-openings', 'total-applicants', 'accepted-job-applicants', 'rejected-job-applicants', 
                           'joboffers', 'applicantto-hire-percent', 'joboffer-acceptence-rate', 'time-to-fill']);
            render_recruitment_charts();
            break;
        case 'expenses':
            load_stat_cards(['expense-claims', 'approved-claims', 'rejected-claims']);
            render_expense_details();
            break;
    }
}

// Modify the load_stat_cards function to accept specific card IDs
function load_stat_cards(card_ids) {
    const card_methods = {
        'total-employees': {
            method: "frappe.client.get_count",
            args: { doctype: "Employee", filters: { status: "Active" } },
            render_args: ["Total Employees", "As of Today", { doctype: "Employee", filters: { status: "Active" } }, "#198754", "bi-people-fill"]
        },
        // Add all other card definitions here following the same pattern
        // ...
    };

    card_ids.forEach(card_id => {
        if (card_methods[card_id]) {
            frappe.call({
                method: card_methods[card_id].method,
                args: card_methods[card_id].args,
                callback: (r) => {
                    render_stat_card(card_id, ...card_methods[card_id].render_args, r.message);
                }
            });
        }
    });
}

// Keep all other functions the same as before
// ...