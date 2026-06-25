from io import BytesIO
import cv2
import numpy as np
from zipfile import ZipFile
import uvicorn
from fastapi import FastAPI, UploadFile
from fastapi.responses import StreamingResponse
from ultralytics import YOLO


app = FastAPI()


@app.get("/")
def root():
    return {"message": "OK"}

yolo_detect = YOLO()


@app.post('/detect')
def yolo_detect_people(archive: UploadFile) -> StreamingResponse: 

    """
    Processes a ZIP archive of images using a YOLO model.

    Each image inside the archive is decoded and passed through the YOLO detector.
    Only images containing detected persons (confidence > 0.5) are kept.
    Bounding boxes are drawn only for the "person" class.

    Parameters
    ----------
    archive : UploadFile
        Input ZIP archive containing images (jpg/png)

    Returns
    -------
    StreamingResponse
        ZIP archive with processed images where only persons are detected and annotated
    """
    
    contents = archive.file.read() 
    zip_file = ZipFile(BytesIO(contents))

    output_zip = BytesIO()

    with ZipFile(output_zip, "w") as zip_out:

        for info in zip_file.infolist():
            if not info.is_dir():
                with zip_file.open(info.filename) as file:
                
                    image_bytes = file.read()
                    nparr = np.frombuffer(image_bytes, np.uint8)
                    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                    result = yolo_detect(image)[0]

                    has_person = False
                    annotated = image.copy()

                    for box in result.boxes:
                        cls_id = int(box.cls[0])
                        conf = float(box.conf[0])

                        if cls_id == 0 and conf > 0.5:

                            x1, y1, x2, y2 = map(int, box.xyxy[0])

                            cv2.rectangle(
                                annotated,
                                (x1, y1),
                                (x2, y2),
                                (255, 0, 0),  # синій
                                2
                            )

                            cv2.putText(
                            annotated,
                            f"person {conf:.2f}",
                            (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (255, 155, 0),
                            2,
                            cv2.LINE_AA  
                        )

                            if not has_person:
                                has_person = True
                    
                    if has_person:
                        
                        _, buffer = cv2.imencode(".jpg", annotated)
                                    
                        zip_out.writestr(
                            info.filename,
                            buffer.tobytes()
                        )
    output_zip.seek(0)

    return StreamingResponse(
        output_zip,
        media_type="application/zip",
        headers={
    "Content-Disposition": "attachment; filename=processed.zip"
        }
    )


if __name__ == "__main__":
    uvicorn.run('main:app')
