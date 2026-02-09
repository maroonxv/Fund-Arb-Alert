# LOF/QDII 基金套利监控系统

> 基于集思录 API 的高溢价基金套利机会实时监控工具

## 项目简介

本系统是一个轻量级的基金套利监控工具，通过集思录（Jisilu）API 获取 LOF 指数基金和 QDII 基金的实时溢价率数据，自动筛选溢价率超过 10% 的套利机会，并通过 Streamlit Web 界面展示和飞书 Webhook 推送通知。

### 核心功能

- 📊 **实时数据获取**：从集思录 API 获取 LOF 指数、QDII 欧美、QDII 商品三类基金数据
- 🔍 **智能筛选**：自动筛选溢价率 > 10% 的套利机会
- 🌐 **Web 界面**：基于 Streamlit 的直观 Web 界面，支持三个分类 Tab 展示
- 📱 **飞书通知**：每日 14:00 自动检测并推送高溢价机会到飞书群
- 🔗 **快捷跳转**：提供东方财富行情和蛋卷基金详情的快捷链接

### 数据源

- **集思录 (Jisilu)**：https://www.jisilu.cn/
  - LOF 指数基金数据：`/data/lof/index_lof_list/`
  - QDII 基金数据：`/data/qdii/qdii_list/`

## 技术栈

- **Python 3.10+**
- **Web 框架**：Streamlit >= 1.28.0
- **数据处理**：Pandas >= 1.5.0
- **HTTP 请求**：Requests >= 2.28.0
- **定时任务**：Schedule >= 1.2.0
- **测试框架**：Pytest + Hypothesis（属性测试）
- **环境变量**：python-dotenv >= 1.0.0

## 安装和运行

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd <project-directory>

# 创建虚拟环境（推荐）
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件（可选，仅用于飞书通知）：

```bash
# 飞书 Webhook URL（可选）
FEISHU_BOT_HOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook-url
```

### 3. 运行 Web 界面

```bash
streamlit run app.py
```

访问 http://localhost:8501 查看监控界面。

### 4. 运行后台定时任务（可选）

```bash
python background_task.py
```

后台任务将在每日 14:00 自动检测套利机会并发送飞书通知。

## 项目结构

```
project/
├── app.py                      # Streamlit Web 界面主程序
├── data_fetcher.py             # 数据获取与处理模块
├── background_task.py          # 后台定时任务 + 飞书通知
├── requirements.txt            # Python 依赖清单
├── .env                        # 环境变量配置（需自行创建）
├── .gitignore                  # Git 忽略文件配置
├── README.md                   # 项目说明文档
├── test_background_task.py     # 后台任务测试
├── test_checkpoint.py          # 检查点测试
└── .kiro/                      # Kiro 规范文档
    └── specs/
        └── jisilu-fund-monitor/
            ├── requirements.md  # 需求文档
            ├── design.md        # 设计文档
            └── tasks.md         # 任务清单
```

## 系统架构

### 架构图

```
┌─────────────────────────────────────────────────────────┐
│                    用户界面层                            │
│  ┌──────────────────┐      ┌──────────────────┐        │
│  │  Streamlit Web   │      │  飞书 Webhook    │        │
│  │    (app.py)      │      │ (background_task)│        │
│  └──────────────────┘      └──────────────────┘        │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  业务逻辑层                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │         data_fetcher.py (数据获取与处理)          │  │
│  │  • fetch_jisilu_data()    - API 请求             │  │
│  │  • process_jisilu_rows()  - 数据解析             │  │
│  │  • filter_by_premium()    - 溢价率筛选           │  │
│  │  • filter_by_keywords_and_premium() - 关键词筛选 │  │
│  │  • get_market_opportunities() - 统一入口         │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    数据源层                              │
│  ┌──────────────────┐      ┌──────────────────┐        │
│  │  集思录 LOF API  │      │  集思录 QDII API │        │
│  │  index_lof_list  │      │    qdii_list     │        │
│  └──────────────────┘      └──────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

### 数据流程

1. **数据获取**：通过 HTTP POST 请求从集思录 API 获取原始 JSON 数据
2. **数据解析**：提取 `fund_id`、`fund_nm`、`price`、`discount_rt`、`apply_status` 等字段
3. **数据清洗**：将溢价率字符串（如 "41.74%"）转换为浮点数
4. **数据筛选**：
   - LOF 指数：溢价率 > 10%
   - QDII 欧美：名称包含关键词（标普、纳指等）且溢价率 > 10%
   - QDII 商品：名称包含关键词（油、金、银等）且溢价率 > 10%
5. **数据展示**：通过 Streamlit 界面或飞书消息展示结果

## 使用说明

### Web 界面

1. **三个 Tab 分类展示**：
   - 📈 LOF 指数 (>10%)：国内上市的指数型 LOF 基金
   - 🌍 QDII 欧美 (>10%)：投资美股、欧股等的 QDII 基金
   - 🛢️ QDII 商品 (>10%)：投资油气、黄金等商品的 QDII 基金

2. **数据刷新**：点击侧边栏的"🔄 刷新数据"按钮清除缓存并重新获取

3. **快捷链接**：
   - 行情链接：跳转到东方财富查看实时行情
   - 详情链接：跳转到蛋卷基金查看基金详情

### 飞书通知

配置 `.env` 文件中的 `FEISHU_BOT_HOOK_URL` 后，后台任务会在每日 14:00 自动检测并推送通知。

通知内容示例：
```
💰 基金高溢价套利提醒 (14:00)
--------------------
📈 【LOF指数】发现 3 个机会:
- 石油基金LOF (160416): 溢价 41.74
- 国投白银LOF (161226): 溢价 20.36
...

