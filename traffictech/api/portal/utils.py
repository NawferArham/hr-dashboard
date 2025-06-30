# Copyright (c) 2025, Teciza Solutions and contributors
# For license information, please see license.txt

import frappe
import cv2
import numpy as np
import tensorflow as tf
from mtcnn import MTCNN
import os
import base64
import time

def get_current_employee_info(usernmae) -> dict:
	current_user = usernmae
	employee = frappe.db.get_value(
		"Employee",
		{"user_id": current_user, "status": "Active"},
		[
			"name",
			"first_name",
			"employee_name",
			"designation",
			"department",
			"company",
			"reports_to",
			"user_id",
			"date_of_birth",
			"date_of_joining",
			"employment_type",
			"branch",
			"grade",
			"company_email",
			"personal_email",
			"cell_number",
			"ctc",
			"payroll_cost_center",
			"salary_mode",
			"bank_name",
			"custom_employee_bank_short_name",
			"bank_ac_no",
			"iban",
			"image"
		],
		as_dict=True,
	)
	if not employee:
		return {
			"success": False,
			"error": "Employee not found"
		}

	if employee and employee.get("reports_to"):
		employee['reports_to_name'] = frappe.db.get_value("Employee", employee.get("reports_to"), "employee_name")
	if employee.get("image"):
		file_url = employee.get("image")
		file_name = frappe.get_value("File", {"file_url": file_url}, "file_name")
		file_is_private = file_url.startswith("/private/files/")
		full_path = frappe.utils.get_files_path(file_name, is_private=file_is_private)

		file = open(full_path, 'rb')
		try:
			file_content = file.read()
		finally:
			file.close()

		employee['image_base64'] = base64.b64encode(file_content).decode('utf-8')

	return {
		"success": True,
		"data": employee
	}


def load_tflite_model(model_path='facenet.tflite'):
	"""Load the TFLite FaceNet model."""
	interpreter = tf.lite.Interpreter(model_path=model_path)
	interpreter.allocate_tensors()
	return interpreter

def extract_face(image, required_size=(160, 160)):
	"""Extract a single face from an image using MTCNN."""
	detector = MTCNN()
	results = detector.detect_faces(image)
	if len(results) == 0:
		return None
	
	x1, y1, width, height = results[0]['box']
	x1, y1 = max(0, x1), max(0, y1)
	x2, y2 = x1 + width, y1 + height

	face = image[y1:y2, x1:x2]
	face = cv2.resize(face, required_size)
	face = face.astype('float32') / 255.0  # Normalize pixel values
	return face

def get_face_embedding_tflite(interpreter, face):
	"""Get the 128-dimensional embedding from the face image using TFLite model."""
	input_details = interpreter.get_input_details()
	output_details = interpreter.get_output_details()
	face = np.expand_dims(face, axis=0).astype('float32')
	interpreter.set_tensor(input_details[0]['index'], face)
	interpreter.invoke()
	embedding = interpreter.get_tensor(output_details[0]['index'])[0]
	return embedding

def calculate_distance(embedding1, embedding2):
	"""Calculate the Euclidean distance between two embeddings."""
	distance = np.linalg.norm(embedding1 - embedding2)
	return distance

def compare_faces_tflite(image_path1, image_path2, model_path='facenet.tflite', threshold=10):
	"""Compare two face images and return True if they match, False otherwise."""
	
	interpreter = load_tflite_model(model_path)
	
	image1 = cv2.imread(image_path1)
	image2 = cv2.imread(image_path2)
	
	# Convert BGR to RGB
	image1 = cv2.cvtColor(image1, cv2.COLOR_BGR2RGB)
	image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2RGB)
	
	face1 = extract_face(image1)
	face2 = extract_face(image2)
	
	if face1 is None or face2 is None:
		return False

	embedding1 = get_face_embedding_tflite(interpreter, face1)
	embedding2 = get_face_embedding_tflite(interpreter, face2)
	distance = calculate_distance(embedding1, embedding2)

	return distance < threshold

def is_recognized(user_image_path, current_image_path):
	try:
		model_path = os.path.join(frappe.get_app_path('teciza'), 'assets', 'facenet.tflite')
		result = compare_faces_tflite(user_image_path, current_image_path, model_path=model_path, threshold=0.6)
		if result:
			return True
		else:
			return False
	except Exception as e:
		return False

def save_base64_to_file(base64_string: str, file_extension: str = 'jpg') -> str:
	try:
		if not base64_string:
			raise ValueError("Base64 string is required.")
		padding = len(base64_string) % 4
		if padding != 0:
			base64_string += '=' * (4 - padding)
		file_data = base64.b64decode(base64_string)
		timestamp = int(time.time())
		file_name = f'img_recognition_{timestamp}.{file_extension}'
		file_path = frappe.get_site_path('private', 'files', file_name)
		with open(file_path, 'wb') as f:
			f.write(file_data)
		return file_path
	except Exception as e:
		frappe.log_error(f"Error in saving Base64 file: {str(e)}", "Base64 to File Error")
		raise e

def get_attendance_for_calendar(employee: str, from_date: str, to_date: str) -> list[dict[str, str]]:
	attendance = frappe.get_all(
		"Attendance",
		{"employee": employee, "attendance_date": ["between", [from_date, to_date]]},
		["attendance_date", "status", "working_hours", "in_time", "out_time"],
	)
	return { d["attendance_date"]: {
		"status": d["status"],
		"hours": d["working_hours"],
		"in_time": d["in_time"],
		"out_time": d["out_time"],
	} for d in attendance}

def get_holidays_for_calendar(employee: str, from_date: str, to_date: str) -> list[str]:
	from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee

	if holiday_list := get_holiday_list_for_employee(employee, raise_exception=False):
		return frappe.get_all(
			"Holiday",
			filters={"parent": holiday_list, "holiday_date": ["between", [from_date, to_date]]},
			pluck="holiday_date",
		)

	return []