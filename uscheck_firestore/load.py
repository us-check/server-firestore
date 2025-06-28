#!/usr/bin/env python3
"""
us_tourdata_final.txt 파일의 데이터를 Firestore에 추가 로드하는 스크립트
(기존 데이터 유지, 새로운 데이터만 추가)
"""
import os
import sys
import json
import django
from datetime import datetime
from google.cloud import firestore as firestore

# Django 설정
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'uscheck_firestore.settings')
django.setup()

from django.conf import settings

def load_additional_data_to_firestore():
    """us_tourdata_final.txt 데이터를 Firestore에 추가 로드 (기존 데이터 유지)"""
    try:
        # Firestore 클라이언트 가져오기
        db = firestore.Client()
        
        if not db:
            print("❌ Firestore 클라이언트가 초기화되지 않았습니다.")
            return
        
        # us_tourdata_final.txt 파일 읽기
        txt_file_path = 'us_tourdata_final.txt'
        
        if not os.path.exists(txt_file_path):
            print(f"❌ 파일을 찾을 수 없습니다: {txt_file_path}")
            return
        
        print(f"📖 파일 읽기 시작: {txt_file_path}")
        
        with open(txt_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 데이터 구조 확인
        items = data['response']['body']['items']['item']
        total_count = len(items)
        
        print(f"📊 총 {total_count}개 항목 발견")
        print(f"🎯 Firestore 컬렉션: uiseong_tourism")
        print(f"📋 프로젝트: {settings.FIRESTORE_PROJECT_ID}")
        print(f"📋 데이터베이스: {settings.FIRESTORE_DATABASE_ID}")
        
        # Firestore 컬렉션 참조
        collection_ref = db.collection('tour_list')
        
        # 기존 데이터 확인
        existing_docs = list(collection_ref.stream())
        existing_content_ids = set()
        
        if existing_docs:
            print(f"🔍 기존 {len(existing_docs)}개 문서가 존재합니다.")
            for doc in existing_docs:
                doc_data = doc.to_dict()
                content_id = doc_data.get('contentid')
                if content_id:
                    existing_content_ids.add(content_id)
            print(f"📝 기존 contentid {len(existing_content_ids)}개 확인")
        else:
            print("📋 기존 데이터가 없습니다. 모든 데이터를 새로 추가합니다.")
        
        # 데이터 로드
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for i, item in enumerate(items, 1):
            try:
                content_id = item.get('contentid', f'item_{i}')
                
                # 기존 데이터 존재 여부 확인
                if content_id in existing_content_ids:
                    skip_count += 1
                    if i % 10 == 0:
                        print(f"⏭️  항목 {i} 건너뜀 (이미 존재): {item.get('title', 'N/A')}")
                    continue
                
                # 문서 ID로 사용
                doc_id = content_id
                
                # 카테고리 매핑
                category = get_category_name(item.get('contenttypeid', ''))
                
                # 좌표 변환
                latitude = float(item.get('mapy', 0)) if item.get('mapy') else None
                longitude = float(item.get('mapx', 0)) if item.get('mapx') else None
                
                # 태그 생성
                tags = []
                if item.get('tel'):
                    tags.append('연락처있음')
                if item.get('firstimage'):
                    tags.append('이미지있음')
                if item.get('cpyrhtDivCd'):
                    tags.append('저작권표시')
                
                # 지역 정보 추가
                tags.append('의성군')
                tags.append('경상북도')
                
                # 분류별 태그 추가
                if item.get('cat1') == 'A01':
                    tags.append('자연')
                elif item.get('cat1') == 'A02':
                    tags.append('인문')
                elif item.get('cat1') == 'A03':
                    tags.append('레포츠')
                elif item.get('cat1') == 'A04':
                    tags.append('쇼핑')
                elif item.get('cat1') == 'A05':
                    tags.append('음식')
                elif item.get('cat1') == 'B02':
                    tags.append('숙박')
                
                # Firestore 문서 데이터 구성
                doc_data = {
                    # 기본 정보
                    'title': item.get('title', '').strip(),
                    'category': category,
                    'addr1': item.get('addr1', '').strip(),
                    'addr2': item.get('addr2', '').strip(),
                    'overview': item.get('overview', '').strip(),
                    'price': item.get('price', '').strip(),
                    # 연락처
                    'tel': item.get('tel', '').strip(),
                    
                    # 이미지
                    'firstimage': item.get('firstimage', '').strip(),
                    'firstimage2': item.get('firstimage2', '').strip(),
                    
                    # 위치 정보
                    'latitude': latitude,
                    'longitude': longitude,
                    'mapx': item.get('mapx', '').strip(),
                    'mapy': item.get('mapy', '').strip(),
                    
                    # 분류 정보
                    'contentid': item.get('contentid', '').strip(),
                    'contenttypeid': item.get('contenttypeid', '').strip(),
                    'areacode': item.get('areacode', '').strip(),
                    'sigungucode': item.get('sigungucode', '').strip(),
                    
                    # 카테고리 정보
                    'cat1': item.get('cat1', '').strip(),
                    'cat2': item.get('cat2', '').strip(),
                    'cat3': item.get('cat3', '').strip(),
                    
                    # 새로운 분류 시스템
                    'lDongRegnCd': item.get('lDongRegnCd', '').strip(),
                    'lDongSignguCd': item.get('lDongSignguCd', '').strip(),
                    'lclsSystm1': item.get('lclsSystm1', '').strip(),
                    'lclsSystm2': item.get('lclsSystm2', '').strip(),
                    'lclsSystm3': item.get('lclsSystm3', '').strip(),
                    
                    # 저작권 정보
                    'cpyrhtDivCd': item.get('cpyrhtDivCd', '').strip(),
                    
                    # 기타 정보
                    'zipcode': item.get('zipcode', '').strip(),
                    'mlevel': item.get('mlevel', '').strip(),
                    'readcount': 0,
                    
                    # 시간 정보
                    'createdtime': item.get('createdtime', '').strip(),
                    'modifiedtime': item.get('modifiedtime', '').strip(),
                    
                    # 메타데이터
                    'tags': tags,
                    'source': 'us_tourdata_final.txt',
                    'region': '의성군',
                    'province': '경상북도',
                    'loaded_at': datetime.now().isoformat(),
                    
                    # 검색용 키워드 (제목을 공백으로 분리)
                    'search_keywords': item.get('title', '').replace('(', ' ').replace(')', ' ').replace('[', ' ').replace(']', ' ').split(),
                }
                
                # 빈 값 제거
                doc_data = {k: v for k, v in doc_data.items() if v is not None and v != '' and v != []}
                
                # Firestore에 저장
                collection_ref.document(doc_id).set(doc_data)
                
                success_count += 1
                print(f"✅ 새로 추가: {item.get('title', 'N/A')}")
                
                if i % 10 == 0:
                    print(f"⏳ 진행률: {i}/{total_count} ({i/total_count*100:.1f}%) - 추가: {success_count}, 건너뜀: {skip_count}")
                
            except Exception as e:
                error_count += 1
                print(f"❌ 항목 {i} 저장 실패: {e}")
                print(f"   제목: {item.get('title', 'N/A')}")
                continue
        
        print(f"\n🎉 의성군 관광 데이터 추가 로드 완료!")
        print(f"✅ 새로 추가: {success_count}개")
        print(f"⏭️  기존 데이터 건너뜀: {skip_count}개")
        print(f"❌ 실패: {error_count}개")
        print(f"📊 총 처리: {total_count}개")
        print(f"🗂️  최종 데이터베이스 예상 크기: {len(existing_content_ids) + success_count}개")
        
        # 새로 추가된 데이터 통계 정보 출력
        if success_count > 0:
            print(f"\n📈 새로 추가된 데이터 통계:")
            category_stats = {}
            for item in items:
                content_id = item.get('contentid')
                if content_id not in existing_content_ids:
                    cat = get_category_name(item.get('contenttypeid', ''))
                    category_stats[cat] = category_stats.get(cat, 0) + 1
            
            for category, count in sorted(category_stats.items()):
                print(f"   {category}: {count}개")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

def get_category_name(contenttypeid):
    """contenttypeid를 카테고리명으로 변환"""
    category_map = {
        '12': '관광지',
        '14': '문화시설', 
        '15': '축제공연행사',
        '28': '레포츠',
        '32': '숙박',
        '38': '쇼핑',
        '39': '음식점'
    }
    
    return category_map.get(contenttypeid, '일반')

if __name__ == '__main__':
    print("🏛️  의성군 관광 데이터 Firestore 추가 업로드")
    print("📝 기존 데이터는 유지하고 새로운 데이터만 추가합니다")
    print("=" * 60)
    load_additional_data_to_firestore()