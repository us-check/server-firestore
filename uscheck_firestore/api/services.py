import logging
import uuid
from typing import Dict
from django.conf import settings
import google.generativeai as genai
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
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
                
                # System Instructions 정의
                system_instruction = """
                당신은 경상북도 의성군 전문 ai 관광 어시스턴트입니다.
                
                핵심 임무:
                1. 의성군 관광정보 전문가로서 정확하고 유용한 정보 제공
                2. 사용자 쿼리를 정확히 분석하여 맞춤형 관광지 추천
                3. 의성군의 지역 특색을 반영한 개인화된 서비스 제공
                
                응답 원칙:
                - 항상 JSON 형태로 구조화된 응답 제공
                - 의성군의 문화적, 지리적 특성을 고려
                - 실용적이고 실행 가능한 정보만 제공
                - 사용자의 의도와 맥락을 정확히 파악
                - 
                ** 주의 사항 **:
                - 응답 개수: 반드시 15개 이상
                - contenttypeid 값이 39 인 item (음식점) : 반드시  3개 이상 포함
                - contenttypeid 값이 32 인 item (숙박시설): 반드시 전부 포함
                
                의성군 전문 지식:
                - 마늘, 양파 특산품과 관련 관광자원
                - 조문국 역사문화유적 (조문국사적지, 조문국박물관)
                - 자연관광지 (빙계계곡, 사촌역 은행나무길)
                - 전통문화시설 (의성향교, 의성관아)
                - 체험관광 프로그램 및 시설
                """
                
                # System Instructions와 함께 모델 초기화
                self.model = genai.GenerativeModel(
                    'gemini-2.5-flash',
                    system_instruction=system_instruction
                )
                logger.info("Gemini AI initialized successfully with system instructions")
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
                    'id': collection.to_dict().get('contentid', collection.id),  # contentid 사용, 없으면 문서 ID 사용
                    'name': collection.to_dict().get('title', ''),  # title을 name으로 사용
                    'overview': collection.to_dict().get('overview', ''),
                    'category': collection.to_dict().get('category', ''),
                } for collection in collections if collection.to_dict().get('contentid') or collection.id
            ]
            
            recommendation_result = self.recommend_tourism_spots(user_query, all_spots)

            full_spots = []
            for spot in recommendation_result.get('recommended_spots', []):
                try:
                    spot_id = spot.get('id', '')
                    if not spot_id:
                        logger.warning(f"Spot ID is empty, skipping: {spot}")
                        continue
                        
                    # contentid로 문서 찾기 (새로운 filter 방식 사용)
                    docs = db.collection('tour_list').where(filter=FieldFilter('contentid', '==', spot_id)).get()
                    
                    if docs:
                        # contentid로 찾은 경우
                        item = docs[0].to_dict()
                    else:
                        # 문서 ID로 직접 찾기
                        doc = db.collection('tour_list').document(spot_id).get()
                        if doc.exists:
                            item = doc.to_dict()
                        else:
                            logger.warning(f"Document not found for ID: {spot_id}")
                            continue
                    
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
                    logger.error(f"Error fetching full spot details for {spot.get('id', 'unknown')}: {e}")
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
            
            # Generation config 설정 (더 정확하고 일관된 응답을 위해)
            generation_config = genai.types.GenerationConfig(
                temperature=0.8,  #일관성 있는 응답 정도 (높을수록 자유도)
                top_p=0.8,
                top_k=40,
                max_output_tokens=10000,  # 토큰 수 줄임
                response_mime_type="text/plain"
            )
            
            # 안전성 설정 (필터링 완화)
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_ONLY_HIGH"
                }
            ]
            
            logger.info("🤖 Gemini AI 호출 중...")
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # 응답 상태 확인
            if not response.candidates:
                logger.error("❌ Gemini AI 응답에 후보가 없습니다")
                raise Exception("Gemini AI returned no candidates")
            
            candidate = response.candidates[0]
            finish_reason = candidate.finish_reason
            
            # finish_reason 확인 (0: FINISH_REASON_UNSPECIFIED, 1: FINISH_REASON_STOP, 2: FINISH_REASON_MAX_TOKENS, 3: FINISH_REASON_SAFETY, 4: FINISH_REASON_RECITATION)
            if finish_reason == 1:  # FINISH_REASON_STOP - 정상 완료
                logger.info(f"✅ Gemini AI 응답 받음: {response.text[:100]}...")
                response_text = response.text
            elif finish_reason == 2:  # FINISH_REASON_MAX_TOKENS
                logger.warning("⚠️ Gemini AI 응답이 최대 토큰 수에 도달했습니다")
                if candidate.content and candidate.content.parts:
                    response_text = candidate.content.parts[0].text
                else:
                    raise Exception("Response truncated due to max tokens but no content available")
            elif finish_reason == 3:  # FINISH_REASON_SAFETY
                logger.error("❌ Gemini AI 응답이 안전성 필터에 의해 차단되었습니다")
                raise Exception("Content blocked by safety filters")
            elif finish_reason == 4:  # FINISH_REASON_RECITATION
                logger.error("❌ Gemini AI 응답이 저작권 문제로 차단되었습니다")
                raise Exception("Content blocked due to recitation")
            else:
                logger.error(f"❌ 알 수 없는 finish_reason: {finish_reason}")
                raise Exception(f"Unknown finish reason: {finish_reason}")
                
            # 응답 파싱
            analysis_result = self._parse_analysis_response(response_text)
            
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
        # 간단하고 안전한 프롬프트
        prompt = f"""
사용자 관광 쿼리 분석:

입력: "{user_query}"

다음 JSON 형식으로 분석 결과를 제공해주세요:

{{
    "keywords": ["관련 키워드들"],
    "categories": ["관광지 유형"],
    "intent": "사용자 의도",
    "processed_query": "정제된 쿼리",
    "confidence": 0.8
}}

의성군 관광 카테고리:
- 문화재/유적지
- 자연관광지  
- 체험관광지
- 음식/맛집
- 숙박시설
- 레저/스포츠

반드시 15개 이상의 응답을 주세요.
        """
        
        return prompt
    
    def _parse_analysis_response(self, response_text: str) -> Dict:
        """AI 응답을 파싱하여 구조화된 데이터로 변환"""
        try:
            # JSON 부분 추출 (markdown 코드 블록 처리 포함)
            if '```json' in response_text:
                start_idx = response_text.find('```json') + 7
                end_idx = response_text.find('```', start_idx)
                json_str = response_text[start_idx:end_idx].strip()
            elif '```' in response_text:
                start_idx = response_text.find('```') + 3
                end_idx = response_text.find('```', start_idx)
                json_str = response_text[start_idx:end_idx].strip()
            else:
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                json_str = response_text[start_idx:end_idx] if start_idx != -1 and end_idx != -1 else response_text
            
            if json_str and json_str.startswith('{'):
                parsed_data = json.loads(json_str)
                
                # 기본 필드 검증 및 기본값 설정
                result = {
                    'keywords': parsed_data.get('keywords', []),
                    'categories': parsed_data.get('categories', []),
                    'preferences': parsed_data.get('preferences', []),
                    'intent': parsed_data.get('intent', 'general_search'),
                    'processed_query': parsed_data.get('processed_query', ''),
                    'confidence': float(parsed_data.get('confidence', 0.7))
                }
                
                # 데이터 품질 검증
                if not result['keywords']:
                    result['keywords'] = ['관광', '의성']
                if not result['processed_query']:
                    result['processed_query'] = response_text.strip()
                    
                return result
            else:
                raise json.JSONDecodeError("No valid JSON found", response_text, 0)
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse AI response as JSON: {e}")
            logger.warning(f"Response text: {response_text[:200]}...")
            
            # 폴백 분석 - 텍스트에서 키워드 추출 시도
            keywords = []
            text_lower = response_text.lower()
            
            # 의성군 관련 키워드 추출
            uiseong_keywords = ['마늘', '양파', '조문국', '빙계계곡', '사촌역', '은행나무', '향교', '관광', '맛집', '숙박']
            for keyword in uiseong_keywords:
                if keyword in text_lower:
                    keywords.append(keyword)
            
            return {
                'keywords': keywords if keywords else ['관광', '의성'],
                'categories': [],
                'preferences': [],
                'intent': 'general_search',
                'processed_query': response_text.strip()[:100],
                'confidence': 0.4
            }



        