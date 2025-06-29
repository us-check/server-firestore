from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
import logging
import uuid
from google.cloud import firestore
from .services import GeminiService
import json
import os
from google.cloud import pubsub_v1

PUBSUB_TOPIC = "qr-gen"  # 실제 생성한 Pub/Sub 
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0000121060")

logger = logging.getLogger(__name__)

@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
@csrf_exempt
def process_query(request):
    if request.method == 'POST':
        data = request.data
        user_query = data.get('query', '').strip()
        logger.info(f"쿼리: {user_query}")
        
        if not user_query:
            return Response({"error": "쿼리가 비어 있습니다."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            service = GeminiService()
            result = service.process_query(user_query)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"모델 초기화 실패: {e}")
            return Response({"error": "모델 초기화 실패"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)       

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def qr_generate_request(request):
    """QR 코드 생성 요청 (Pub/Sub 발행)"""
    if request.method == 'POST':
        data = request.data
        
        store_name = data.get('store', '').strip()
        store_price = data.get('price', '').strip()
        store_address = data.get('address', '').strip()
        store_overview = data.get('overview', '').strip()
        
        # 필수 데이터 검증
        if not store_name or not store_price or not store_address:
            return Response({
                "error": "store, price, address 필드가 필요합니다."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Pub/Sub 메시지 데이터 구성
            qr_data = {
                'store': store_name,
                'price': store_price,
                'timestamp': timezone.now().isoformat(),
                'request_id': uuid.uuid4().hex[:8],
                'original_data': f"{store_name}_{store_price}_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
            # Pub/Sub Publisher 클라이언트 생성
            publisher = pubsub_v1.PublisherClient()
            topic_path = publisher.topic_path(PROJECT_ID, PUBSUB_TOPIC)
            
            # 메시지 발행
            message_data = json.dumps(qr_data, ensure_ascii=False).encode('utf-8')
            future = publisher.publish(topic_path, message_data)
            message_id = future.result(timeout=30.0)
            
            logger.info(f"QR 생성 요청 발행 완료: {message_id}")
            
            return Response({
                "success": True,
                "message": "QR 코드 생성 요청이 처리되었습니다.",
                "request_id": qr_data['request_id'],
                "original_data": qr_data['original_data'],
                "message_id": message_id
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"QR 요청 처리 중 오류: {e}")
            return Response({
                "error": "QR 코드 생성 요청 처리에 실패했습니다."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        "error": "POST 메서드만 지원합니다."
    }, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
@csrf_exempt
def qr_get_url(request):
    """QR URL 조회"""
    if request.method == 'POST':
        data = request.data
        original_data = data.get('original_data')
    elif request.method == 'GET':
        original_data = request.GET.get('original_data')
    else:
        return Response({
            "error": "GET 또는 POST 메서드만 지원합니다."
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    if not original_data:
        return Response({
            "error": "original_data 파라미터가 필요합니다."
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Firestore에서 QR URL 조회
        db = firestore.Client()
        docs = db.collection('qr_results').where(
            'original_data', '==', original_data
        ).order_by(
            'created_at', direction=firestore.Query.DESCENDING
        ).limit(1).stream()
        
        qr_url = None
        for doc in docs:
            qr_url = doc.to_dict().get('qr_url')
            break
        
        if qr_url:
            return Response({
                "success": True,
                "qr_url": qr_url,
                "original_data": original_data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "error": "QR URL을 찾을 수 없습니다."
            }, status=status.HTTP_404_NOT_FOUND)
            
    except Exception as e:
        logger.error(f"QR URL 조회 중 오류: {e}")
        return Response({
            "error": "QR URL 조회 중 오류가 발생했습니다."
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
@api_view(['POST','GET'])
@permission_classes([AllowAny])
@csrf_exempt
def view_business(request):
    if request.method == 'POST':
        data = request.data
        business_name = data.get('name', '').strip()
        business_address = data.get('address', '').strip()
        business_price = data.get('price', '').strip()
        business_overview = data.get('overview', '').strip()
        business_contenttypeid = data.get('contenttypeid', None)
        business_contentid = uuid.uuid4().hex[:8]  # UUID 생성 (예시로 8자리 사용)
        
        if not (business_name and business_address and business_price):
            return Response({"error": "모든 필드를 입력해야 합니다."}, status=status.HTTP_400_BAD_REQUEST)
        
        # 비즈니스 정보 저장 로직 (예: 데이터베이스에 저장)
        db = firestore.Client()
        doc_ref = db.collection('businesses').document()
        doc_ref.set({
            'name': business_name,
            'address': business_address,
            'price': business_price,
            'overview': business_overview,
            'created_at': timezone.now().isoformat()
        })
        
        
        
        return Response({"message": "비즈니스 정보 저장 완료"}, status=status.HTTP_200_OK)
    return Response({"error": "잘못된 요청"}, status=status.HTTP_400_BAD_REQUEST)       
        
        
   

