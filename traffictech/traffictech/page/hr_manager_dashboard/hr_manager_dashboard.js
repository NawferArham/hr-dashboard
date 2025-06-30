frappe.pages['hr-manager-dashboard'].on_page_load = function(wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'HR Manager Dashboard',
		single_column: true
	});

	// Inject base layout
	build_dashboard_layout(wrapper);

	// Render all dashboard data
	load_data();

	// load dynamic colors
	setTimeout(() => {
		load_colors();
	}, 1000);
};


function build_dashboard_layout(wrapper) {
	$(wrapper).find('.layout-main-section').load('/assets/traffictech/html/page/hr_manager_dashboard.html');
}

function load_data() {
	load_stat_cards();
	render_employee_inout_chart();
	render_salary_chart();
	render_outside_country_chart();
	render_gender_ratio_chart();
	render_designation_chart();
	render_nationality_chart();
	render_recruitment_charts();
	document_expiry_details();
	render_attendance_charts();
	render_expense_details();
	render_payroll_details();
}

function load_colors() {
	frappe.call({
		method: "traffictech.traffictech.page.utils.get_dynamic_colors",
		callback: (r) => {
			if (!r.message) {
				return
			}
			let colors = r.message;

			document.querySelectorAll('.stat-card').forEach(card => {
				card.style.background = colors.card_backgound_color;

				const card_title = card.querySelector('.stat-content h4');
				if (card_title) card_title.style.color = colors.card_title_color;

				const card_value = card.querySelector('.stat-value');
				if (card_value) card_value.style.color = colors.card_value_color;

				const card_sub = card.querySelector('.stat-sub');
				if (card_sub) card_sub.style.color = colors.card_sub_heading;

				const card_icon = card.querySelector('.stat-icon-top-right');
				if (card_icon) card_icon.style.color = colors.icon_color;
			});

			document.querySelectorAll('.chart-main-container').forEach(chart => {
				chart.style.background = colors.chart_backgound_color;
				chart.style.color = colors.chart_text_color;
			}); 

			const total_card = document.querySelector('.total-salary-card');
			const card_title = total_card.querySelector('.stat-content h4');
			if (card_title) card_title.style.color = colors.card_title_color;
			total_card.style.background = colors.card_backgound_color;

			const exp_btn = document.querySelector('.document-expiry-btn');
			exp_btn.style.background = colors.card_backgound_color;
			const exp_btn_title = exp_btn.querySelector('a');
			exp_btn_title.style.color = colors.card_title_color;
		}
	});
	
}

