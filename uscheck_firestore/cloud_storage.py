import qrcode
import tempfile
import time
import json
from google.cloud import storage
from markupsafe import escape
import base64

BUCKET_NAME = "qr_bucket111"
BUCKET_URL = f"https://storage.googleapis.com/{BUCKET_NAME}/"

def generate_qr_http(request):
    request_json = request.get_json()
    if not request_json:
        return {"error": "No JSON data provided"}, 400

    qr_data = json.dumps(request_json, ensure_ascii=False)
    qr_img = qrcode.make(qr_data)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"qr_{timestamp}.png"
    temp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    qr_img.save(temp.name)

    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_filename(temp.name, content_type="image/png")
    temp.close()
    blob.make_public()

    return {"result": "success", "qr_url": BUCKET_URL + filename}, 200

def generate_qr_pubsub(event, context):
    if 'data' not in event:
        return
    message = base64.b64decode(event['data']).decode('utf-8')
    data = json.loads(message)

    qr_data = json.dumps(data, ensure_ascii=False)
    qr_img = qrcode.make(qr_data)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"qr_{timestamp}.png"
    temp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    qr_img.save(temp.name)

    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_filename(temp.name, content_type="image/png")
    temp.close()
    blob.make_public()

    print({"result": "success", "qr_url": BUCKET_URL + filename})
