import json
import os
from google.cloud import firestore
from django.conf import settings
from google.oauth2 import service_account
from django.core.management.base import BaseCommand


cred_path = os.environ.get("FIRESTORE_CREDENTIALS", "./gen-lang-client-0000121060-ea7b2bef1534.json")
credentials = service_account.Credentials.from_service_account_file(cred_path)
DATABASE = firestore.Client(credentials=credentials)
def upload_json_to_firestore():
    """JSON 파일의 데이터를 Firestore에 업로드"""
    try:
        # Firestore 클라이언트 초기화
        db = firestore.Client()
        
        # JSON 파일 읽기
        json_file_path = os.path.join(os.path.dirname(__file__), 'uscheck_firestore', 'us_tourdata_final.txt')
        
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # JSON 구조에서 관광지 데이터 추출
        tour_items = data['response']['body']['items']['item']
        
        # tour_list 컬렉션에 데이터 업로드
        collection_ref = db.collection('tour_list')
        
        upload_count = 0
        for item in tour_items:
            try:
                # contentid를 문서 ID로 사용
                doc_id = item.get('contentid', '')
                
                if not doc_id:
                    print(f"contentid가 없는 항목 건너뜀: {item.get('title', 'Unknown')}")
                    continue
                
                # 필요한 필드들 정리
                tour_data = {
                    'id': doc_id,  # AI 추천에서 사용할 ID
                    'name': item.get('title', ''),  # AI 추천에서 사용할 이름
                    'title': item.get('title', ''),
                    'overview': item.get('overview', ''),
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
                    'zipcode': item.get('zipcode', ''),
                    'modifiedtime': item.get('modifiedtime', ''),
                    'sigungucode': item.get('sigungucode', ''),
                    'cpyrhtDivCd': item.get('cpyrhtDivCd', ''),
                    'mlevel': item.get('mlevel', ''),
                    'category': get_category_name(item.get('cat1', '')),  # AI 추천에서 사용할 카테고리
                }
                
                # Firestore에 문서 추가
                collection_ref.document(doc_id).set(tour_data)
                upload_count += 1
                print(f"업로드 완료: {tour_data['title']} (ID: {doc_id})")
                
            except Exception as e:
                print(f"개별 항목 업로드 실패: {item.get('title', 'Unknown')} - {e}")
                continue
        
        print(f"\n총 {upload_count}개의 관광지 데이터가 Firestore에 업로드되었습니다.")
        return True
        
    except Exception as e:
        print(f"Firestore 업로드 중 오류 발생: {e}")
        return False

def get_category_name(cat1_code):
    """카테고리 코드를 이름으로 변환"""
    category_map = {
        'A01': '자연',
        'A02': '인문(문화/예술/역사)',
        'A03': '레포츠',
        'A04': '쇼핑',
        'A05': '음식',
        'B02': '숙박',
        'C01': '추천코스',
    }
    return category_map.get(cat1_code, '기타')

if __name__ == "__main__":
    # 환경 변수 설정 (실제 경로로 변경 필요)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r'C:\Users\JHSHIN\ProgrammingCodes\us-check-firestore\uscheck_firestore\gen-lang-client-0000121060-ea7b2bef1534.json'
    
    success = upload_json_to_firestore()
    if success:
        print("데이터 업로드가 성공적으로 완료되었습니다!")
    else:
        print("데이터 업로드 중 오류가 발생했습니다.")