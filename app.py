"""
LOF/QDII 基金套利监控系统 (集思录版)
功能: 监控 LOF 指数、QDII 欧美及商品基金的高溢价套利机会
数据源: 集思录 (Jisilu)
"""

import streamlit as st
import pandas as pd
import logging
from datetime import datetime
from data_fetcher import get_market_opportunities  # 导入公共数据模块

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def make_clickable_links(df):
    """添加点击跳转链接"""
    if df.empty:
        return df
    
    df_display = df.copy()
    
    # 东方财富链接
    df_display['行情'] = df_display['基金代码'].apply(
        lambda x: f"https://so.eastmoney.com/web/s?keyword={x}"
    )
    # 蛋卷/天天基金链接 (这里示例用蛋卷)
    df_display['详情'] = df_display['基金代码'].apply(
        lambda x: f"https://danjuanfunds.com/funding/{x}"
    )
    
    return df_display

def main():
    st.set_page_config(
        page_title="LOF/QDII 套利监控 (集思录版)",
        page_icon="💰",
        layout="wide"
    )
    
    st.title("💰 LOF/QDII 高溢价套利监控")
    st.markdown("""
    > 数据来源：集思录 (Jisilu) | 筛选标准：溢价率 > 10%
    """)
    
    # 侧边栏
    with st.sidebar:
        st.header("⚙️ 控制台")
        if st.button("🔄 刷新数据", type="primary"):
            st.cache_data.clear()
        
        st.info("💡 提示：\n点击列名可排序\n双击单元格可放大")
        st.markdown("---")
        st.markdown("### 📝 策略说明")
        st.markdown("**1. LOF 指数**\n关注国内上市的指数型 LOF，溢价 > 10%")
        st.markdown("**2. QDII 欧美**\n关注美股、欧股等 QDII，T-1 溢价 > 10%")
        st.markdown("**3. QDII 商品**\n关注油气、黄金等商品 QDII，T-1 溢价 > 10%")

    # 获取数据
    with st.spinner("🚀 正在从集思录 API 获取最新数据..."):
        opportunities = get_market_opportunities()

    # 创建 Tabs
    tab1, tab2, tab3 = st.tabs([
        "📈 LOF 指数 (>10%)", 
        "🌍 QDII 欧美 (>10%)", 
        "🛢️ QDII 商品 (>10%)"
    ])
    
    # 通用列配置
    column_config = {
        "行情": st.column_config.LinkColumn("行情 (东财)"),
        "详情": st.column_config.LinkColumn("详情 (蛋卷)"),
        "溢价率(%)": st.column_config.NumberColumn(
            "溢价率",
            format="%.2f%%",
            help="正数表示溢价，负数表示折价"
        )
    }

    def show_dataframe(df, key_prefix):
        if df.empty:
            st.info("当前无符合条件 (>10% 溢价) 的标的。" )
        else:
            # 添加链接
            df_show = make_clickable_links(df)
            # 选择展示列
            cols = ['基金代码', '基金名称', '现价', '溢价率(%)', '申购状态', '行情', '详情']
            
            st.dataframe(
                df_show[cols],
                column_config=column_config,
                use_container_width=True,
                hide_index=True,
                height=400
            )
            st.caption(f"共发现 {len(df)} 个机会")

    with tab1:
        st.subheader("📈 LOF 指数基金高溢价机会")
        show_dataframe(opportunities['lof_index'], "lof")
        
    with tab2:
        st.subheader("🌍 QDII 欧美指数高溢价机会")
        show_dataframe(opportunities['qdii_us_eu'], "us_eu")
        
    with tab3:
        st.subheader("🛢️ QDII 商品基金高溢价机会")
        show_dataframe(opportunities['qdii_commodity'], "commodity")

    # 底部更新时间
    st.markdown("---")
    st.caption(f"最后更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    # 禁用 urllib3 的 SSL 警告
    import urllib3
    urllib3.disable_warnings()
    main()