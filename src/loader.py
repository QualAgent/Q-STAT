import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

# 1. 환경 변수 로드 (.env 파일에서 DB 정보 가져오기)
load_dotenv()

USER = os.getenv("POSTGRES_USER", "myuser")
PASSWORD = os.getenv("POSTGRES_PASSWORD", "mypassword")
HOST = os.getenv("POSTGRES_HOST", "localhost")
PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "agent_db")

# 2. DB 연결 엔진 생성
db_url = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}?sslmode=require"

engine = create_engine(db_url)

def load_data_to_db(excel_file_path):
    print(f"엑셀 파일 로딩 중: {excel_file_path}")
    
    try:
        # 엑셀 파일 전체 읽기
        xls = pd.ExcelFile(excel_file_path)
        
        if 'MI' in xls.sheet_names:
            df_mi = pd.read_excel(xls, 'MI')
            # DB 적재 (replace: 기존 거 지우고 새로 씀 / append: 뒤에 추가)
            df_mi.to_sql('MI', engine, if_exists='replace', index=False)
            print(f"MI 적재 완료 ({len(df_mi)}건)")
        else:
            print("'MI' 시트가 없습니다.")

        if 'FDC' in xls.sheet_names:
            df_fdc = pd.read_excel(xls, 'FDC')
            df_fdc.to_sql('FDC', engine, if_exists='replace', index=False)
            print(f"FDC 적재 완료 ({len(df_fdc)}건)")
        else:
            print("'FDC' 시트가 없습니다.")

        if 'PM' in xls.sheet_names:
            df_pm = pd.read_excel(xls, 'PM')
            # 날짜 컬럼은 datetime 형식으로 변환해주는 게 안전함
            if 'date' in df_pm.columns:
                df_pm['date'] = pd.to_datetime(df_pm['date'])
                
            df_pm.to_sql('PM', engine, if_exists='replace', index=False)
            print(f"PM 적재 완료 ({len(df_pm)}건)")
        else:
            print("'PM' 시트가 없습니다.")

        if 'BOM' in xls.sheet_names:
            df_bom = pd.read_excel(xls, 'BOM')
            df_bom.to_sql('BOM', engine, if_exists='replace', index=False)
            print(f"BOM 적재 완료 ({len(df_bom)}건)")
        else:
            print("'BOM' 시트가 없습니다.")
            
        print("\n 모든 데이터 적재가 완료되었습니다!")

    except Exception as e:
        print(f"데이터 적재 중 오류 발생: {e}")

if __name__ == "__main__":
    file_path = "data/dummy_data/etch_process_data.xlsx" 
    if os.path.exists(file_path):
        load_data_to_db(file_path)
    else:
        print("파일 확인 필요")