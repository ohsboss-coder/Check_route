import streamlit as st
import pandas as pd
import requests
import io
import math

# --- [여기에 아까 발급받은 키를 꼭 넣으셔야 작동합니다] ---
NAVER_CLIENT_ID = "appix3et7d"
NAVER_CLIENT_SECRET = "fcwb4iLEeen2UzjBHHDYBBO8PICDxhlbtUosH0Ol"

def get_coords(address):
    url = f"https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode?query={address}"
    headers = {"X-NCP-APIGW-API-KEY-ID": NAVER_CLIENT_ID, "X-NCP-APIGW-API-KEY": NAVER_CLIENT_SECRET}
    try:
        res = requests.get(url, headers=headers).json()
        if 'addresses' in res and res['addresses']:
            return float(res['addresses'][0]['x']), float(res['addresses'][0]['y'])
    except: return None
    return None

def calculate_distance(p1, p2):
    if p1 and p2:
        return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
    return float('inf')

st.title("🚗 전국 현장점검 최적 동선 생성기")
uploaded_file = st.file_uploader("11조 원본 엑셀을 올려주세요", type=['xlsx'])
start_address = st.text_input("출발지 (예: 완주군청)", "전라북도 완주군청")

if uploaded_file and st.button("🚀 진짜 최적 일정표 만들기"):
    df = pd.read_excel(uploaded_file)
    # 주소 컬럼 찾기
    addr_col = [c for c in df.columns if '주소' in c or '소재지' in c][0]
    
    with st.spinner("네이버 지도로 71개 업체의 위치를 분석 중..."):
        start_coords = get_coords(start_address)
        df['coords'] = df[addr_col].apply(get_coords)
        
        # 최단거리 정렬 로직 (Greedy)
        ordered_data = []
        current_coords = start_coords
        remaining_df = df.copy()
        
        while not remaining_df.empty:
            remaining_df['dist'] = remaining_df['coords'].apply(lambda x: calculate_distance(current_coords, x))
            closest_idx = remaining_df['dist'].idxmin()
            closest_row = remaining_df.loc[closest_idx]
            ordered_data.append(closest_row)
            current_coords = closest_row['coords']
            remaining_df = remaining_df.drop(closest_idx)
            
        result_df = pd.DataFrame(ordered_data)
        
        # 7개씩 끊어서 날짜와 방문순서 부여
        result_df['방문순서'] = range(1, len(result_df) + 1)
        result_df['방문예정일'] = result_df['방문순서'].apply(lambda x: f"{(x-1)//7 + 1}일차")
        result_df['일일순번'] = result_df['방문순서'].apply(lambda x: (x-1)%7 + 1)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            result_df.drop(columns=['coords', 'dist']).to_excel(writer, index=False, sheet_name='최적점검동선')
        
        st.success("네이버 지도 분석 완료! 이제 진짜 동선이 짜여졌습니다.")
        st.download_button("📥 최적화된 일정표 다운로드", output.getvalue(), "최적점검일정_최종.xlsx")
