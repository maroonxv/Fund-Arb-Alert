"""
数据获取与处理模块
负责从集思录抓取数据并进行清洗和筛选
"""

import os
import requests
import pandas as pd
import time
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logger = logging.getLogger(__name__)

# 全局配置
JISILU_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Referer": "https://www.jisilu.cn/",
    "X-Requested-With": "XMLHttpRequest"
}

# 集思录登录地址
JISILU_LOGIN_URL = "https://www.jisilu.cn/account/ajax/login_process/"

# 全局 Session（模块级别复用）
_session: requests.Session | None = None
_logged_in: bool = False


def _get_session() -> requests.Session:
    """
    获取已登录的 requests.Session。
    首次调用时创建 Session 并尝试登录，后续复用。
    """
    global _session, _logged_in

    if _session is not None:
        return _session

    _session = requests.Session()
    _session.headers.update(JISILU_HEADERS)
    _session.verify = False

    account = os.getenv("jisilu_account")
    password = os.getenv("jisilu_password")

    if not account or not password:
        logger.warning("⚠️ 未配置 jisilu_account / jisilu_password，将以未登录状态抓取数据")
        return _session

    try:
        login_data = {
            "user_name": account,
            "password": password,
            "net_auto_login": "1",
            "return_url": "",
        }
        resp = _session.post(
            JISILU_LOGIN_URL, data=login_data, timeout=10
        )
        result = resp.json()
        if resp.status_code == 200 and result.get("err") == 0:
            _logged_in = True
            logger.info("✅ 集思录登录成功")
        else:
            err_msg = result.get("msg", "未知错误")
            logger.error(f"❌ 集思录登录失败: {err_msg}")
    except Exception as e:
        logger.error(f"❌ 集思录登录异常: {str(e)}")

    return _session

# 筛选关键词配置
KEYWORDS_US_EU = [
    "标普", "纳指", "纳斯达克", "道琼斯",
    "德国", "法国", "日经", "美国", "欧洲", "海外"
]

KEYWORDS_COMMODITY = [
    # 能源类
    "油", "原油", "石油", "油气", "能源",
    # 贵金属类
    "金", "银", "黄金", "白银",
    # 工业金属类
    "铜", "有色",
    # 农产品类
    "豆", "糖", "棉",
    # 综合类
    "商品", "资源", "抗通胀"
]

PREMIUM_THRESHOLD = 5.0


def fetch_jisilu_data(url: str, description: str = "Data") -> list:
    """
    通用集思录 API 数据抓取函数。
    使用已登录的 Session 发送 POST 请求，返回 rows 数组。
    失败时返回空列表并记录日志。
    """
    try:
        session = _get_session()

        ts = int(time.time() * 1000)
        full_url = f"{url}?___jsl=LST___t={ts}"

        params = {"rp": 100, "page": 1}

        logger.info(f"开始抓取 {description}: {url}")
        resp = session.post(
            full_url, data=params, timeout=10
        )

        if resp.status_code == 200:
            data = resp.json()
            if "rows" in data:
                logger.info(f"✅ {description} 抓取成功，共 {len(data['rows'])} 条")
                return data["rows"]
            else:
                logger.warning(f"⚠️ {description} 响应格式不包含 'rows'")
                return []
        else:
            logger.error(f"❌ {description} 请求失败，状态码: {resp.status_code}")
            return []
    except Exception as e:
        logger.error(f"❌ {description} 发生异常: {str(e)}")
        return []


def process_jisilu_rows(rows: list, fund_type: str = "LOF") -> pd.DataFrame:
    """
    将集思录返回的 rows 数据解析为 DataFrame。
    提取 fund_id, fund_nm, price, discount_rt, apply_status。
    输出列: 基金代码, 基金名称, 现价, 溢价率(%), 申购状态
    """
    if not rows:
        return pd.DataFrame()

    processed_data = []
    for row in rows:
        cell = row.get("cell", {})
        if not cell:
            continue

        fund_id = cell.get("fund_id")
        fund_nm = cell.get("fund_nm")
        price = cell.get("price")

        # 溢价率处理
        discount_rt_raw = cell.get("discount_rt", "0")
        try:
            if isinstance(discount_rt_raw, str):
                premium_rt = float(discount_rt_raw.replace("%", ""))
            else:
                premium_rt = float(discount_rt_raw)
        except (ValueError, TypeError):
            premium_rt = 0.0

        apply_status = cell.get("apply_status", "未知")

        processed_data.append({
            "基金代码": fund_id,
            "基金名称": fund_nm,
            "现价": price,
            "溢价率(%)": round(premium_rt, 2),
            "申购状态": apply_status,
        })

    df = pd.DataFrame(processed_data)
    if not df.empty:
        df["溢价率(%)"] = pd.to_numeric(df["溢价率(%)"], errors="coerce")
    return df


def filter_by_premium(df: pd.DataFrame, threshold: float = PREMIUM_THRESHOLD) -> pd.DataFrame:
    """按溢价率阈值筛选并降序排列。"""
    if df.empty:
        return pd.DataFrame()
    mask = df["溢价率(%)"] > threshold
    return df[mask].sort_values("溢价率(%)", ascending=False)


def filter_by_keywords_and_premium(
    df: pd.DataFrame,
    keywords: list,
    threshold: float = PREMIUM_THRESHOLD,
) -> pd.DataFrame:
    """按关键词 + 溢价率阈值筛选并降序排列。"""
    if df.empty or not keywords:
        return pd.DataFrame()
    pattern = "|".join(keywords)
    mask_name = df["基金名称"].str.contains(pattern, regex=True, na=False)
    mask_premium = df["溢价率(%)"] > threshold
    return df[mask_name & mask_premium].sort_values("溢价率(%)", ascending=False)


def get_market_opportunities() -> dict:
    """
    获取并筛选所有市场机会。
    返回 dict，包含 lof_index, qdii_us_eu, qdii_commodity 三个 DataFrame。
    """
    # 1. 获取 LOF 指数数据
    lof_rows = fetch_jisilu_data(
        "https://www.jisilu.cn/data/lof/index_lof_list/", "LOF指数数据"
    )
    df_lof = process_jisilu_rows(lof_rows, "LOF")

    # 2. 获取 QDII 全量数据（欧美 + 商品均从此筛选）
    qdii_rows = fetch_jisilu_data(
        "https://www.jisilu.cn/data/qdii/qdii_list/", "QDII数据"
    )
    df_qdii = process_jisilu_rows(qdii_rows, "QDII")

    # 3. 筛选
    results = {
        "lof_index": filter_by_premium(df_lof),
        "qdii_us_eu": filter_by_keywords_and_premium(df_qdii, KEYWORDS_US_EU),
        "qdii_commodity": filter_by_keywords_and_premium(df_qdii, KEYWORDS_COMMODITY),
    }

    return results
