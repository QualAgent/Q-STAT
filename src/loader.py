import pandas as pd
from sqlalchemy import create_engine, text
import os

# 1. DB 접속 (환경변수 사용)
db_user = os.getenv("POSTGRES_USER")
db_password = os.getenv("POSTGRES_PASSWORD")
db_host = os.getenv("POSTGRES_HOST")
db_name = os.getenv("POSTGRES_DB")
db_url = f"postgresql://{db_user}:{db_password}@{db_host}:5432/{db_name}"
engine = create_engine(db_url)

def upload_normalized_data():
    print("[Start] 정규화 데이터 적재 시작")

    upload_list = [

        ("products.xlsx", "products", "product_id"), 
        ("equipment.xlsx", "equipment", "eq_id"),
        
        # 2. 자식 테이블 (로그, 이력 등)
        # 자식은 부모가 들어간 뒤에 넣어야 안전함
        ("defect_logs.xlsx", "defect_logs", None), 
    ]

    try:
        with engine.connect() as conn:
            for file_name, table_name, pk_col in upload_list:
                print(f"\n 처리 중: {file_name} -> 테이블: {table_name}")
                
                # 1. 파일 읽기
                file_path = f"/app/src/{file_name}"
                df = pd.read_excel(file_path) # csv면 read_csv로 변경
                
                # 2. 데이터 넣기 (일단 덮어쓰기)
                print(f"데이터 {len(df)}건 업로드 중...")
                df.to_sql(name=table_name, con=engine, if_exists='replace', index=False)
                
                # 3. [고급] Primary Key(기본키) 설정해주기
                # Pandas to_sql은 기본키 설정을 안 해줍니다. 그래서 SQL로 직접 지정해줘야 진짜 RDB답게 씁니다.
                if pk_col:
                    print(f"Primary Key 설정 ({pk_col})...")
                    conn.execute(text(f"ALTER TABLE {table_name} ADD PRIMARY KEY ({pk_col});"))
                    conn.commit()
                    
        print("\n [Success] 모든 정규화 데이터 적재 완료!")

    except Exception as e:
        print(f"\n [Error] 문제가 발생했습니다: {e}")

if __name__ == "__main__":
    upload_normalized_data()