function load_stat_cards() {
	frappe.call({
		method: "frappe.client.get_count",
		args: {
			doctype: "Employee",
			filters: {
				status: "Active"
			}
		},
		callback: (r) => {
			render_stat_card("total-employees", "Total Employees", r.message, "As of Today", {
				doctype: "Employee",
				filters: { status: "Active" }
			}, "#198754", "bi-people-fill");
		}
	});

	frappe.call({
		method: "frappe.client.get_count",
		args: {
			doctype: "Employee",
			filters: {
				status: "Active",
				date_of_joining: ['>=', frappe.datetime.year_start()]
			}
		},
		callback: (r) => {
			render_stat_card("new-hires", "New Hires", r.message, "This Year", {
				doctype: "Employee",
				filters: {
					status: "Active",
					date_of_joining: ['>=', frappe.datetime.year_start()]
				}
			}, "black", "bi-person-plus-fill");
		}
	});

	frappe.call({
		method: "frappe.client.get_count",
		args: {
			doctype: "Employee",
			filters: {
				relieving_date: ['>=', frappe.datetime.year_start()]
			}
		},
		callback: (r) => {
			render_stat_card("exits", "Employee Exits", r.message, "This Year", {
				doctype: "Employee",
				filters: {
					relieving_date: ['>=', frappe.datetime.year_start()]
				}
			}, "black", "bi-person-dash-fill");
		}
	});

	frappe.call({
		method: "frappe.client.get_count",
		args: {
			doctype: "Employee",
			filters: {
				status: 'Active',
				date_of_joining: ['>=', frappe.datetime.month_start()]
			}
		},
		callback: (r) => {
			render_stat_card("joining", "Joining", r.message, "This Month", {
				doctype: "Employee",
				filters: {
					status: 'Active',
					date_of_joining: ['>=', frappe.datetime.month_start()]
				}
			}, "black", "bi-box-arrow-in-right");
		}
	});

	frappe.call({
		method: "frappe.client.get_count",
		args: {
			doctype: "Employee",
			filters: {
				status: 'Active',
				date_of_joining: ['>=', frappe.datetime.month_start()]
			}
		},
		callback: (r) => {
			render_stat_card("relieving", "Relieving", r.message, "This Month", {
				doctype: "Employee",
				filters: {
					date_of_joining: ['>=', frappe.datetime.month_start()]
				}
			}, "black", "bi-box-arrow-right");
		}
	});

	frappe.call({
		method: "frappe.client.get_count",
		args: {
			doctype: "Employee",
			filters: {
				status: 'Active',
				custom_work_location: "Head Office"
			}
		},
		callback: (r) => {
			render_stat_card("office-staff", "Office Staff", r.message, " ", route_options={
				doctype: "Employee",
				filters: {
					status: 'Active',
					custom_work_location: "Head Office"
				}
			}, txt_color="black", icon_class="bi-building");
		}
	});

	frappe.call({
		method: "frappe.client.get_count",
		args: {
			doctype: "Employee",
			filters: {
				status: 'Active',
				custom_work_location: "Site"
			}
		},
		callback: (r) => {
			render_stat_card("site-staff", "Site Staff", r.message, " ", {
				doctype: "Employee",
				filters: {
					status: 'Active',
					custom_work_location: "Site"
				}
			}, "black", "bi-person-workspace");
		}
	});

	// salary

	frappe.call({
		method: "traffictech.traffictech.page.utils.get_total_salary_structure_amount",
		callback: (r) => {
			render_stat_card("total-salary", `Total Salary : ${format_currency(r.message)}`, "", "", {
				doctype: "Salary Structure Assignment",
				filters: {
					docstatus: 1,
				}
			}, txt_color="black", icon_class="", total = true);
		}
	});

	// recruitement
	frappe.call({
		method: "frappe.client.get_count",
		args: {
			doctype: "Job Opening",
			filters: {
				status:"Open",
				posted_on: ['>=', frappe.datetime.year_start()]
			}
		},
		callback: (r) => {
			render_stat_card("job-openings", "Job Openings", r.message, "This Month", {
				doctype: "Job Opening"
			}, "black", "bi-briefcase");
		}
	});

	frappe.call({
		method: "frappe.client.get_count",
		args: {
			doctype: "Job Applicant",
			filters: {
				creation: ['>=', frappe.datetime.month_start()]
			}
		},
		callback: (r) => {
			render_stat_card("total-applicants", "Total Applicants", r.message, "This Month", {
				doctype: "Job Applicant"
			}, "black", "bi-person-lines-fill");
		}
	});

	frappe.call({
		method: "frappe.client.get_count",
		args: {
			doctype: "Job Applicant",
			filters: {
				status:"Accepted"
			}
		},
		callback: (r) => {
			render_stat_card("accepted-job-applicants", "Accepted Job Applicants", r.message, " ", {
				doctype: "Job Applicant",
				filters: {
					status: "Accepted"
				}
			}, "black", "bi-hand-thumbs-up-fill");
		}
	});


	frappe.call({
		method: "frappe.client.get_count",
		args: {
			doctype: "Job Applicant",
			filters: {
				status:"Rejected"
			}
		},
		callback: (r) => {
			render_stat_card("rejected-job-applicants", "Rejected Job Applicants", r.message, "", {
				doctype: "Job Applicant",
				filters: {
					status: "Rejected"
				}
			}, "black", "bi-hand-thumbs-down-fill");
		}
	});

	frappe.call({
		method: "frappe.client.get_count",
		args: {
			doctype: "Job Offer",
			filters: {
				offer_date: ['>=', frappe.datetime.month_start()]
			}
		},
		callback: (r) => {
			render_stat_card("joboffers", "Job Offers", r.message, "This Month", {
				doctype: "Job Offer"
			}, "black", "bi-envelope-open-fill");
		}
	});

	frappe.call({
		method: "hrms.hr.doctype.job_applicant.job_applicant.get_applicant_to_hire_percentage",
		callback: (r) => {
			if (r.message) {
				render_stat_card("applicantto-hire-percent", "Applicant Hire Percentage", `${r.message.value}%`, "This Month", {
					doctype: "Job Offer",
					filters: {status: "Accepted"}
				});
			}
		}
	});

	frappe.call({
		method: "hrms.hr.doctype.job_offer.job_offer.get_offer_acceptance_rate",
		callback: (r) => {
			const acceptanceRate = r.message.rate || 0;  // Access the rate property, or default to 0 if not found
			render_stat_card("joboffer-acceptence-rate", "Job Offer Acceptance Rate", acceptanceRate, "This Month", {
				doctype: "Job Offer",
				filters: {status: "Accepted"}
			});
		}
	});

	frappe.call({
		method: "frappe.client.get_count",
		args: {
			doctype: "Employee",
			filters: {
				date_of_joining: ['>=', frappe.datetime.year_start()]
			}
		},
		callback: (r) => {
			render_stat_card("time-to-fill", "Time to Fill", "2 days", "This Month", {
				doctype: "",
				filters: {}
			});
		}
	});


	// attendance
	frappe.call({
		method: "frappe.client.get_count",
		args: {
			doctype: "Attendance",
			filters: {
				attendance_date: ['>=', frappe.datetime.month_start()],
				status: "Present",
				docstatus: 1
			}
		},
		callback: (r) => {
			render_stat_card("total-present", "Total Present", r.message, "This Month", {
				doctype: "Attendance",
				filters: {
					attendance_date: ['>=', frappe.datetime.month_start()],
					status: "Present",
					docstatus: 1
				}
			}, txt_color="green", icon_class="bi-calendar-check");
		}
	});

	frappe.call({
		method: "frappe.client.get_count",
		args: {
			doctype: "Attendance",
			filters: {
				attendance_date: ['>=', frappe.datetime.month_start()],
				status: "Absent",
				docstatus: 1
			}
		},
		callback: (r) => {
			render_stat_card("total-absent", "Total Absent", r.message, "This Month", {
				doctype: "Attendance",
				filters: {
					attendance_date: ['>=', frappe.datetime.month_start()],
					status: "Absent",
					docstatus: 1
				}
			},txt_color="red", icon_class="bi-calendar-x");
		}
	});

	frappe.call({
		method: "frappe.client.get_count",
		args: {
			doctype: "Attendance",
			filters: {
				attendance_date: ['>=', frappe.datetime.month_start()],
				late_entry: 1,
				docstatus: 1
			}
		},
		callback: (r) => {
			render_stat_card("late-entry", "Late Entry", r.message, "This Month", {
				doctype: "Attendance",
				filters: {
					attendance_date: ['>=', frappe.datetime.month_start()],
					late_entry: 1,
					docstatus: 1
				}
			}, txt_color="red", icon_class="bi-clock-history");
		}
	});

	frappe.call({
		method: "frappe.client.get_count",
		args: {
			doctype: "Attendance",
			filters: {
				attendance_date: ['>=', frappe.datetime.month_start()],
				early_exit: 1,
				docstatus: 1
			}
		},
		callback: (r) => {
			render_stat_card("early-exit", "Early Exit", r.message, "This Month", {
				doctype: "Attendance",
				filters: {
					attendance_date: ['>=', frappe.datetime.month_start()],
					early_exit: 1,
					docstatus: 1
				}
			}, txt_color="red", icon_class="bi-door-closed");
		}
	});
}


