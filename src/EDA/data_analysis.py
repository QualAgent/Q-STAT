import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sqlalchemy import create_engine, inspect
import os
from dotenv import load_dotenv

# ── DB 연결 ──────────────────────────────────────────────
load_dotenv()

USER = os.getenv("POSTGRES_USER", "myuser")
PASSWORD = os.getenv("POSTGRES_PASSWORD", "mypassword")
HOST = os.getenv("POSTGRES_HOST", "localhost")
PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "agent_db")

db_url = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}?sslmode=require"
engine = create_engine(db_url)


# ── 유틸 함수 ────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_table_names():
    """DB에 존재하는 테이블 목록 조회"""
    insp = inspect(engine)
    return insp.get_table_names()


@st.cache_data(ttl=300)
def load_table(_table_name: str) -> pd.DataFrame:
    """테이블 전체 데이터를 DataFrame으로 로드"""
    return pd.read_sql_table(_table_name, engine)


def show_basic_info(df: pd.DataFrame):
    """기본 정보: shape, dtypes, 결측치"""
    col1, col2, col3 = st.columns(3)
    col1.metric("Rows", f"{len(df):,}")
    col2.metric("Columns", f"{len(df.columns)}")
    col3.metric("Missing Cells", f"{df.isna().sum().sum():,}")

    st.markdown("#### Column 정보")
    info_df = pd.DataFrame({
        "dtype": df.dtypes.astype(str),
        "non_null": df.notna().sum(),
        "null": df.isna().sum(),
        "null_%": (df.isna().mean() * 100).round(2),
        "unique": df.nunique(),
    })
    st.dataframe(info_df, use_container_width=True)


def show_statistics(df: pd.DataFrame):
    """수치형 컬럼 기술통계"""
    numeric_df = df.select_dtypes(include="number")
    if numeric_df.empty:
        st.info("수치형 컬럼이 없습니다.")
        return
    st.dataframe(numeric_df.describe().T, use_container_width=True)


def show_missing_heatmap(df: pd.DataFrame):
    """결측치 히트맵"""
    missing = df.isna().sum()
    missing = missing[missing > 0]
    if missing.empty:
        st.success("결측치가 없습니다.")
        return

    fig, ax = plt.subplots(figsize=(10, max(3, len(missing) * 0.4)))
    ax.barh(missing.index.astype(str), missing.values)
    ax.set_xlabel("Missing Count")
    ax.set_title("Missing Values by Column")
    plt.tight_layout()
    st.pyplot(fig)


def show_distribution(df: pd.DataFrame):
    """수치형 컬럼 분포 (히스토그램)"""
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if not numeric_cols:
        st.info("수치형 컬럼이 없습니다.")
        return

    selected = st.multiselect("히스토그램 컬럼 선택", numeric_cols, default=numeric_cols[:3])
    if not selected:
        return

    n_cols = min(3, len(selected))
    n_rows = (len(selected) + n_cols - 1) // n_cols
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 4 * n_rows))
    axes = np.array(axes).flatten() if len(selected) > 1 else [axes]

    for i, col in enumerate(selected):
        axes[i].hist(df[col].dropna(), bins=30, edgecolor="black", alpha=0.7)
        axes[i].set_title(col)
        axes[i].set_xlabel(col)
        axes[i].set_ylabel("Frequency")

    for j in range(len(selected), len(axes)):
        axes[j].set_visible(False)

    plt.tight_layout()
    st.pyplot(fig)


def show_boxplot(df: pd.DataFrame):
    """수치형 컬럼 박스플롯"""
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if not numeric_cols:
        st.info("수치형 컬럼이 없습니다.")
        return

    selected = st.multiselect("박스플롯 컬럼 선택", numeric_cols, default=numeric_cols[:3], key="box")
    if not selected:
        return

    fig, ax = plt.subplots(figsize=(max(6, len(selected) * 1.5), 5))
    df[selected].boxplot(ax=ax)
    ax.set_title("Box Plot")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    st.pyplot(fig)


def show_correlation(df: pd.DataFrame):
    """수치형 컬럼 상관관계 히트맵"""
    numeric_df = df.select_dtypes(include="number")
    if numeric_df.shape[1] < 2:
        st.info("상관관계를 계산하려면 수치형 컬럼이 2개 이상 필요합니다.")
        return

    corr = numeric_df.corr()
    fig, ax = plt.subplots(figsize=(max(8, len(corr) * 0.6), max(6, len(corr) * 0.5)))
    cax = ax.matshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    fig.colorbar(cax)
    ax.set_xticks(range(len(corr.columns)))
    ax.set_yticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=90, fontsize=8)
    ax.set_yticklabels(corr.columns, fontsize=8)
    ax.set_title("Correlation Heatmap", pad=20)
    plt.tight_layout()
    st.pyplot(fig)


def show_scatter(df: pd.DataFrame):
    """수치형 컬럼 간 산점도"""
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if len(numeric_cols) < 2:
        st.info("산점도를 그리려면 수치형 컬럼이 2개 이상 필요합니다.")
        return

    c1, c2 = st.columns(2)
    x_col = c1.selectbox("X축", numeric_cols, index=0)
    y_col = c2.selectbox("Y축", numeric_cols, index=min(1, len(numeric_cols) - 1))

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(df[x_col], df[y_col], alpha=0.5, s=10)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title(f"{x_col} vs {y_col}")
    plt.tight_layout()
    st.pyplot(fig)


# ── 메인 페이지 ──────────────────────────────────────────
def main():
    st.set_page_config(page_title="EDA - Data Analysis", page_icon="📊", layout="wide")
    st.title("Exploratory Data Analysis")
    st.divider()

    # 테이블 선택
    tables = get_table_names()
    if not tables:
        st.warning("DB에 테이블이 없습니다. 먼저 데이터를 적재하세요.")
        return

    selected_table = st.sidebar.selectbox("테이블 선택", tables)
    df = load_table(selected_table)

    st.sidebar.markdown(f"**{selected_table}** — {len(df):,} rows, {len(df.columns)} cols")

    # 데이터 미리보기
    with st.expander("🔍 데이터 미리보기", expanded=True):
        st.dataframe(df.head(50), use_container_width=True)

    # 탭 구성
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "기본 정보", "기술 통계", "결측치", "분포", "상관관계", "산점도"
    ])

    with tab1:
        show_basic_info(df)
    with tab2:
        show_statistics(df)
    with tab3:
        show_missing_heatmap(df)
    with tab4:
        show_distribution(df)
        st.divider()
        show_boxplot(df)
    with tab5:
        show_correlation(df)
    with tab6:
        show_scatter(df)


if __name__ == "__main__":
    main()
