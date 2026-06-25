# Overview

This project implements a simple computer vision API using FastAPI and a YOLO object detection model.

The API accepts a ZIP archive containing images, processes each image with YOLO, and detects people in the images. Only images containing at least one detected person with confidence greater than 0.5 are included in the output. Detected persons are highlighted with bounding boxes and confidence scores.

The processed images are returned to the user as a new ZIP archive.

## Deployment Info

The solution is deployed as a REST API using FastAPI.

The API loads a YOLO object detection model when the application starts and exposes HTTP endpoints for interaction. Users can send requests containing image archives, and the server processes them and returns the results.

The application is started using FastAPI:

```bash
fastapi dev main.py
```

By default, the server runs locally and can be accessed through:

* `http://127.0.0.1:8000` – application root endpoint;
* `http://127.0.0.1:8000/docs` – automatically generated API documentation (Swagger UI).

## Installation

1. Clone the repository:

```bash
git clone <repository_url>
cd <repository_name>
```

2. Create a virtual environment:

```bash
python -m venv .venv
```

3. Activate the virtual environment:

Windows

```bash
.venv\Scripts\activate
```

4. Install the required packages:

```bash
pip install -r requirements.txt
```

5. Start the application:

```bash
fastapi dev main.py
```

6. Open the API documentation:

```text
http://127.0.0.1:8000/docs
```

## Modeling Info

The solution uses a YOLO object detection model provided by the Ultralytics library.

For each image in the input archive, the model performs object detection and returns bounding boxes, class labels, and confidence scores for detected objects.

The application filters detections to keep only the **person** class with a confidence score greater than **0.5**. Images containing at least one valid person detection are annotated with bounding boxes and confidence scores and included in the output archive.

Images without detected persons are excluded from the output.

## Interface Description

### GET `/`

**Description:**
Health check endpoint used to verify that the server is running.

**Input:**
None

**Output:**

```json
{
  "message": "OK"
}
```

---

### POST `/detect`

**Description:**
Processes a ZIP archive of images using a YOLO object detection model. The model detects objects in each image and keeps only images containing at least one detected person (confidence > 0.5). Detected persons are highlighted with bounding boxes and confidence scores.

**Input:**

* `archive` (UploadFile): ZIP archive containing image files 

**Output:**

* `StreamingResponse` (ZIP archive)

The returned ZIP archive contains only images where at least one person was detected. Each image is annotated with bounding boxes and confidence scores for the detected persons.