function render_stat_card(id, title, value, subtitle, route_options = null, txt_color = "black", icon_class = "", total = false) {
	let value_html = value !== undefined && value !== null && txt_color
		? `<p class="stat-value" style="color: ${txt_color};">${value}</p>` : '';

	const icon_html = icon_class
	? `<div class="stat-icon-top-right"><i class="bi ${icon_class}"></i></div>` : '';

	if (total) {
		$(`#${id}`).html(`
			<div class="clickable-card total-salary-card" ${route_options ? `data-route='${JSON.stringify(route_options)}'` : ''}>
				<div class="stat-content">
					<h4>${title}</h4>
				</div>
			</div>
		`);
	} else {
		$(`#${id}`).html(`
			<div class="stat-card clickable-card position-relative" ${route_options ? `data-route='${JSON.stringify(route_options)}'` : ''}>
				${icon_html}
				<div class="stat-content">
					<h4>${title}</h4>
					${value_html}
					<p class="stat-sub">${subtitle} &nbsp</p>
				</div>
			</div>
		`);
	}

	if (route_options) {
		$(`#${id} .stat-card`).on('click', function () {
			frappe.set_route("List", route_options.doctype, {
				...route_options.filters
			});
		});
		$(`#${id} .total-salary-card`).on('click', function () {
			frappe.set_route("List", route_options.doctype, {
				...route_options.filters
			});
		});
	}
}


