import React, { useEffect, useRef, useState, useCallback } from "react";
import { Stage, Layer, Image, Line, Circle, Group, Rect } from "react-konva";


function App({ form, onImagesUploaded, liveDetection }) {
	const liveDetectionEnabled = Number(liveDetection);
	const videoRef = useRef(null);
	const canvasRef = useRef(null);
	const [contourFrame, setContourFrame] = useState(null);

	const [isCameraOn, setIsCameraOn] = useState(false);
	const [capturedImage, setCapturedImage] = useState(null);
	const [imageElement, setImageElement] = useState(null);
	const [croppedImages, setCroppedImages] = useState([]);

	const [cropping, setCropping] = useState(false);

	const [lensPosition, setLensPosition] = useState(null);
	const [lensVisible, setLensVisible] = useState(false);
	const [cropperSize, setCropperSize] = useState({ width: 400, height: 600 });

	const [cropPoints, setCropPoints] = useState([
		{ x: 15, y: 15 },
		{ x: cropperSize.width-15, y: 15 },
		{ x: cropperSize.width-15, y: cropperSize.height-15 },
		{ x: 15, y: cropperSize.height-15 }
	]);

	useEffect(() => {
		if (isCameraOn) {
			startCamera();
		}
	}, [isCameraOn]);

	useEffect(() => {
		if (capturedImage) {
			const img = new window.Image();
			img.src = capturedImage;
			img.onload = () => setImageElement(img);
		}
	}, [capturedImage]);

	useEffect(() => {
		const updateCropperSize = () => {
			if (window.innerWidth < 768) {  
				// Mobile devices
				setCropperSize(
					{
						width: window.innerWidth * 0.8,
						height: window.innerHeight * 0.6
					}
				);
			} else {  
				// Laptops & larger screens
				setCropperSize({ width: 400, height: 600 });
			}
		};

		updateCropperSize();
		window.addEventListener("resize", updateCropperSize);
		return () => window.removeEventListener("resize", updateCropperSize);
	}, []);

	const startCamera = async () => {
		try {
			const stream = await navigator.mediaDevices.getUserMedia({
				video: { 
					facingMode: { exact: "environment" },
					width: { ideal: 1920 },
					height: { ideal: 1080 },
				},
				
			});
	
			if (videoRef.current) {
				videoRef.current.srcObject = stream;
				videoRef.current.onloadedmetadata = () => {
					videoRef.current.play();
					processContourFrame();
				};
			}
		} catch (error) {
			console.error("Error accessing the camera:", error);
			if (error.name === "OverconstrainedError") {
				try {
					const fallbackStream = await navigator.mediaDevices.getUserMedia({
						video: { facingMode: "environment" }
					});
					if (videoRef.current) {
						videoRef.current.srcObject = fallbackStream;
						videoRef.current.onloadedmetadata = () => {
							videoRef.current.play();
							processContourFrame();
						};
					}
				} catch (fallbackError) {
					console.error("Fallback error accessing camera:", fallbackError);
				}
			}
		}
	};


	//  For Live Detection
	const isProcessingRef = useRef(false); // Track if an API request is in progress

	const processContourFrame = () => {
		if (!liveDetectionEnabled) return;
		if (!videoRef.current || !canvasRef.current) return;
	
		const canvas = canvasRef.current;
		const video = videoRef.current;
		const context = canvas.getContext("2d");
	
		canvas.width = video.videoWidth;
		canvas.height = video.videoHeight;
	
		const sendFrame = async () => {
			if (!videoRef.current || !canvasRef.current || isProcessingRef.current) {
				requestAnimationFrame(sendFrame); // No delay, runs on each frame
				return;
			}
	
			isProcessingRef.current = true; // Mark request as in-progress
	
			context.drawImage(video, 0, 0, canvas.width, canvas.height);
			const imageData = canvas.toDataURL("image/jpeg");
	
			try {
				frappe.call({
					method: "traffictech.api.scanner.contour_video",
					args: { image: imageData },
					callback: async function (r) {
						setContourFrame(`data:image/jpeg;base64,${r.message.processed_image}`);
						isProcessingRef.current = false; // Mark request as completed
					},
				});
			} catch (error) {
				console.error("Error processing contour frame:", error);
				isProcessingRef.current = false;
			}
	
			// Continue processing frames without delay
			requestAnimationFrame(sendFrame);
		};
	
		sendFrame(); // Start the loop
	};


	const captureAndCrop = async () => {
		const canvas = canvasRef.current;
		const video = videoRef.current;
		const context = canvas.getContext("2d");

		canvas.width = video.videoWidth;
		canvas.height = video.videoHeight;

		context.drawImage(video, 0, 0, canvas.width, canvas.height);
		const imageData = canvas.toDataURL("image/jpeg");
		try {
			frappe.call({
				method: 'traffictech.api.scanner.capture',
				args: {
					image: imageData
				},
				callback: async function (r) {
					setCroppedImages((prev) => [...prev, `data:image/jpeg;base64,${r.message.cropped_image}`]);
				}
			})
		} catch (error) {
			console.error("Error capturing and cropping image:", error);
		}
	};

	const handleRemove = (index) => {
		setCroppedImages(croppedImages.filter((_, i) => i !== index));
	};

	const handleRotate = (index) => {
		const img = document.createElement("img");
		img.src = croppedImages[index];

		img.onload = () => {
			const canvas = document.createElement("canvas");
			const ctx = canvas.getContext("2d");

			// Set canvas dimensions for rotation (swap width & height for 90° rotation)
			canvas.width = img.height;
			canvas.height = img.width;

			// Rotate the image
			ctx.translate(canvas.width / 2, canvas.height / 2);
			ctx.rotate(90 * Math.PI / 180); // Rotate 90 degrees
			ctx.drawImage(img, -img.width / 2, -img.height / 2);

			// Get the rotated image data
			const rotatedImageData = canvas.toDataURL("image/jpeg");

			// Update state with the rotated image
			setCroppedImages((prevImages) =>
				prevImages.map((img, i) => (i === index ? rotatedImageData : img))
			);
		};
	};

	const handleSendImages = async () => {
		if (croppedImages.length === 0) {
			alert("No images to send!");
			return;
		}

		try {
			frappe.call({
				method: 'traffictech.api.scanner.upload_images',
				args: {
					images: croppedImages,
					frm: form
				},
				callback: async function (r) {
					setCroppedImages([]);
					if (onImagesUploaded) {
						onImagesUploaded(r.message);
					}

				}
			})
		} catch (error) {
			console.error("Error sending images:", error);
			alert("Failed to send images!");
		}
	};

	const captureOriginalPhoto = async () => {
		if (!videoRef.current) return;
	
		const video = videoRef.current;
		const videoWidth = video.videoWidth;
		const videoHeight = video.videoHeight;
	
		console.log(`Video Resolution: ${videoWidth}x${videoHeight}`);
	
		// **Capture in Maximum Resolution**
		// const scaleFactor = Math.max(12, window.devicePixelRatio * 4); // Increase for HD
		const canvas = document.createElement("canvas");
		canvas.width = videoWidth;
		canvas.height = videoHeight;
	
		const ctx = canvas.getContext("2d");
	
		// **Disable smoothing for pixel-perfect capture**
		ctx.imageSmoothingEnabled = false;
		ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
		
		const image  = canvas.toDataURL("image/png", 1.0);
		setCapturedImage(image);
		setCropping(true);

		// **Define precise crop points**
		setCropPoints([
			{ x: 15, y: 15 },
			{ x: cropperSize.width - 15, y: 15 },
			{ x: cropperSize.width - 15, y: cropperSize.height - 15 },
			{ x: 15, y: cropperSize.height - 15 }
		]);
		// **Save as PNG (lossless quality)**
		// canvas.toBlob(
		// 	(blob) => {
		// 		const reader = new FileReader();
		// 		reader.readAsDataURL(blob);
		// 		reader.onloadend = () => {
		// 			setCapturedImage(reader.result);
		// 			setCropping(true);
	
		// 			// **Define precise crop points**
		// 			setCropPoints([
		// 				{ x: 15, y: 15 },
		// 				{ x: cropperSize.width - 15, y: 15 },
		// 				{ x: cropperSize.width - 15, y: cropperSize.height - 15 },
		// 				{ x: 15, y: cropperSize.height - 15 }
		// 			]);
		// 		};
		// 	},
		// 	"image/png",
		// 	1.0 // Maximum quality
		// );
	};
	
	const cropImage = () => {
		if (!capturedImage) return;
	
		const img = new window.Image();
		img.src = capturedImage;
	
		img.onload = () => {
			const canvas = document.createElement("canvas");
			const ctx = canvas.getContext("2d", { willReadFrequently: true });
	
			const imgWidth = img.width;  // Full-resolution width
			const imgHeight = img.height; // Full-resolution height
	
			// **Scale crop points to match full resolution**
			const xs = cropPoints.map(p => Math.round((p.x / cropperSize.width) * imgWidth));
			const ys = cropPoints.map(p => Math.round((p.y / cropperSize.height) * imgHeight));
			const minX = Math.min(...xs);
			const minY = Math.min(...ys);
			const maxX = Math.max(...xs);
			const maxY = Math.max(...ys);
	
			// **Ensure crop dimensions remain within bounds**
			const cropX = Math.max(0, minX);
			const cropY = Math.max(0, minY);
			const cropWidth = Math.min(imgWidth, maxX - minX);
			const cropHeight = Math.min(imgHeight, maxY - minY);
	
			// **Set canvas size to crop size**
			canvas.width = cropWidth;
			canvas.height = cropHeight;
	
			// **Disable smoothing for sharp cropping**
			ctx.imageSmoothingEnabled = false;
	
			// **Draw the cropped region**
			ctx.drawImage(img, cropX, cropY, cropWidth, cropHeight, 0, 0, cropWidth, cropHeight);
	
			// **Save cropped image in lossless quality**
			canvas.toBlob(
				(blob) => {
					const reader = new FileReader();
					reader.readAsDataURL(blob);
					reader.onloadend = () => {
						setCroppedImages([...croppedImages, reader.result]);
					};
				},
				"image/png", // PNG is lossless
				1.0 // Maximum quality
			);
	
			setCropping(false);
			setCapturedImage(null);
		};
	
		img.onerror = (err) => {
			console.error("Failed to load image for cropping:", err);
		};
	};
	
	
	
	
	return (
		<div className="dialog_container bg-white">
			<div className="camera-section" style={{ position: "relative", display: "inline-block" }}>
				{liveDetectionEnabled ? (
					// Live Scanner
					<div className="live_scanner">
						<video
							ref={videoRef}
							autoPlay
							playsInline
							style={{ display: "none", width: "200px", height: "300px", maxWidth: "100%", maxHeight: "90vh" }}
						/>
						<canvas ref={canvasRef} style={{ display: "none" }}></canvas>
						{contourFrame ? (
							<img
							src={contourFrame}
							alt="Contour Detection"
							style={{ width: "200px", height: "300px", border: "2px solid black", objectFit: "cover" }}
							/>
						) : (
							<div
							style={{ width: "200px", height: "300px", backgroundColor: "black", color: "white", display: "flex", alignItems: "center", justifyContent: "center" }}
							>
							Processing...
							</div>
						)}
						<div style={{ marginTop: "10px", textAlign: "left" }}>
							{!isCameraOn && (
							<button className="btn btn-primary" onClick={() => setIsCameraOn(true)} style={{ marginBottom: "5px" }}>
								Start
							</button>
							)}
							{isCameraOn && (
							<>
								<button className="cpt-button btn btn-primary" onClick={captureAndCrop}>Capture</button>
								<button className="cpt-button btn btn-primary" onClick={captureOriginalPhoto} style={{ marginLeft: "2px" }}>Take Original Photo</button>
							</>
							)}
						</div>
					</div>
				) : (
					// Normal Scanner
					<div className="normal_scanner">
						<div style={{ display: "flex" }}>
							<div>
								<video
								className="camera"
								ref={videoRef}
								autoPlay
								playsInline
								style={{  maxWidth: "100%", maxHeight: "60vh", border: "2px solid black", objectFit: "cover" }}
								/>

								{!isCameraOn && (
									<div style={{ marginTop: "10px", textAlign: "center" }}>
										<button className="cpt-button btn btn-primary" onClick={() => setIsCameraOn((prev) => !prev)}>Start</button>
									</div>
								)}
								{isCameraOn && (
									<div style={{ marginTop: "10px", textAlign: "center" }}>
										<button className="cpt-button btn btn-primary" onClick={captureOriginalPhoto}>Capture & Crop</button>
									</div>
								)}
							</div>
						</div>
						<canvas ref={canvasRef} style={{ display: "none" }}></canvas>
						
						{/* Cropping Modal */}
						{cropping && (
							<div style={{
								position: "fixed",
								top: "8%",
								left: "50%",
								transform: "translateX(-50%)",
								width: "auto",
								maxWidth: "90vw",
								background: "#fff",
								padding: "20px",
								borderRadius: "10px",
								zIndex: 1000,
								boxShadow: "0px 4px 10px rgba(0,0,0,0.2)",
							}}>
								<h4>Adjust Image</h4>
								{imageElement && (
									<Stage width={cropperSize.width} height={cropperSize.height}>
										<Layer>
											<Image image={imageElement} width={cropperSize.width} height={cropperSize.height} />
											<Line points={cropPoints.flatMap((p) => [p.x, p.y])} stroke="yellow" closed />
											{cropPoints.map((point, index) => (
												<Circle
													key={index}
													x={point.x}
													y={point.y}
													radius={10}
													fill="yellow"
													draggable
													onDragStart={() => setLensVisible(true)}
													onDragMove={(e) => {
														const newPoints = [...cropPoints];
														const newX = Math.max(0, Math.min(e.target.x(), cropperSize.width)); // Constrain X within 0 to 200
														const newY = Math.max(0, Math.min(e.target.y(), cropperSize.height)); // Constrain Y within 0 to 300
													
														newPoints[index] = { x: newX, y: newY };
														setCropPoints(newPoints);
														setLensPosition({ x: newX, y: newY });
													}}
													onDragEnd={() => setLensVisible(false)}
												/>
											))}
					
											{/* Lens Effect */}
											{lensVisible && lensPosition && (
												<Group 
													x={Math.max(10, Math.min(lensPosition.x + 20, 160))}  // Ensures lens stays inside width
													y={Math.max(10, Math.min(lensPosition.y - 50, 250))}  // Ensures lens stays inside height
												>
													<Rect width={40} height={40} fill="white" opacity={0.8} />
													<Image
														image={imageElement}
														crop={{
															x: Math.max(0, Math.min(lensPosition.x * (imageElement.width / cropperSize.width) - 10, imageElement.width - 20)),
															y: Math.max(0, Math.min(lensPosition.y * (imageElement.height / cropperSize.height) - 10, imageElement.height - 20)),
															width: 20,
															height: 20,
														}}
														width={40}
														height={40}
													/>
													<Rect width={40} height={40} stroke="white" strokeWidth={1} />
												</Group>
											)}
										</Layer>
									</Stage>
								)}
								<div className="mt-2 d-flex justify-content-between">
									<button className="cpt-button btn btn-primary" onClick={() => setCropping(false)}>Cancel</button>
									<button className="cpt-button btn btn-primary" onClick={cropImage}>Add</button>
								</div>
								
							</div>
						)}
					   
					</div>
				)}
			</div>
			
			<div className="image-section p-2">
				{croppedImages.length !== 0 && (
					<div>
						<h6>Captured Images</h6>
						<div className="row captured-images">
							{croppedImages.map((value, i) => (
								<div key={i} className="mt-3 position-relative m-2">
									<div >
										<img src={value} alt="Cropped"/>

										{/* Rotate Button */}
										<button
											className="position-absolute btn btn-primary"
											style={{ bottom: "2px", left: "20px", fontSize: "10px" }}
											onClick={() => handleRotate(i)}
										>
											Rotate
										</button>

										{/* Remove Button */}
										<button
											className="position-absolute btn btn-danger"
											style={{ bottom: "2px", right: "20px", fontSize: "10px"}}
											onClick={() => handleRemove(i)}
										>
											Remove
										</button>
									</div>
								</div>
							))}
						</div>
						<button
							className="btn btn-primary my-5"
							onClick={handleSendImages}
						>
							Attach
						</button>
					</div>
				)}
			</div>
		</div>
	);
}

export default App;