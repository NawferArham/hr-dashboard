app_name = "traffictech"
app_title = "Traffictech"
app_publisher = "Niyaz Razak"
app_description = "Customization Traffictech"
app_email = "niyasibnurazak@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "traffictech",
# 		"logo": "/assets/traffictech/logo.png",
# 		"title": "Traffictech",
# 		"route": "/traffictech",
# 		"has_permission": "traffictech.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/traffictech/css/traffictech.css"
app_include_js = [
	"/assets/traffictech/js/rejection_reason.js",
	"https://cdn.jsdelivr.net/npm/qrcode/build/qrcode.min.js",
	"https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js",
	"https://cdn.jsdelivr.net/npm/chart.js",
]

# include js, css files in header of web template
# web_include_css = "/assets/traffictech/css/traffictech.css"
# web_include_js = "/assets/traffictech/js/traffictech.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "traffictech/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"Task" : "public/js/task.js",
	"Opportunity" : "public/js/opportunity.js",
	"Customer" : "public/js/customer.js",
	"Quotation" : "public/js/quotation.js",
	"Lead" : "public/js/lead.js",
	"Employee" : "public/js/employee.js",
	"User" : "public/js/user.js",
}
doctype_list_js = {"Task" : "public/js/task_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "traffictech/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "traffictech.utils.jinja_methods",
# 	"filters": "traffictech.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "traffictech.install.before_install"
# after_install = "traffictech.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "traffictech.uninstall.before_uninstall"
# after_uninstall = "traffictech.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

boot_session = "traffictech.boot.set_bootinfo"

on_session_creation = "traffictech.utils.set_home_page"


# before_app_install = "traffictech.utils.before_app_install"
# after_app_install = "traffictech.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "traffictech.utils.before_app_uninstall"
# after_app_uninstall = "traffictech.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "traffictech.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Data Import": "traffictech.overrides.data_import.CustomDataImport"
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Communication": {
		"after_insert": "traffictech.crud_events.set_email_category"
	},
	"Task": {
		"after_insert": "traffictech.tasks.assign_task_to_team",
		"validate": [
			"traffictech.tasks.calculate_total_time",
			"traffictech.tasks.change_team_assignment",
			"traffictech.tasks.update_preventive_maintenance",
		]
	},
	"ToDo": {
		"after_insert": "traffictech.tasks.update_task_details"
	},
	"File": {
		"validate": "traffictech.crud_events.make_file_private"
	},
	"Salary Structure Assignment": {
		"validate": "traffictech.crud_events.calculate_ssa_total",
		"on_submit": "traffictech.crud_events.set_ctc_in_emp",
		"on_cancel": "traffictech.crud_events.set_ctc_in_emp"
	},
	"Employee": {
		"validate": "traffictech.crud_events.get_ctc_from_ssa"
	},
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"traffictech.tasks.all"
# 	],
# 	"daily": [
# 		"traffictech.tasks.daily"
# 	],
# 	"hourly": [
# 		"traffictech.tasks.hourly"
# 	],
# 	"weekly": [
# 		"traffictech.tasks.weekly"
# 	],
# 	"monthly": [
# 		"traffictech.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "traffictech.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "traffictech.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "traffictech.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["traffictech.utils.before_request"]
# after_request = ["traffictech.utils.after_request"]

# Job Events
# ----------
# before_job = ["traffictech.utils.before_job"]
# after_job = ["traffictech.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"traffictech.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

fixtures = [
	{
		"doctype": "Custom Field",
		"filters": {
			"module": "Traffictech"
        }
    }
]
