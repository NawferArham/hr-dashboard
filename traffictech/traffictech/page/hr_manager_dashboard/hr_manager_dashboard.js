frappe.pages['hr-manager-dashboard'].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'HR Manager Dashboard',
        single_column: true
    });

    // Inject base layout
    build_dashboard_layout(wrapper);

    // Load all data initially
    load_data();

    // load dynamic colors
    setTimeout(() => {
        load_colors();
    }, 1000);
};

function build_dashboard_layout(wrapper) {
    $(wrapper).find('.layout-main-section').html(`
        <div class="dashboard-wrapper">
            <ul class="nav nav-tabs mb-3" id="dashboardTabs" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="summary-tab" data-bs-toggle="tab" data-bs-target="#summary" type="button" role="tab">Summary</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="attendance-tab" data-bs-toggle="tab" data-bs-target="#attendance" type="button" role="tab">Attendance</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="salary-tab" data-bs-toggle="tab" data-bs-target="#salary" type="button" role="tab">Salary</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="demographics-tab" data-bs-toggle="tab" data-bs-target="#demographics" type="button" role="tab">Demographics</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="documents-tab" data-bs-toggle="tab" data-bs-target="#documents" type="button" role="tab">Documents</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="recruitment-tab" data-bs-toggle="tab" data-bs-target="#recruitment" type="button" role="tab">Recruitment</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="expenses-tab" data-bs-toggle="tab" data-bs-target="#expenses" type="button" role="tab">Expenses</button>
                </li>
            </ul>

            <div class="tab-content" id="dashboardTabsContent">
                <!-- Summary Tab -->
                <div class="tab-pane fade show active" id="summary" role="tabpanel">
                    <div class="section-heading">Employee Summary</div>
                    <hr>
                    <div class="cards-grid">
                        <div id="total-employees"></div>
                        <div id="new-hires"></div>
                        <div id="exits"></div>
                        <div id="joining"></div>
                        <div id="relieving"></div>
                    </div>
                </div>

                <!-- Attendance Tab -->
                <div class="tab-pane fade" id="attendance" role="tabpanel">
                    <div class="section-heading">Attendance</div>
                    <hr>
                    <div class="attendance-section">
                        <div class="attendance-grid cards-grid" style="width:50%; margin-right:16px;">
                            <div id="office-staff"></div>
                            <div id="site-staff"></div>
                        </div>
                        <div class="chart-main-container" id="employee-inout-chart" style="width:50%;"></div>
                    </div>

                    <div class="section-heading">Attendance Details</div>
                    <hr>
                    <div class="cards-grid">
                        <div id="total-present"></div>
                        <div id="total-absent"></div>
                        <div id="late-entry"></div>
                        <div id="early-exit"></div>
                    </div>
                    <div class="chart-main-container w-100 mt-2" id="attendance-count"></div>
                </div>

                <!-- Salary Tab -->
                <div class="tab-pane fade" id="salary" role="tabpanel">
                    <div class="section-heading">Salary Details</div>
                    <hr>
                    <div class="salary-details">
                        <div class="total-salary" id="total-salary"></div>
                        <canvas class="chart-main-container" id="department-wise-salary-chart" style="margin-top: 8px;"></canvas>
                    </div>
                </div>

                <!-- Demographics Tab -->
                <div class="tab-pane fade" id="demographics" role="tabpanel">
                    <div class="presence-gender">
                        <div class="" style="width: 50%; margin-right:16px;">
                            <div class="section-heading">Presence</div>
                            <hr>
                            <div class="chart-main-container" id="outside-country-chart"></div>
                        </div>
                        <div class="" style="width: 50%;">
                            <div class="section-heading">Gender</div>
                            <hr>
                            <div class="chart-main-container" id="gender-ratio-chart"></div>
                        </div>
                    </div>

                    <div class="section-heading">Designation</div>
                    <hr>
                    <div class="chart-main-container" id="designation-chart"></div>

                    <div class="section-heading">Nationality</div>
                    <hr>
                    <div class="chart-main-container" id="nationality-chart"></div>
                </div>

                <!-- Documents Tab -->
                <div class="tab-pane fade" id="documents" role="tabpanel">
                    <div class="section-heading">Document Expiry Details</div>
                    <hr>
                    <div class="cards-grid">
                        <div id="" class="document-expiry-btn"><a href="/app/query-report/Document%20Expiry%20Details">Open Report</a></div>
                    </div>
                    <div class="chart-main-container w-100 mt-2" id="document-expiry-details"></div>
                </div>

                <!-- Recruitment Tab -->
                <div class="tab-pane fade" id="recruitment" role="tabpanel">
                    <div class="section-heading">Recruitment</div>
                    <hr>
                    <div class="cards-grid">
                        <div id="job-openings"></div>
                        <div id="total-applicants"></div>
                        <div id="accepted-job-applicants"></div>
                        <div id="rejected-job-applicants"></div>
                    </div>
                    <div class="cards-grid" style="margin-top: 10px;">
                        <div id="joboffers"></div>
                        <div id="applicantto-hire-percent"></div>
                        <div id="joboffer-acceptence-rate"></div>
                        <div id="time-to-fill"></div>
                    </div>

                    <div class="d-flex mt-2">
                        <div class="chart-main-container w-50 mr-4" id="job-applicant-pipeline"></div>
                        <div class="chart-main-container w-50" id="job-applicant-source"></div>
                    </div>

                    <div class="d-flex mt-2">
                        <div class="chart-main-container w-50 mr-4" id="job-applicantby-country"></div>
                        <div class="chart-main-container w-50" id="job-applicant-status"></div>
                    </div>

                    <div class="chart-main-container w-100 mt-2" id="job-applicant-frequency"></div>

                    <div class="d-flex mt-2">
                        <div class="chart-main-container w-50 mr-4" id="designation-wise-opening"></div>
                        <div class="chart-main-container w-50" id="department-wise-opening"></div>
                    </div>
                </div>

                <!-- Expenses Tab -->
                <div class="tab-pane fade" id="expenses" role="tabpanel">
                    <div class="section-heading">Expense Claims</div>
                    <hr>
                    <div class="cards-grid">
                        <div id="expense-claims"></div>
                        <div id="approved-claims"></div>
                        <div id="rejected-claims"></div>
                    </div>
                    <div class="chart-main-container w-100 mt-2" id="departmentwise-claims-chart"></div>
                </div>
            </div>
        </div>
    `);

    // Load Bootstrap JS for tabs functionality
    frappe.require('/assets/frappe/node_modules/bootstrap/dist/js/bootstrap.bundle.min.js', () => {
        // Initialize the first tab
        const firstTab = new bootstrap.Tab(document.getElementById('summary-tab'));
        firstTab.show();
    });
};

// Keep all other existing functions exactly the same (load_data, load_stat_cards, etc.)
// ...
