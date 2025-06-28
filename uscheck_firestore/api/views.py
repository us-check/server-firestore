from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
import logging

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


def view_business(request):
    if request.method == 'GET':
        return Response({"message": "비즈니스 뷰"})
    return Response({"error": "잘못된 요청"}, status=status.HTTP_400_BAD_REQUEST)       
        
        