function render_employee_inout_chart() {
	frappe.call({
		method: "traffictech.traffictech.page.utils.get_employee_in_out",
		callback: function(r) {
			if (!r.message) return;

			new frappe.Chart("#employee-inout-chart", {
				title: "Employee In Out",
				data: {
					labels: r.message.labels,
					datasets: [{
						name: "",
						values: r.message.values
					}]
				},
				type: 'donut',
				colors: ['#000000', '#ffff00'],
				is_series: 1,
				height: 250
			});
		}
	});
}


function render_salary_chart() {
	frappe.call({
		method: "traffictech.traffictech.page.utils.get_salary_data",
		args: {
			group_by: "department",
		},
		callback: function(r) {
			if (!r.message) return;

			new Chart(document.getElementById("department-wise-salary-chart"), {
				type: 'bar',
				data: {
					labels: r.message.labels,
					datasets: [{
						label: "Salaries",
						data: r.message.values,
						backgroundColor: "yellow",
					}]
				},
				options: {
					indexAxis: 'y',
					barThickness: 5,
					onClick: (e, items) => {
						if (items.length > 0) {
							const label = items[0].element.$context.raw.label;
							frappe.set_route("List", "Salary Structure Assignment", {
								"department": label,
								"docstatus": 1
							});
						}
					},
					responsive: true,
					plugins: {
						legend: { display: false },
						tooltip: {
							titleColor: "yellow",
							bodyColor: "yellow"
						}
					},
					scales: {
						x: {
							ticks: {
								color: "black" // x-axis label color
							},
							grid: {
								display: false
							}
						},
						y: {
							ticks: {
								color: "black" // y-axis label color
							}
						}
					}
				}
			});

		}
	});
}


function render_outside_country_chart() {
	frappe.call({
		method: "traffictech.traffictech.page.utils.get_outside_country_data",
		callback: function(r) {
			if (!r.message) return;
			new frappe.Chart("#outside-country-chart", {
				title: "Employee In Outside Country",
				data: {
					labels: r.message.labels,
					datasets: [{ name: "Count", values: r.message.values }]
				},
				type: 'bar',
				colors: ['#ffff00', '#000000'],
				is_series: 1,
				height: 240
			});
		}
	});
}


function render_gender_ratio_chart() {
	frappe.call({
		method: "traffictech.traffictech.page.utils.get_gender_ratio",
		callback: function(r) {
			if (!r.message) return;
			new frappe.Chart("#gender-ratio-chart", {
				title: "Gender Diversity Ratio",
				data: {
					labels: r.message.labels,
					datasets: [{ name: "Count", values: r.message.values }]
				},
				type: 'pie',
				colors: ['#000000', '#ffff00'],
				height: 240
			});
		}
	});
}

function render_designation_chart() {
	frappe.call({
		method: "traffictech.traffictech.page.utils.get_designation_counts",
		callback: function(r) {
			if (!r.message) return;

			const chart_data =  {
				labels: r.message.labels,
				datasets: [{
					name: "Employees",
					values: r.message.values
				}]
			}

			const container = document.querySelector("#designation-chart");
			new frappe.Chart(container, {
				title: "Designation Wise Employee Count",
				data: chart_data,
				colors: ['#000000', '#ffff00'],
				type: 'pie',
				height: 240,
			});

			make_chart_clickable(container, chart_data, "Employee", "designation", "pie");
		}
	});
}

