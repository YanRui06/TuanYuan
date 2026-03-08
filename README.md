# 团员教育评议投票系统 (TuanYuan)

这是一个基于 [Streamlit](https://streamlit.io/) 构建的 Web 应用程序，旨在简化基层团支部的团员教育评议流程。系统支持团员信息管理、自评互评数据采集、自动计算评议等级以及结果导出等功能。

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)

## 🌟 核心功能

*   **团员信息管理**：管理员可批量导入或手动录入团员信息（包括姓名、身份证后4位等）。
*   **评议投票**：
    *   **自评**：展示团员自评情况。
    *   **互评**：团员之间进行互评打分。
*   **智能计算**：
    *   根据预设权重（默认为自评 40%，互评 60%）自动计算综合得分。
    *   自动根据分数划分评议等级（优秀/合格/基本合格/不合格）。
*   **数据持久化**：使用 CSV 文件本地存储数据，方便备份与迁移。
*   **权限管理**：简单的管理员密码验证机制，保护敏感操作。

## 🛠️ 安装指南

### 1. 克隆项目或下载源码

```bash
git clone <repository-url>
cd TuanYuan
```

### 2. 安装依赖

建议使用 Python 3.8 及以上版本。

```bash
pip install -r requirements.txt
```

*如果你遇到安装速度慢的问题，可以使用国内镜像源：*
`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

## 🚀 运行项目

在终端中执行以下命令启动系统：

```bash
streamlit run main.py
```

启动成功后，浏览器会自动打开 `http://localhost:8501`。如果未自动打开，请手动访问该地址。

## 📖 使用说明

1.  **系统初始化**：
    *   首次运行时，系统会自动创建 `member_data.csv` 和 `votes_data.csv` 用于存储数据。
2.  **管理员登录**：
    *   默认管理员密码为：`123456`（可在 `main.py` 中修改 `ADMIN_PASSWORD`）。
    *   管理员可以进行团员名单导入、清空数据、查看详细投票结果等操作。
3.  **评议流程**：
    *   团员可以使用特定身份（如姓名+身份证后4位）登录进行互评。
    *   系统会实时统计投票进度。

## ⚙️ 配置项说明

主要配置位于 `main.py` 文件头部，你可以根据实际需求修改：

```python
# 管理员密码
ADMIN_PASSWORD = "123456"

# 评议等级权重配置
GRADE_WEIGHTS = {
    "自评权重": 0.4,
    "互评权重": 0.6
}

# 等级分数阈值（分数 ≥ 阈值）
GRADE_THRESHOLDS = {
    "优秀": 3.5,
    "合格": 2.5,
    "基本合格": 1.5,
    "不合格": 0
}
```

## 📂 数据文件

系统运行过程中会生成以下文件：

*   `member_data.csv`: 存储团员基础信息及最终评议结果。
*   `votes_data.csv`: 存储所有的互评投票记录。

> **注意**：请定期备份这两个 CSV 文件以防数据丢失。

## ⚠️ 注意事项

*   本系统为轻量级应用，适用于单个团支部内部使用。
*   默认不包含复杂的用户鉴权系统，请在受信任的网络环境中使用。
