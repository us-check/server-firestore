#!/usr/bin/env python3
"""
us_tourdata_final.txt 파일의 모든 아이템에 price 필드를 추가하는 스크립트
"""
import json
import os

def get_price_by_category_and_title(item):
    """카테고리와 제목을 기반으로 가격을 결정"""
    cat1 = item.get('cat1', '')
    contenttypeid = item.get('contenttypeid', '')
    title = item.get('title', '')
    overview = item.get('overview', '')
    
    # 숙박시설 (contenttypeid: 32, cat1: B02)
    if contenttypeid == '32' or cat1 == 'B02':
        if '고택' in title or '한옥' in title or 'Quality' in title:
            return 120000
        else:
            return 80000
    
    # 음식점 (contenttypeid: 39, cat1: A05)
    elif contenttypeid == '39' or cat1 == 'A05':
        if '한정식' in title or '갈비' in title:
            return 25000
        elif '햄버거' in title or '레스토랑' in title:
            return 18000
        else:
            return 15000
    
    # 축제/행사 (contenttypeid: 15, cat1: A02의 일부)
    elif contenttypeid == '15':
        if '축제' in title or '행사' in title:
            return 5000
        else:
            return 3000
    
    # 문화시설/박물관 (contenttypeid: 14)
    elif contenttypeid == '14':
        if '박물관' in title or '문학관' in title:
            return 3000
        elif '문화원' in title or '문화회관' in title:
            return 2000
        else:
            return 1000
    
    # 레포츠/체험 (contenttypeid: 28, cat1: A03)
    elif contenttypeid == '28' or cat1 == 'A03':
        if '야영장' in title or '캠핑' in title:
            return 25000
        elif '컬링' in title or 'CC' in title:
            return 30000
        else:
            return 20000
    
    # 쇼핑 (contenttypeid: 38, cat1: A04)
    elif contenttypeid == '38' or cat1 == 'A04':
        return 0  # 시장이나 쇼핑 장소는 입장료 무료
    
    # 관광지 (contenttypeid: 12, cat1: A01, A02)
    elif contenttypeid == '12':
        # 사찰, 서원, 향교 등은 무료
        if any(keyword in title for keyword in ['사', '서원', '향교', '정사', '당']):
            return 0
        # 자연관광지
        elif cat1 == 'A01':
            if '휴양림' in title or '생태' in title:
                return 3000
            else:
                return 0  # 산, 계곡 등은 무료
        # 역사문화관광지
        elif cat1 == 'A02':
            if '체험' in title or '마을' in title:
                return 5000
            elif '온천' in title:
                return 8000
            else:
                return 0
        else:
            return 0
    
    # 기본값 (overview만 있는 경우)
    else:
        if '맛집' in overview:
            return 20000
        elif '축제' in overview or '행사' in overview:
            return 5000
        elif '체험' in overview:
            return 10000
        elif '고택' in overview or '한옥' in overview:
            return 100000
        elif '명소' in overview:
            return 0
        else:
            return 0

def add_prices_to_json():
    """JSON 파일의 모든 아이템에 price 필드 추가"""
    file_path = 'us_tourdata_final.txt'
    
    # 파일 읽기
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    items = data['response']['body']['items']['item']
    
    # 각 아이템에 price 추가
    for i, item in enumerate(items):
        price = get_price_by_category_and_title(item)
        item['price'] = price
        
        # 진행 상황 출력
        title = item.get('title', 'N/A')
        print(f"{i+1:2d}. {title[:30]:30s} : {price:,}원")
    
    # 파일 저장
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print(f"\n✅ 완료! 총 {len(items)}개 항목에 가격이 추가되었습니다.")
    
    # 통계 출력
    price_stats = {}
    for item in items:
        price = item['price']
        if price not in price_stats:
            price_stats[price] = 0
        price_stats[price] += 1
    
    print("\n📊 가격별 통계:")
    for price in sorted(price_stats.keys()):
        count = price_stats[price]
        print(f"   {price:,}원: {count}개")

if __name__ == '__main__':
    print("🏛️  의성군 관광 데이터에 가격 정보 추가")
    print("=" * 50)
    add_prices_to_json()