function render_nationality_chart() {
	frappe.call({
		method: "traffictech.traffictech.page.utils.get_nationality_counts",
		callback: function(r) {
			if (!r.message) return;
			const real_labels = r.message.labels;
			const values = r.message.values;

			const numbered_labels = real_labels.map((_, i) => (i + 1).toString());

			const chart_data = {
				labels: numbered_labels,
				datasets: [{ name: "Count", values: values }]
			};

			const container = document.querySelector("#nationality-chart");

			new frappe.Chart(container, {
				title: "Nationality Wise Employee",
				data: chart_data,
				type: 'line',
				height: 240,
				colors: ['#ffff00'],
				tooltipOptions: {
					formatTooltipX: d => real_labels[parseInt(d) - 1],
					formatTooltipY: d => d
				}
			});

			make_chart_clickable(container, chart_data, "Employee", "custom_nationality", "line");
		}
	});
}

function render_recruitment_charts() {
	frappe.call({
		method: "traffictech.traffictech.page.utils.get_job_applicant_details",
		args: { group_by: "job_title"},
		callback: function(r) {
			if (!r.message) return;
			const chart_data =  {
				labels: r.message.labels,
				datasets: [{ name: "Count", values: r.message.values }]
			}

			let container = document.querySelector("#job-applicant-pipeline");
			new frappe.Chart(container, {
				title: "Job Applicant Pipeline",
				data: chart_data,
				type: 'bar',
				colors: ['#ffff00', '#000000'],
				height: 240
			});

			make_chart_clickable(container, chart_data, "Job Applicant", "job_title", "bar");
		}
	});

	frappe.call({
		method: "traffictech.traffictech.page.utils.get_job_applicant_details",
		args: { group_by: "source"},
		callback: function(r) {
			if (!r.message) return;
			const chart_data =  {
				labels: r.message.labels,
				datasets: [{ name: "Count", values: r.message.values }]
			}

			let container = document.querySelector("#job-applicant-source");
			new frappe.Chart(container, {
				title: "Job Applicant Source",
				data: chart_data,
				type: 'donut',
				colors: ['#ffff00', '#000000'],
				height: 240
			});

			make_chart_clickable(container, chart_data, "Job Applicant", "source", "donut");
		}
	});

	frappe.call({
		method: "traffictech.traffictech.page.utils.get_job_applicant_details",
		args: { group_by: "country"},
		callback: function(r) {
			if (!r.message) return;
			const chart_data =  {
				labels: r.message.labels,
				datasets: [{ name: "Count", values: r.message.values }]
			}

			let container = document.querySelector("#job-applicantby-country");
			new frappe.Chart(container, {
				title: "Job Applicant By Country",
				data: chart_data,
				colors: ['#ffff00', '#000000'],
				type: 'donut',
				height: 240
			});

			make_chart_clickable(container, chart_data, "Job Applicant", "country", "donut");
		}
	});

	frappe.call({
		method: "traffictech.traffictech.page.utils.get_job_applicant_details",
		args: { group_by: "status"},
		callback: function(r) {
			if (!r.message) return;
			const chart_data =  {
				labels: r.message.labels,
				datasets: [{ name: "Count", values: r.message.values }]
			}

			let container = document.querySelector("#job-applicant-status");
			new frappe.Chart(container, {
				title: "Job Applicant Status",
				data: chart_data,
				colors: ['#ffff00', '#000000'],
				type: 'pie',
				height: 240
			});

			make_chart_clickable(container, chart_data, "Job Applicant", "status", "pie");
		}
	});

	frappe.call({
		method: "traffictech.traffictech.page.utils.get_job_applicant_frequency",
		callback: function(r) {
			if (!r.message) return;
			const chart_data =  {
				labels: r.message.labels,
				datasets: [{ name: "Count", values: r.message.values }]
			}

			let container = document.querySelector("#job-applicant-frequency");
			new frappe.Chart(container, {
				title: "Job Applicant Frequency",
				data: chart_data,
				colors: ['#ffff00', '#000000'],
				type: 'line',
				height: 240
			});

			make_chart_clickable(container, chart_data, "Job Applicant", "creation", "bar");
		}
	});

	frappe.call({
		method: "traffictech.traffictech.page.utils.get_job_openings_details",
		args: { group_by: "designation"},
		callback: function(r) {
			if (!r.message) return;
			const chart_data =  {
				labels: r.message.labels,
				datasets: [{ name: "Count", values: r.message.values }]
			}

			let container = document.querySelector("#designation-wise-opening");
			new frappe.Chart(container, {
				title: "Designation Wise Openinig",
				data: chart_data,
				colors: ['#ffff00', '#000000'],
				type: 'bar',
				height: 240
			});

			make_chart_clickable(container, chart_data, "Job Opening", "designation", "bar");
		}
	});

	frappe.call({
		method: "traffictech.traffictech.page.utils.get_job_openings_details",
		args: { group_by: "department"},
		callback: function(r) {
			if (!r.message) return;
			const chart_data =  {
				labels: r.message.labels,
				datasets: [{ name: "Count", values: r.message.values }]
			}

			let container = document.querySelector("#department-wise-opening");
			new frappe.Chart(container, {
				title: "Department Wise Openinig",
				data: chart_data,
				colors: ['#ffff00', '#000000'],
				type: 'donut',
				height: 240
			});

			make_chart_clickable(container, chart_data, "Job Opening", "department", "bar");
		}
	});
}