🌍 【QDII欧美】发现 2 个机会:
- 纳指ETF (513100): 溢价 15.23
...
```

## 筛选关键词配置

### QDII 欧美关键词
```python
["标普", "纳指", "纳斯达克", "道琼斯", "德国", "法国", 
 "日经", "美国", "欧洲", "海外"]
```

### QDII 商品关键词
```python
# 能源类
["油", "原油", "石油", "油气", "能源"]
# 贵金属类
["金", "银", "黄金", "白银"]
# 工业金属类
["铜", "有色"]
# 农产品类
["豆", "糖", "棉"]
# 综合类
["商品", "资源", "抗通胀"]
```

## 测试

项目使用 pytest + hypothesis 进行测试：

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest test_background_task.py

# 查看测试覆盖率
pytest --cov=. --cov-report=html
```

## 错误处理

| 场景 | 处理方式 | 用户影响 |
|------|---------|---------|
| API 请求超时 (10s) | 记录日志，返回空列表 | 对应 Tab 显示"无数据" |
| API 返回非 200 | 记录日志，返回空列表 | 对应 Tab 显示"无数据" |
| JSON 解析失败 | 记录日志，返回空列表 | 对应 Tab 显示"无数据" |
| discount_rt 格式异常 | 默认为 0.0 | 该基金溢价率显示为 0 |
| 飞书 Webhook 未配置 | 记录错误日志，跳过发送 | 不影响 Web 界面 |
| 飞书消息发送失败 | 记录错误日志 | 不影响 Web 界面 |

## 常见问题

### Q1: 为什么有些基金的溢价率显示为 0？
**A**: 可能是集思录 API 返回的 `discount_rt` 字段格式异常或缺失，系统会默认设置为 0.0。

### Q2: 如何修改溢价率阈值？
**A**: 在 `data_fetcher.py` 中修改 `PREMIUM_THRESHOLD` 常量（默认 10.0）。

### Q3: 飞书通知没有收到消息？
**A**: 请检查：
1. `.env` 文件中的 `FEISHU_BOT_HOOK_URL` 是否配置正确
2. 后台任务 `background_task.py` 是否正在运行
3. 当前是否有溢价率 > 10% 的机会（无机会时不发送通知）

### Q4: 如何添加新的筛选关键词？
**A**: 在 `data_fetcher.py` 中修改 `KEYWORDS_US_EU` 或 `KEYWORDS_COMMODITY` 列表。

## 开发说明

### 添加新的数据源

1. 在 `data_fetcher.py` 中添加新的 `fetch_xxx_data()` 函数
2. 在 `get_market_opportunities()` 中调用并返回结果
3. 在 `app.py` 中添加新的 Tab 展示

### 修改筛选逻辑

在 `data_fetcher.py` 中修改 `filter_by_premium()` 或 `filter_by_keywords_and_premium()` 函数。

## 许可证

本项目仅供学习和研究使用，请勿用于商业用途。

## 贡献

欢迎提交 Issue 和 Pull Request！

---

**最后更新**: 2026-02-09  
**版本**: v2.0 (集思录 API 版本)
