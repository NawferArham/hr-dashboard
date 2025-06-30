frappe.pages['employee-dashboard'].on_page_load = function(wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Employee Dashboard',
		single_column: true
	});

	$(wrapper).find('.layout-main-section').html(`
		<header>
			<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
		</header>

		<div class="employee-dashboard">
			<div class="row grid">
				<div class="col profile" id="profile-section"></div>
				<div class="col announcement" id="announcements"></div>
			</div>
			<div class="row grid">
				<div class="col leave" id="leave-summary"></div>
				<div class="col actions" id="quick-actions"></div>
				<div class="col directory" id="phone-directory"></div>
			</div>
			<div class="row grid">
				<div class="col salary" id="salary-slip"></div>
				<div class="col other" id="other-details"></div>
			</div>
			<div class="row grid">
				<div class="col reminders" id="weekly-reminders"></div>
			</div>
		</div>
	`);

	load_employee_dashboard();
};

function load_employee_dashboard() {
	frappe.call({
		method: "traffictech.traffictech.page.employee_dashboard.employee_dashboard.get_emp_details",
		callback: function(r) {
			if (r.message) {
				render_profile(r.message);
				render_announcements();
				render_leave_summary(r.message.name);
				render_quick_actions();
				render_salary_slip(r.message.name);
				render_other_details(r.message.name);
				render_directory();
				render_reminders();
			}
		}
	});
}

function render_profile(emp) {
	const doj = frappe.datetime.str_to_obj(emp.date_of_joining);
	const today = frappe.datetime.str_to_obj(frappe.datetime.nowdate());
	const service_years = frappe.datetime.get_diff(today, doj);
	const full_profile_link = `/app/employee/${emp.name}`;

	$("#profile-section").html(`
		<div class="card profile-card">
			<div class="profile-content position-relative">
				<div class="stat-icon-top-right"><i class="fa fa-user-circle"></i></div>

				<div class="profile-left">
					<img src="${emp.image || '/files/default-profile.png'}" class="profile-image">
					<a href="${full_profile_link}" class="btn btn-sm btn-primary">View Full Profile</a>
				</div>
				<div class="profile-details">
					<h3>${emp.employee_name}</h3>
					<p><b>ID:</b> ${emp.name}</p>
					<p>${emp.designation || ''}</p>
					<p> ${emp.department || ''}</p>
					<p><b>Reports to:</b> ${emp.reports_to || ''}</p>
					<p><b>Service Period:</b> ${service_years} day(s)</p>
				</div>
			</div>
		</div>
	`);
}

function render_announcements(emp_id) {
	frappe.call({
		method: "frappe.client.get_list",
		args: {
			doctype: "Leave Allocation",
			filters: { employee: emp_id },
			fields: ["leave_type", "total_leaves_allocated"]
		},
		callback: function(r) {
			let html = `<div class="card position-relative">
				<div class="stat-icon-top-right"><i class="fa fa-bullhorn"></i></div>
				<h4>Announcements</h4> 
				<p> Sample Announcement </p>
			</div>`;
			$("#announcements").html(html);
		}
	});
}

// 📘 Leave
function render_leave_summary(emp_id) {
	frappe.call({
		method: "frappe.client.get_list",
		args: {
			doctype: "Leave Allocation",
			filters: { employee: emp_id},
			fields: ["leave_type", "total_leaves_allocated"]
		},
		callback: function(r) {
			let html = `
			<div class="card">
			<div class="stat-icon-top-right"><i class="fa fa-plane-departure"></i></div>
			<h4>Leave Summary</h4>`;
			r.message.forEach(leave => {
				const remaining = leave.total_leaves_allocated;
				html += `<p>${leave.leave_type}: ${remaining} days left</p>`;
			});
			html += '</div>';
			$("#leave-summary").html(html);
		}
	});
}