function document_expiry_details() {
	frappe.call({
		method: "traffictech.traffictech.page.utils.get_document_expiry_details",
		callback: function(r) {
			if (!r.message) return;
			const chart_data =  {
				labels: r.message.labels,
				datasets: [{ name: "Count", values: r.message.values }]
			}

			let container = document.querySelector("#document-expiry-details");
			new frappe.Chart(container, {
				title: "Document Expiry Details",
				data: chart_data,
				colors: ['#ffff00', '#000000'],
				type: 'bar',
				height: 240
			});

			make_chart_clickable(container, chart_data, "Employee", "", "bar");
		}
	});
}

function render_attendance_charts() {
	frappe.call({
		method: "traffictech.traffictech.page.utils.get_attendance_counts",
		callback: function(r) {
			if (!r.message) return;
			const chart_data =  {
				labels: r.message.labels,
				datasets: [{ name: "Count", values: r.message.values }]
			}

			let container = document.querySelector("#attendance-count");
			new frappe.Chart(container, {
				title: "Attendance Count",
				data: chart_data,
				type: 'line',
				height: 240,
				colors: ['#ffff00', '#000000'],
			});

			// make_chart_clickable(container, chart_data, "Employee", "custom_nationality", "line");
		}
	});
}

function render_expense_details() {
	frappe.call({
		method: "frappe.client.get_count",
		args: {
			doctype: "Expense Claim",
			filters: {
				"docstatus": 1,
				"posting_date": ['>=', frappe.datetime.month_start()],
			}
		},
		callback: (r) => {
			render_stat_card("expense-claims", "Expense Claims", r.message, "This Month", {
				doctype: "Expense Claim",
				filters: {
					"docstatus": 1,
					"posting_date": ['>=', frappe.datetime.month_start()],
				}
			});
		}
	});

	frappe.call({
		method: "frappe.client.get_count",
		args: {
			doctype: "Expense Claim",
			filters: {
				"docstatus": 1,
				"posting_date": ['>=', frappe.datetime.month_start()],
				"approval_status": "Approved",
			}
		},
		callback: (r) => {
			render_stat_card("approved-claims", "Approved Claims", r.message, "This Month", {
				doctype: "Expense Claim",
				filters: {
					"docstatus": 1,
					"posting_date": ['>=', frappe.datetime.month_start()],
					"approval_status": "Approved",
				}
			});
		}
	});

	frappe.call({
		method: "frappe.client.get_count",
		args: {
			doctype: "Expense Claim",
			filters: {
				"docstatus": 1,
				"posting_date": ['>=', frappe.datetime.month_start()],
				"approval_status": "Rejected",
			}
		},
		callback: (r) => {
			render_stat_card("rejected-claims", "Rejected Claims", r.message, "This Month", {
				doctype: "Expense Claim",
				filters: {
					"docstatus": 1,
					"posting_date": ['>=', frappe.datetime.month_start()],
					"approval_status": "Rejected",
				}
			});
		}
	});

	frappe.call({
		method: "traffictech.traffictech.page.utils.get_expense_claims",
		args: {
			group_by: "department"
		},
		callback: function(r) {
			if (!r.message) return;
			const chart_data =  {
				labels: r.message.labels,
				datasets: [{ name: "Count", values: r.message.values }]
			}

			let container = document.querySelector("#departmentwise-claims-chart");
			new frappe.Chart(container, {
				title: "Expense Claims",
				data: chart_data,
				type: 'bar',
				colors: ['#ffff00', '#000000'],
				height: 240,
			});

			make_chart_clickable(container, chart_data, "Expense Claim", "department", "bar");
		}
	}); 

}


