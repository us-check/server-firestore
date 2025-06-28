import logging
import uuid
from typing import Dict
from django.conf import settings
import google.generativeai as genai
from google.cloud import firestore
from google.oauth2 import service_account
import os
import json

logger = logging.getLogger(__name__)

cred_path = os.environ.get("FIRESTORE_CREDENTIALS", "./gen-lang-client-0000121060-ea7b2bef1534.json")
credentials = service_account.Credentials.from_service_account_file(cred_path)
DATABASE = firestore.Client(credentials=credentials)

class GeminiService:
    def __init__(self):
        try:
            if settings.GEMINI_API_KEY:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                # 최신 Gemini 모델 사용 (gemini-pro 대신 gemini-1.5-flash 또는 gemini-1.5-pro)
                self.model = genai.GenerativeModel('gemini-2.5-flash')
                logger.info("Gemini AI initialized successfully with gemini-1.5-flash")
            else:
                logger.error("GEMINI_API_KEY not found in settings")
                self.model = None
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI: {e}")
            self.model = None
            
    def process_query(self, user_query):
        try:
            db = DATABASE
            collections = db.collection('tour_list').get()
            all_spots = [
                {
                    'id': collection.to_dict().get('id', ''),
                    'name': collection.to_dict().get('name', ''),
                    'overview': collection.to_dict().get('overview', ''),
                    'category': collection.to_dict().get('category', ''),
                } for collection in collections
            ]
            
            recommendation_result = self.recommend_tourism_spots(user_query, all_spots)

            full_spots = []
            for spot in recommendation_result.get('recommended_spots', []):
                try:
                    item = db.collection('tour_list').document(spot['id']).get().to_dict()
                    full_spots.append({
                        'addr1': item.get('addr1', ''),
                        'addr2': item.get('addr2', ''),
                        'areacode': item.get('areacode', ''),
                        'cat1': item.get('cat1', ''),
                        'cat2': item.get('cat2', ''),
                        'cat3': item.get('cat3', ''),
                        'contentid': item.get('contentid', ''),
                        'contenttypeid': item.get('contenttypeid', ''),
                        'createdtime': item.get('createdtime', ''),
                        'firstimage': item.get('firstimage', ''),
                        'firstimage2': item.get('firstimage2', ''),
                        'mapx': item.get('mapx', ''),
                        'mapy': item.get('mapy', ''),
                        'tel': item.get('tel', ''),
                        'title': item.get('title', ''),
                        'zipcode': item.get('zipcode', ''),
                        'overview': item.get('overview', ''),
                        'price': item.get('price', ''),
                    })
                except Exception as e:
                    logger.error(f"Error fetching full spot details for {spot['id']}: {e}")
                    continue
                
            recommendation_result['recommended_spots'] = full_spots
            
            response_data = {
                    'success': True,
                    'query': user_query,
                    'analysis': recommendation_result.get('analysis', {}),
                    'recommended_spots': recommendation_result.get('recommended_spots', []),
            }
            return response_data
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {'success': False, 'message': str(e)}

    def recommend_tourism_spots(self, user_query: str, all_spots: list, max_results: int = 30) -> Dict:
        """사용자 쿼리를 기반으로 관광지 추천"""
        try:
            # 1. 쿼리 분석
            analysis_result = self.analyze_user_query(user_query)
            
            if not analysis_result['success']:
                return analysis_result
            
            analysis = analysis_result['analysis']
            
            # 2. 간단한 키워드 매칭으로 관광지 추천
            recommended_spots = []
            keywords = analysis.get('keywords', [])
            
            for spot in all_spots:
                # 키워드가 이름이나 개요에 포함되어 있는지 확인
                spot_text = f"{spot.get('name', '')} {spot.get('overview', '')}".lower()
                for keyword in keywords:
                    if keyword.lower() in spot_text:
                        recommended_spots.append(spot)
                        break
            
            # 키워드 매칭이 없으면 전체 목록에서 일부만 반환
            if not recommended_spots:
                recommended_spots = all_spots[:max_results]
            
            # 결과 수 제한
            recommended_spots = recommended_spots[:max_results]
            
            return {
                'success': True,
                'query': user_query,
                'analysis': analysis,
                'recommended_spots': recommended_spots,
                'total_found': len(recommended_spots),
                'returned_count': len(recommended_spots)
            }
            
        except Exception as e:
            logger.error(f"Error recommending tourism spots: {e}")
            return {'success': False, 'message': str(e)}
    
    def analyze_user_query(self, user_query: str) -> Dict:
        """사용자 쿼리를 분석하여 관광지 검색 조건 추출"""
        try:
            # Gemini AI 상태 상세 로깅
            logger.info(f"=== Gemini AI 상태 확인 ===")
            logger.info(f"self.model 존재: {self.model is not None}")
            logger.info(f"GEMINI_API_KEY 설정: {bool(getattr(settings, 'GEMINI_API_KEY', None))}")
            
            # if not self.model:
            #     logger.warning("⚠️ Gemini AI not available, using fallback analysis")
            #     logger.warning("Gemini AI를 사용할 수 없어 폴백 분석을 사용합니다")
            #     return self._fallback_analysis(user_query)
            
            logger.info("✅ Gemini AI 사용 가능 - 실제 AI 분석 시작")
            
            # 의성군 관광지 정보를 기반으로 한 프롬프트 생성
            prompt = self._create_analysis_prompt(user_query)
            logger.info(f"Generated prompt length: {len(prompt)}")
            
            logger.info("🤖 Gemini AI 호출 중...")
            response = self.model.generate_content(prompt)
            logger.info(f"✅ Gemini AI 응답 받음: {response.text[:100]}...")
            
            # 응답 파싱
            analysis_result = self._parse_analysis_response(response.text)
            
            logger.info(f"Query analysis completed for: {user_query}")
            logger.info(f"Analysis result: {analysis_result}")
            
            return {
                'success': True,
                'original_query': user_query,
                'analysis': analysis_result,
                'processed_query': analysis_result.get('processed_query', user_query),
                'gemini_used': True  # Gemini가 실제로 사용되었음을 표시
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing user query with Gemini: {e}")
            import traceback
            logger.error(f"Gemini 오류 상세: {traceback.format_exc()}")
            return {
                'success': False,
                'message': str(e),
                'original_query': user_query,
                'analysis': {
                    'keywords': [],
                    'categories': [],
                    'preferences': [],
                    'intent': 'general_search',
                    'processed_query': user_query,
                    'confidence': 0.5
                },
                'gemini_used': False  # Gemini가 사용되지 않았음을 표시
            }
        
        
    def _create_analysis_prompt(self, user_query: str) -> str:

        """사용자 쿼리 분석을 위한 프롬프트 생성"""
        return f"""
        의성군 관광지 추천 시스템입니다. 사용자의 자연어 쿼리를 분석해주세요.

        사용자 쿼리: "{user_query}"

        다음 정보를 추출하여 JSON 형태로 반환해주세요:
        {{
            "keywords": ["추출된 키워드들"],
            "categories": ["관광지 카테고리들"],
            "preferences": ["사용자 선호사항들"],
            "intent": "사용자 의도",
            "processed_query": "정제된 검색 쿼리",
            "confidence": 0.0-1.0
        }}

        가능한 카테고리:
        - 문화재/유적지
        - 자연관광지
        - 체험관광지
        - 축제/이벤트
        - 음식/맛집
        - 숙박시설
        - 레저/스포츠

        의성군의 특색:
        - 마늘과 양파의 고장
        - 조문국 유적지
        - 빙계계곡
        - 사촌역 은행나무
        - 의성 조문국사적지
        """
    
    def _parse_analysis_response(self, response_text: str) -> Dict:
        """AI 응답을 파싱하여 구조화된 데이터로 변환"""
        try:
            # JSON 부분 추출
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # JSON 형태가 아닌 경우 기본값 반환
                return {
                    'keywords': [response_text.strip()],
                    'categories': [],
                    'preferences': [],
                    'intent': 'general_search',
                    'processed_query': response_text.strip(),
                    'confidence': 0.5
                }
                
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse AI response as JSON: {response_text}")
            return {
                'keywords': [],
                'categories': [],
                'preferences': [],
                'intent': 'unknown',
                'processed_query': response_text.strip(),
                'confidence': 0.3
            }



        