"""
后台监控任务
功能: 每日定时 (14:00) 抓取数据，如有高溢价机会通过飞书 Webhook 发送通知
"""

import schedule
import time
import requests
import json
import os
import logging
from dotenv import load_dotenv
from data_fetcher import get_market_opportunities

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 从环境变量获取飞书 Webhook URL
FEISHU_WEBHOOK_URL = os.getenv("FEISHU_BOT_HOOK_URL")

def send_feishu_message(content):
    """发送飞书消息"""
    if not FEISHU_WEBHOOK_URL:
        logger.error("❌ 未配置 FEISHU_BOT_HOOK_URL，无法发送消息")
        return

    headers = {"Content-Type": "application/json"}
    payload = {
        "msg_type": "text",
        "content": {
            "text": content
        }
    }
    
    try:
        resp = requests.post(FEISHU_WEBHOOK_URL, headers=headers, json=payload, timeout=10)
        if resp.status_code == 200:
            logger.info("✅ 飞书消息发送成功")
        else:
            logger.error(f"❌ 飞书消息发送失败: {resp.text}")
    except Exception as e:
        logger.error(f"❌ 发送飞书消息时发生异常: {str(e)}")

def job():
    """定时任务逻辑"""
    logger.info("⏰ 开始执行定时监控任务...")
    
    try:
        opportunities = get_market_opportunities()
        
        lof_idx = opportunities.get('lof_index')
        qdii_useu = opportunities.get('qdii_us_eu')
        qdii_comm = opportunities.get('qdii_commodity')
        
        msg_lines = []
        
        # 检查是否有机会
        has_opp = False
        
        if not lof_idx.empty:
            has_opp = True
            msg_lines.append(f"📈 【LOF指数】发现 {len(lof_idx)} 个机会:")
            for _, row in lof_idx.head(5).iterrows(): # 仅展示前5个
                msg_lines.append(f"- {row['基金名称']} ({row['基金代码']}): 溢价 {row['溢价率(%)']}")
            if len(lof_idx) > 5: msg_lines.append("...等")
            msg_lines.append("")

        if not qdii_useu.empty:
            has_opp = True
            msg_lines.append(f"🌍 【QDII欧美】发现 {len(qdii_useu)} 个机会:")
            for _, row in qdii_useu.head(5).iterrows():
                msg_lines.append(f"- {row['基金名称']} ({row['基金代码']}): 溢价 {row['溢价率(%)']}")
            if len(qdii_useu) > 5: msg_lines.append("...等")
            msg_lines.append("")
            
        if not qdii_comm.empty:
            has_opp = True
            msg_lines.append(f"🛢️ 【QDII商品】发现 {len(qdii_comm)} 个机会:")
            for _, row in qdii_comm.head(5).iterrows():
                msg_lines.append(f"- {row['基金名称']} ({row['基金代码']}): 溢价 {row['溢价率(%)']}")
            if len(qdii_comm) > 5: msg_lines.append("...等")
            msg_lines.append("")
            
        if has_opp:
            final_msg = "💰 基金高溢价套利提醒 (14:00)\n--------------------\n" + "\n".join(msg_lines)
            logger.info("发现机会，准备发送飞书通知...")
            send_feishu_message(final_msg)
        else:
            logger.info("未发现溢价 > 10% 的套利机会，无需发送通知。")
            
    except Exception as e:
        logger.error(f"❌ 定时任务执行异常: {str(e)}")

def main():
    if not FEISHU_WEBHOOK_URL:
        logger.warning("⚠️ 警告: 未检测到 FEISHU_BOT_HOOK_URL 环境变量，消息发送功能将不可用。")
    
    # 设定每天 14:00 执行
    schedule.every().day.at("14:00").do(job)
    
    logger.info("🚀 后台监控服务已启动")
    logger.info("📅 计划任务: 每日 14:00 检查套利机会")
    
    # 启动时先运行一次检查 (可选，为了确认服务正常，或者注释掉)
    # job() 
    
    while True:
        schedule.run_pending()
        time.sleep(60) # 每分钟检查一次

if __name__ == "__main__":
    # 禁用 SSL 警告
    import urllib3
    urllib3.disable_warnings()
    main()