function render_payroll_details() {
	let last_year = frappe.datetime.get_today().split('-')[0] - 1;

	let year_from_date = `${last_year}-01-01`;
	let year_to_date = `${last_year}-12-31`;
	frappe.call({
		method: "frappe.client.get_count",
		args: {
			doctype: "Employee Tax Exemption Declaration",
			filters: {
				"docstatus": 1,
				"creation": ['between', [year_from_date, year_to_date]],
			}
		},
		callback: (r) => {
			render_stat_card("total-declaration", "Total Declaration", r.message, " ", {
				doctype: "Employee Tax Exemption Declaration",
				filters: {
					"docstatus": 1,
					"creation": ['between', [year_from_date, year_to_date]],
				}
			}, "black", "bi-journal-text");
		}
	});

	frappe.call({
		method: "frappe.client.get_count",
		args: {
			doctype: "Salary Structure",
			filters: {
			}
		},
		callback: (r) => {
			render_stat_card("total-salary-structure", "Total Salary Structure", r.message, " ", {
				doctype: "Salary Structure"
			});
		}
	});

	let from_date = frappe.datetime.month_start(frappe.datetime.add_months(frappe.datetime.get_today(), -1));
	let to_date = frappe.datetime.month_end(frappe.datetime.add_months(frappe.datetime.get_today(), -1));
	frappe.call({
		method: "traffictech.traffictech.page.utils.get_total_incentive",
		args: { from_date, to_date },
		callback: (r) => {
			render_stat_card("total-incentive", "Total Incentive Given", format_currency(r.message), "Last Month", {
				doctype: "Employee Incentive",
				filters: {
					docstatus: 1,
					payroll_date: ['between', [from_date, to_date]],
				}
			}, "black", "bi-gift-fill");
		}
	});


	frappe.call({
		method: "traffictech.traffictech.page.utils.get_total_salary_structure_amount",
		callback: (r) => {
			render_stat_card("total-outgoing", `Total Outgoing`, format_currency(r.message), "", {
				doctype: "Salary Structure Assignment",
				filters: {
					docstatus: 1,
				}
			});
		}
	});

	frappe.call({
		method: "traffictech.traffictech.page.utils.get_monthly_salary_data",
		callback: function(r) {
			if (!r.message) return;
			const chart_data =  {
				labels: r.message.labels,
				datasets: [{ name: "Amount", values: r.message.values }]
			}

			let container = document.querySelector("#monthly-salary-chart");
			new frappe.Chart(container, {
				title: "Monthly Outgoing Salary",
				data: chart_data,
				type: 'line',
				colors: ['#ffff00'],
				height: 240
			});

			make_chart_clickable(container, chart_data, "Salary Slip", "", "line");
		}
	});

}


function make_chart_clickable(container, chart_data, document_type, filter_field, chart_type = "bar") {
	container.addEventListener("click", function (e) {
		let index;
		if (chart_type === "bar" || chart_type === "line") {
			const bar = e.target.closest('.bar, .point');
			if (!bar) return;

			index = parseInt(bar.getAttribute('data-point-index'), 10);
		} else if (chart_type === "pie") {

		} else {
			console.warn("Unsupported chart type for click handler");
			return;
		}

		if (isNaN(index)) return;

		const label = chart_data.labels[index];
		const filters = {};
		if (["QID", "Passport", "Health Card"].includes(label)) {
			if (label == "Passport") {
				filters["valid_upto"] = ["<", frappe.datetime.get_today()];
			}
			if (label == "Health Card") {
				filters["expiry"] = ["<", frappe.datetime.get_today()];
			}
			if (label == "QID") {
				filters["qid_expiry"] = ["<", frappe.datetime.get_today()];
			}
			frappe.set_route("List", document_type, filters);
		} else {
			if (document_type && filter_field && label) {
				filters[filter_field] = label;

				frappe.set_route("List", document_type, filters);
			} else {
				frappe.msgprint("Missing chart info or clicked label.");
			}
		}
	});
}
