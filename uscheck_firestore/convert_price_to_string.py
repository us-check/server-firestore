#!/usr/bin/env python3
"""
us_tourdata_final.txt 파일의 모든 price 값을 정수에서 문자열로 변환하는 스크립트
"""
import json

def convert_prices_to_string():
    """JSON 파일의 모든 price 값을 문자열로 변환"""
    file_path = 'us_tourdata_final.txt'
    
    try:
        # 파일 읽기
        print("📖 파일 읽기 중...")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        items = data['response']['body']['items']['item']
        converted_count = 0
        
        # 각 아이템의 price를 문자열로 변환
        for i, item in enumerate(items):
            if 'price' in item:
                original_price = item['price']
                # 정수를 문자열로 변환
                item['price'] = str(original_price)
                converted_count += 1
                
                # 진행 상황 출력 (10개마다)
                if (i + 1) % 10 == 0:
                    title = item.get('title', 'N/A')
                    print(f"⏳ 진행률: {i + 1}/{len(items)} - {title}: {original_price} → '{item['price']}'")
        
        # 파일 저장
        print("\n💾 파일 저장 중...")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        print(f"\n✅ 변환 완료!")
        print(f"📊 총 {len(items)}개 항목 중 {converted_count}개의 price 값을 문자열로 변환했습니다.")
        
        # 샘플 확인
        print(f"\n🔍 변환 결과 샘플:")
        for i in range(min(5, len(items))):
            item = items[i]
            if 'price' in item:
                title = item.get('title', f'항목 {i+1}')
                price = item['price']
                price_type = type(price).__name__
                print(f"   - {title}: '{price}' (타입: {price_type})")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("🔄 Price 값을 정수에서 문자열로 변환")
    print("=" * 50)
    convert_prices_to_string()
