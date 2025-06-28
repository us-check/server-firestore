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
        
        
def view_qr(request):
    if request.method == 'GET':
        return Response({"message": "QR 코드 뷰"})
    return Response({"error": "잘못된 요청"}, status=status.HTTP_400_BAD_REQUEST)


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
        business_image = data.get('image', None)
        business_contenttypeid = data.get('contenttypeid', None)
        business_contentid = uuid().hex[:8]  # UUID 생성 (예시로 8자리 사용)
        
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
            'image': business_image,
            'created_at': timezone.now().isoformat()
        })
        
        
        
        return Response({"message": "비즈니스 정보 저장 완료"}, status=status.HTTP_200_OK)
    return Response({"error": "잘못된 요청"}, status=status.HTTP_400_BAD_REQUEST)       
        
        
   