// 💰 Salary
function render_salary_slip(emp_id) {
	frappe.call({
		method: "frappe.client.get_list",
		args: {
			doctype: "Salary Slip",
			filters: { employee: emp_id, docstatus: 1 },
			fields: ["name", "posting_date", "net_pay"],
			order_by: "posting_date desc",
			limit: 1
		},
		callback: function(r) {
			if (r.message.length) {
				const s = r.message[0];
				$("#salary-slip").html(`
					<div class="card position-relative">
						<div class="stat-icon-top-right"><i class="fa fa-file-invoice-dollar"></i></div>
						<h4>Salary Slip</h4>
						<p><b>Month:</b> ${s.posting_date}</p>
						<p><b>Net Pay:</b> ${format_currency(s.net_pay)}</p>
						<a href="/app/salary-slip/${s.name}">View Slip</a>
					</div>
				`);
			} else {
				$("#salary-slip").html(`
					<div class="card position-relative">
						<div class="stat-icon-top-right"><i class="fa fa-file-invoice-dollar"></i></div>
						<h4>Salary Slip</h4>
						<p><b>Month:</b> </p>
						<p><b>Net Pay:</b> </p>
						<a href="/app/salary-slip/">View Slip</a>
					</div>
				`);
			}
		}
	});
}

function render_other_details(emp_id) {
	$("#other-details").html(`
		<div class="card position-relative">
			<div class="stat-icon-top-right"><i class="fa fa-chalkboard-teacher"></i></div>
			<h4>Voting</h4>
			<p>"Measuring Employee Engagement"</p>
		</div>
	`);
}

// ➕ Actions
function render_quick_actions() {
	$("#quick-actions").html(`
		<div class="card position-relative">
			<div class="stat-icon-top-right"><i class="fa fa-bolt"></i></div>
			<h4>Quick Actions</h4>
			<ul>
				<li><a href="/app/leave-application/new">Apply for Leave</a></li>
				<li><a href="/app/petty-cash-entry/new">Petty Cash</a></li>
				<li><a href="/app/attendance-request/new">Attendance Request</a></li>
				<li><a href="/app/back-from-vacation/new">Back from Vacation</a></li>
				<li><a href="/app/business-trip-reimbursement/new">Business Trip Reimbursement</a></li>
				<li><a href="/app/exit-permit-form/new">Exit Permit Form</a></li>
			</ul>
		</div>
	`);
}


function render_reminders() {
	frappe.call({
		method: "traffictech.traffictech.page.employee_dashboard.employee_dashboard.get_todos",
		callback: function(r) {
			const todos = r.message || [];

			let html = `
				<div class="card shadow-sm border-0 position-relative">
					<div class="stat-icon-top-right"><i class="fa fa-calendar-alt"></i></div>
					<div class="card-body pb-2">
						<h6 class="mb-3 text-primary fw-semibold">
							Weekly Reminders
						</h6>
						<ul class="list-group list-group-flush">
			`;

			if (!todos.length) {
				html += `<li class="list-group-item text-muted small">No open reminders 🎉</li>`;
			} else {
				todos.forEach(todo => {
					const date = frappe.datetime.str_to_user(todo.date);
					html += `
						<li class="list-group-item px-2 py-2 small d-flex justify-content-between align-items-start border-0 border-bottom">
							<div>
								<div class="fw-semibold text-dark">${todo.description}</div>
								<small class="text-muted">${date}</small>
							</div>
							<a href="/app/todo/${todo.name}" class="small text-decoration-none text-primary">View</a>
						</li>
					`;
				});
			}
			html += `
						</ul>
					</div>
				</div>
			`;
			$("#weekly-reminders").html(html);
		}
	});
}


// 📇 Directory
function render_directory() {
	frappe.call({
		method: "frappe.client.get_list",
		args: {
			doctype: "Employee",
			fields: ["employee_name", "cell_number", "user_id"],
			limit: 3
		},
		callback: function(r) {
			let html = `<div class="card">
			<div class="stat-icon-top-right"><i class="fa fa-address-book"></i></div>

			<h4>Directory</h4>`;
			r.message.forEach(emp => {
				html += `<p>${emp.employee_name} - ${emp.cell_number}</p>`;
			});
			html += '</div>';
			$("#phone-directory").html(html);
		}
	});
}