import frappe
import cv2
import numpy as np
import base64
import re
import requests
import json

def base64_to_image(base64_string):
	"""Convert base64 string to OpenCV image"""
	image_data = re.sub('^data:image/.+;base64,', '', base64_string)
	image_bytes = base64.b64decode(image_data)
	image_np = np.frombuffer(image_bytes, dtype=np.uint8)
	return cv2.imdecode(image_np, cv2.IMREAD_COLOR)

def image_to_base64(image):
	"""Convert OpenCV image to base64 string"""
	if image is None or not image.any():  # Ensure image is valid
		return None

	_, buffer = cv2.imencode('.jpg', image)
	return base64.b64encode(buffer).decode('utf-8')

def overlay_edges(image):
	"""Overlay detected edges in yellow with increased thickness and draw circles at corners"""
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	blurred = cv2.GaussianBlur(gray, (5, 5), 0)
	edged = cv2.Canny(blurred, 50, 150)

	kernel = np.ones((3, 3), np.uint8)
	edged = cv2.dilate(edged, kernel, iterations=2)

	edges_colored = np.zeros_like(image)
	edges_colored[edged > 0] = (0, 255, 255)

	overlay = cv2.addWeighted(image, 0.6, edges_colored, 0.9, 0)
	return overlay


def get_document_contour(image):
	"""Detect the largest quadrilateral contour"""
	if image is None or not image.any():  # Ensure image is valid
		return None

	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	blurred = cv2.GaussianBlur(gray, (5, 5), 0)
	edged = cv2.Canny(blurred, 40, 200)

	contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	if not contours:
		return None

	# Sort by area, keep largest
	contours = sorted(contours, key=cv2.contourArea, reverse=True)
	
	for contour in contours:
		peri = cv2.arcLength(contour, True)
		approx = cv2.approxPolyDP(contour, 0.02 * peri, True)

		if len(approx) == 4:  # We found a quadrilateral
			return approx

	return None

def perspective_transform(image, contour):
	"""Perform a perspective transform to get a top-down view"""
	pts = contour.reshape(4, 2)

	rect = np.zeros((4, 2), dtype="float32")
	s = pts.sum(axis=1)
	rect[0] = pts[np.argmin(s)]  # Top-left
	rect[2] = pts[np.argmax(s)]  # Bottom-right

	diff = np.diff(pts, axis=1)
	rect[1] = pts[np.argmin(diff)]  # Top-right
	rect[3] = pts[np.argmax(diff)]  # Bottom-left

	(tl, tr, br, bl) = rect

	# Compute width & height of the new image
	widthA = np.linalg.norm(br - bl)
	widthB = np.linalg.norm(tr - tl)
	maxWidth = int(max(widthA, widthB))

	heightA = np.linalg.norm(tr - br)
	heightB = np.linalg.norm(tl - bl)
	maxHeight = int(max(heightA, heightB))

	dst = np.array([
		[0, 0],
		[maxWidth - 1, 0],
		[maxWidth - 1, maxHeight - 1],
		[0, maxHeight - 1]
	], dtype="float32")

	M = cv2.getPerspectiveTransform(rect, dst)
	warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))

	return warped


@frappe.whitelist()
def live_edges():
	"""Process real-time video frame to detect edges with overlay"""
	data = json.loads(frappe.request.data)
	image_base64 = data.get('image')

	if not image_base64:
		frappe.response["http_status_code"] = 400
		return {'error': 'No image provided'}

	image = base64_to_image(image_base64)
	processed_image = overlay_edges(image)
	processed_base64 = image_to_base64(processed_image)

	return {'processed_image': processed_base64}

def order_points(contour):
	"""Sort contour points in correct order: top-left, top-right, bottom-right, bottom-left"""
	pts = contour.reshape(4, 2)

	rect = np.zeros((4, 2), dtype="float32")
	s = pts.sum(axis=1)
	rect[0] = pts[np.argmin(s)]  # Top-left
	rect[2] = pts[np.argmax(s)]  # Bottom-right

	diff = np.diff(pts, axis=1)
	rect[1] = pts[np.argmin(diff)]  # Top-right
	rect[3] = pts[np.argmax(diff)]  # Bottom-left

	return rect

@frappe.whitelist()
def capture(image):
	"""Process captured frame and crop document accurately"""
	image_base64 = image

	if not image_base64:
		frappe.response["http_status_code"] = 400
		return {'error': 'No image provided'}

	image = base64_to_image(image_base64)
	contour = get_document_contour(image)

	if contour is not None and len(contour) >= 4:
		sorted_contour = order_points(contour)  # Ensure points are ordered
		cropped_image = perspective_transform(image, sorted_contour)
	else:
		cropped_image = image  # Return original if no document is found

	cropped_base64 = image_to_base64(cropped_image)
	return {'cropped_image': cropped_base64}

@frappe.whitelist()
def contour_video(image):
	"""Process real-time video frame to detect and overlay the document contour"""
	image_base64 = image

	if not image_base64:
		frappe.response["http_status_code"] = 400
		return {'error': 'No image provided'}

	image = base64_to_image(image_base64)
	
	# Detect document contour
	contour = get_document_contour(image)
	
	# Draw contour on the image
	if contour is not None:
		cv2.drawContours(image, [contour], -1, (0, 255, 0), 3)  # Green contour

	processed_base64 = image_to_base64(image)
	return {'processed_image': processed_base64}


@frappe.whitelist()
def live_edges(image_base64):
	"""Process real-time video frame to detect edges with overlay"""
	if not image_base64:
		return {"error": "No image provided"}
	
	image = base64_to_image(image_base64)
	processed_image = overlay_edges(image)
	processed_base64 = image_to_base64(processed_image)
	
	return {"processed_image": processed_base64}

@frappe.whitelist()
def upload_images(images, frm):
	images = json.loads(images)
	"""Upload and save images in Frappe File manager"""
	if not images:
		return {"message": "No images received"}, 400
	
	saved_files = []

	for img in images:
		image_data = img.split(",")[1]
		image_bytes = base64.b64decode(image_data)

		file_doc = frappe.get_doc({
			"doctype": "File",
			"file_name": "uploaded_image_pce.jpg",
			"content": image_bytes,
			"is_private": 0
		})
		file_doc.insert(ignore_permissions=True)

		saved_files.append(file_doc.file_url)

	return {"message": "Images saved successfully!", "files": saved_files}
