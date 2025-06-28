import qrcode
import tempfile
import time
import json
import os
from google.cloud import storage
from google.cloud import firestore
from markupsafe import escape
import base64

BUCKET_NAME = "us-check-bucket"
BUCKET_URL = f"https://storage.googleapis.com/{BUCKET_NAME}/"

def generate_qr_http(request):
    request_json = request.get_json()
    if not request_json:
        return {"error": "No JSON data provided"}, 400

    qr_string = str(request_json.get("store", ""))
    if not qr_string:
        return {"error": "No 'store' field provided"}, 400

    qr_img = qrcode.make(qr_string)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"qr_{timestamp}.png"
    temp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    qr_img.save(temp.name)

    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_filename(temp.name, content_type="image/png")
    temp.close()
    os.unlink(temp.name)
    blob.make_public()

    return {"result": "success", "qr_url": BUCKET_URL + filename}, 200

def save_qr_url_to_firestore(qr_url, original_data):
    db = firestore.Client()
    doc_ref = db.collection("qr_results").document()
    doc_ref.set({
        "qr_url": qr_url,
        "original_data": original_data,
        "created_at": firestore.SERVER_TIMESTAMP
    })

def generate_qr_pubsub(event, context):
    if 'data' not in event:
        print("[PubSub][오류] event['data']가 없음")
        return
    try:
        message = base64.b64decode(event['data']).decode('utf-8')
        print("[PubSub] 디코딩된 메시지:", message)
        print("[PubSub] message(repr):", repr(message)) 

        qr_string = message
        if not qr_string:
            print("[PubSub][오류] 값이 없음")
            return

        qr_img = qrcode.make(qr_string)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"qr_{timestamp}.png"
        temp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        qr_img.save(temp.name)

        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_filename(temp.name, content_type="image/png")
        temp.close()
        os.unlink(temp.name)
        blob.make_public()

        qr_url = BUCKET_URL + filename
        save_qr_url_to_firestore(qr_url, qr_string)
        print({"result": "success", "qr_url": qr_url})
    except Exception as e:
        import sys, traceback
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("[PubSub][오류] 예외 발생:", exc_type, exc_value)
        print("[PubSub][오류] Exception message:", str(e))
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)

