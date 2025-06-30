# Copyright (c) 2025, Niyaz Razak and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, today
from erpnext.setup.utils import get_exchange_rate
from erpnext.controllers.accounts_controller import get_default_taxes_and_charges


class Estimation(Document):
	def validate(self):
		self.calcualte_totals()
		self.validate_and_remove_items()

	def on_submit(self):
		if not self.items:
			frappe.throw("Please add the items!")

	def calcualte_totals(self):
		self.total_qty = 0
		self.total_amount = 0

		for row in self.items:
			self.total_qty += flt(row.get("qty"))
			self.total_amount += flt(row.get("total"))

	@frappe.whitelist()
	def create_quotation(self):
		quotation = frappe.new_doc("Quotation")
		quotation.quotation_to = self.party_type
		quotation.party_name = self.party
		quotation.currency = self.currency
		company_currency = frappe.get_cached_value("Company", quotation.company, "default_currency")

		if company_currency == quotation.currency:
			exchange_rate = 1
		else:
			exchange_rate = get_exchange_rate(
				quotation.currency, company_currency, quotation.transaction_date, args="for_selling"
			)

		quotation.conversion_rate = exchange_rate

		for item in self.items:
			self.create_item_price(item.get("item_code"),  flt(item.get("rate")))
			quotation.append("items", {
				"item_code": item.get("item_code"),
				"item_name": item.get("item_name"),
				"uom": item.get("unit"),
				"qty": item.get("qty"),  
				"rate": flt(item.get("rate")),
				"price_list_rate": 0,  # force it not to fetch price list rate
				"discount_percentage": 0,
				"group": item.group,
				"estimation_item": item.name,
				"estimation": self.name,
			})

		taxes = get_default_taxes_and_charges("Sales Taxes and Charges Template", company=quotation.company)
		if taxes.get("taxes"):
			quotation.update(taxes)

		quotation.run_method("set_missing_values")
		quotation.run_method("calculate_taxes_and_totals")
		quotation.insert(ignore_permissions=True, ignore_mandatory=True)

		return quotation.as_dict()

	def create_item_price(self, item_code, rate):
		price_list = "Standard Selling"
		# Check if an Item Price already exists
		existing = frappe.get_all("Item Price", filters={
			"item_code": item_code,
			"price_list": price_list
		})

		if existing:
			item_price = frappe.get_doc("Item Price", existing[0].name)
			item_price.price_list_rate = rate
			item_price.save(ignore_permissions=True)
		else:
			item_price = frappe.get_doc({
				"doctype": "Item Price",
				"item_code": item_code,
				"price_list": price_list,
				"price_list_rate": rate
			})
			item_price.insert(ignore_permissions=True)


	@frappe.whitelist()
	def add_items(self, items=[], group=None):
		if not self.items:
			for item in items:
				self.append("items", {
					"item_code": item.get("item_code"),
					"unit": item.get("uom"),
					"qty": item.get("qty"),  
					"list_price": item.get("list_price"),
					"logistic_percent": item.get("logistic_percent"),
					"logistic_amount": item.get("logistic_amount"),
					"total_cost": item.get("total_cost"),
					"installation_cost": item.get("installation_cost"),
					"profit_percent": item.get("profit_percent"),
					"profit_amount": item.get("profit_amount"),
					"unit_price": item.get("unit_price"),
					"rate": item.get("unit_price"),
					"total": item.get("total"),
					"internal_remarks": item.get("internal_remarks"),
					"external_remarks": item.get("external_remarks"),
					"group": group,
				})
			return

		for item in items:
			matched = False
			for row in self.items:
				if row.name == item.get("row_name") and row.group == group:
					row.item_code = item.get("item_code")
					row.unit = item.get("uom")
					row.qty = item.get("qty")
					row.list_price = item.get("list_price")
					row.logistic_percent = item.get("logistic_percent")
					row.logistic_amount = item.get("logistic_amount")
					row.total_cost = item.get("total_cost")
					row.installation_cost = item.get("installation_cost")
					row.profit_percent = item.get("profit_percent")
					row.profit_amount = item.get("profit_amount")
					row.unit_price = item.get("unit_price")
					row.rate = item.get("unit_price")
					row.total = item.get("total")
					row.internal_remarks = item.get("internal_remarks")
					row.external_remarks = item.get("external_remarks")
					
					matched = True
					break

			if not matched:
				self.append("items", {
					"item_code": item.get("item_code"),
					"unit": item.get("uom"),
					"qty": item.get("qty"),  
					"list_price": item.get("list_price"),
					"logistic_percent": item.get("logistic_percent"),
					"logistic_amount": item.get("logistic_amount"),
					"total_cost": item.get("total_cost"),
					"installation_cost": item.get("installation_cost"),
					"profit_percent": item.get("profit_percent"),
					"profit_amount": item.get("profit_amount"),
					"unit_price": item.get("unit_price"),
					"rate": item.get("unit_price"),
					"total": item.get("total"),
					"internal_remarks": item.get("internal_remarks"),
					"external_remarks": item.get("external_remarks"),
					"group": group,
				})

	def get_groups(self):
		grp_wise = {}
		for grp in self.groups:
			grp_wise.setdefault(grp.description, 0)
			grp_wise[grp.description] += 1
		
		return grp_wise

	def validate_and_remove_items(self):
		grp_wise = self.get_groups()
		for row in self.items:
			if (row.group not in list(grp_wise.keys())):
				self.items.remove(row)
