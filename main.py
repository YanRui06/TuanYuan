import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
import os
import json

warnings.filterwarnings('ignore')

# 页面基础设置
st.set_page_config(
    page_title="团员教育评议投票系统",
    page_icon="🏫",
    layout="wide"
)

# 常量定义（数据持久化文件）
DATA_FILE = "member_data.csv"
VOTES_FILE = "votes_data.csv"

# ===================== 数据持久化核心函数 =====================
def load_member_data():
    """加载团员基础信息（CSV持久化）"""
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, dtype=str, encoding='utf-8-sig')
            df.fillna('', inplace=True)
            return df
        except:
            # 兼容编码问题
            df = pd.read_csv(DATA_FILE, dtype=str, encoding='gbk')
            df.fillna('', inplace=True)
            return df
    # 初始化空数据表
    return pd.DataFrame({
        '姓名': [],
        '是否新团员(未满一年)': [],
        '是否有处分/挂科': [],
        '自评等级': [],
        '互评等级': [],
        '最终评议等级': [],
        '备注': []
    })

def save_member_data(df):
    """保存团员基础信息到CSV"""
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

def load_votes_data():
    """加载投票数据（CSV持久化）"""
    if os.path.exists(VOTES_FILE):
        try:
            df = pd.read_csv(VOTES_FILE, dtype=str, encoding='utf-8-sig')
            df.fillna('', inplace=True)
            return df
        except:
            df = pd.read_csv(VOTES_FILE, dtype=str, encoding='gbk')
            df.fillna('', inplace=True)
            return df
    # 初始化空投票表
    return pd.DataFrame({
        '投票人': [],
        '投票详情': []  # JSON字符串存储投票明细
    })

def save_votes_data(df):
    """保存投票数据到CSV"""
    df.to_csv(VOTES_FILE, index=False, encoding='utf-8-sig')

# ===================== 会话状态初始化 =====================
if 'member_data' not in st.session_state:
    st.session_state.member_data = load_member_data()

if 'class_name' not in st.session_state:
    st.session_state.class_name = "默认团支部"

if 'total_members' not in st.session_state:
    # 自动计算总人数（优先用录入的，无则用数据行数）
    member_count = len(st.session_state.member_data)
    st.session_state.total_members = member_count if member_count > 0 else 1

# ===================== 核心业务函数 =====================
def validate_evaluation(df, total_members):
    """校验评优规则：优秀比例、挂科/新团员限制"""
    max_excellent = int(total_members * 0.3)  # 30%上限
    excellent_count = len(df[df['最终评议等级'] == '优秀'])
    
    # 检查1：挂科/处分人员不能评优秀
    disqualified_excellent = df[(df['是否有处分/挂科'] == '是') & (df['最终评议等级'] == '优秀')]
    if len(disqualified_excellent) > 0:
        st.error(f"❌ 错误：以下团员有处分/挂科，不能评为优秀：{', '.join(disqualified_excellent['姓名'].tolist())}")
        return False
    
    # 检查2：新团员（未满一年）不能参评
    new_member_evaluate = df[(df['是否新团员(未满一年)'] == '是') & (df['最终评议等级'] != '不参评')]
    if len(new_member_evaluate) > 0:
        st.error(f"❌ 错误：以下新团员(未满一年)不能参评，需标记为'不参评'：{', '.join(new_member_evaluate['姓名'].tolist())}")
        return False
    
    # 检查3：优秀比例不超过30%
    if excellent_count > max_excellent:
        st.error(f"❌ 错误：优秀团员数量({excellent_count}人)超过30%上限({max_excellent}人)，请调整！")
        return False
    
    st.success(f"✅ 校验通过！优秀团员数量({excellent_count}人) ≤ 30%上限({max_excellent}人)")
    return True

def generate_excel(df, class_name):
    """生成最终导出的Excel表格（CSV格式，Excel可直接打开）"""
    # 整理输出格式
    output_df = df[['姓名', '是否新团员(未满一年)', '是否有处分/挂科', '自评等级', '互评等级', '最终评议等级', '备注']].copy()
    output_df.columns = ['姓名', '是否新团员', '是否有处分/挂科', '自评等级', '互评等级', '最终评议等级', '备注']
    
    # 添加统计信息行
    total_members = st.session_state.total_members
    max_excellent = int(total_members * 0.3)
    actual_excellent = len(df[df['最终评议等级'] == '优秀'])
    stats_df = pd.DataFrame({
        '姓名': ['统计信息', '', ''],
        '是否新团员': [f'团支部总人数：{total_members}', f'优秀上限：{max_excellent}', f'实际优秀人数：{actual_excellent}'],
        '是否有处分/挂科': ['', '', ''],
        '自评等级': ['', '', ''],
        '互评等级': ['', '', ''],
        '最终评议等级': ['', '', ''],
        '备注': [f'导出时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}', '公示期：3天', f'制表人：{class_name}团支书']
    })
    
    final_df = pd.concat([output_df, stats_df], ignore_index=True)
    return final_df

# ===================== 页面主体 =====================
# 侧边栏：角色选择
st.sidebar.title("📋 系统导航")
role = st.sidebar.radio(
    "🎯 选择你的身份",
    ["🗳️ 团员投票通道", "👑 管理员后台"],
    index=0
)
st.sidebar.info("💡 提示：管理员先录入名册，团员再进行投票")
st.sidebar.divider()
st.sidebar.markdown("#### 📞 操作说明")
st.sidebar.markdown("1. 管理员：导入名单 → 查看投票 → 结算结果\n2. 团员：选择姓名 → 完成互评/自评 → 提交")

# ===================== 管理员后台 =====================
if role == "👑 管理员后台":
    st.title("🏫 管理员后台 - 团员教育评议管理系统")
    st.divider()

    # 第一步：团支部基础信息设置
    st.subheader("📋 第一步：团支部基础信息")
    col1, col2 = st.columns(2)
    with col1:
        class_name = st.text_input(
            "请输入班级名称（如：2023级计算机1班）",
            value=st.session_state.class_name,
            placeholder="例：2023级汉语言文学2班"
        )
        st.session_state.class_name = class_name
    with col2:
        total_members = st.number_input(
            "团支部总人数（智慧团建人数）",
            min_value=1,
            value=st.session_state.total_members,
            help="优秀名额=总人数×30%（向下取整）"
        )
        st.session_state.total_members = total_members

    # 第二步：团员信息管理（导入/添加/编辑）
    st.subheader("✏️ 第二步：团员信息管理")
    tab1, tab2, tab3 = st.tabs(["📤 批量导入(Excel)", "➕ 添加单名团员", "✂️ 编辑/删除团员"])

    # 标签页1：批量导入Excel
    with tab1:
        st.info("💡 模板说明：必须包含「姓名」列，可选列「是否新团员(未满一年)」「是否有处分/挂科」")
        # 下载模板
        template_df = pd.DataFrame({
            '姓名': ['张三', '李四', '王五'],
            '是否新团员(未满一年)': ['否', '是', '否'],
            '是否有处分/挂科': ['否', '否', '是'],
            '自评等级': ['', '', ''],
            '互评等级': ['', '', ''],
            '最终评议等级': ['', '不参评', ''],
            '备注': ['', '', '挂科2门']
        })
        st.download_button(
            label="📥 下载导入模板（CSV/Excel可打开）",
            data=template_df.to_csv(index=False, encoding='utf-8-sig'),
            file_name=f"{class_name}团员导入模板.csv",
            mime="text/csv"
        )

        # 文件上传
        uploaded_file = st.file_uploader(
            "选择Excel/CSV文件上传",
            type=['xlsx', 'xls', 'csv'],
            help="支持.xlsx/.xls/.csv格式，优先读取「姓名」列"
        )

        if uploaded_file is not None:
            if st.button("🚀 开始导入数据", type="primary"):
                try:
                    # 读取上传文件
                    if uploaded_file.name.endswith('.csv'):
                        df_imported = pd.read_csv(uploaded_file, dtype=str, encoding='utf-8-sig')
                    else:
                        df_imported = pd.read_excel(uploaded_file, dtype=str)
                    df_imported.fillna('', inplace=True)

                    # 校验必备列
                    if '姓名' not in df_imported.columns:
                        st.error("❌ 导入失败！文件中未找到「姓名」列，请检查模板格式")
                    else:
                        # 补全缺失列
                        standard_cols = list(st.session_state.member_data.columns)
                        for col in standard_cols:
                            if col not in df_imported.columns:
                                if col in ['是否新团员(未满一年)', '是否有处分/挂科']:
                                    df_imported[col] = '否'  # 默认非新团员、无处分
                                else:
                                    df_imported[col] = ''     # 其他列默认空

                        # 数据清洗：去空、去重
                        df_imported = df_imported[standard_cols]
                        df_imported = df_imported.replace('nan', '')
                        df_imported = df_imported[df_imported['姓名'].str.strip() != '']  # 过滤空姓名
                        df_imported = df_imported.drop_duplicates(subset=['姓名'], keep='last')  # 去重

                        # 合并数据（覆盖原有同名数据）
                        combined_df = pd.concat([st.session_state.member_data, df_imported])
                        combined_df = combined_df.drop_duplicates(subset=['姓名'], keep='last').reset_index(drop=True)
                        
                        # 自动给新团员标记「不参评」
                        combined_df.loc[combined_df['是否新团员(未满一年)'] == '是', '最终评议等级'] = '不参评'

                        # 保存并更新会话状态
                        st.session_state.member_data = combined_df
                        save_member_data(combined_df)

                        st.success(f"✅ 导入成功！共导入 {len(df_imported)} 名团员，当前总人数：{len(combined_df)}")
                except Exception as e:
                    st.error(f"❌ 导入出错：{str(e)}，请检查文件格式或联系管理员")

    # 标签页2：添加单名团员
    with tab2:
        col1, col2, col3 = st.columns(3)
        with col1:
            member_name = st.text_input("团员姓名", placeholder="请输入真实姓名")
        with col2:
            is_new_member = st.selectbox("是否新团员(未满一年)", ["否", "是"])
        with col3:
            has_punishment = st.selectbox("是否有处分/挂科", ["否", "是"])

        if st.button("➕ 添加团员", type="primary"):
            if not member_name:
                st.warning("⚠️ 请输入团员姓名！")
            elif member_name in st.session_state.member_data['姓名'].tolist():
                st.warning(f"⚠️ 团员「{member_name}」已存在，请勿重复添加！")
            else:
                # 构建新团员数据
                new_row = pd.DataFrame({
                    '姓名': [member_name],
                    '是否新团员(未满一年)': [is_new_member],
                    '是否有处分/挂科': [has_punishment],
                    '自评等级': [""],
                    '互评等级': [""],
                    '最终评议等级': ["不参评" if is_new_member == "是" else ""],
                    '备注': [""]
                })
                # 合并并保存
                st.session_state.member_data = pd.concat([st.session_state.member_data, new_row], ignore_index=True)
                save_member_data(st.session_state.member_data)
                st.success(f"✅ 成功添加团员：{member_name}")

    # 标签页3：编辑/删除团员
    with tab3:
        if len(st.session_state.member_data) == 0:
            st.info("📭 暂无团员数据，请先导入/添加！")
        else:
            # 选择要编辑的团员
            selected_member = st.selectbox("选择要编辑的团员", st.session_state.member_data['姓名'].tolist())
            member_idx = st.session_state.member_data[st.session_state.member_data['姓名'] == selected_member].index[0]
            
            # 编辑表单
            col1, col2, col3 = st.columns(3)
            with col1:
                self_grade = st.selectbox(
                    "自评等级",
                    ["", "优秀", "合格", "基本合格", "不合格"],
                    index=["", "优秀", "合格", "基本合格", "不合格"].index(st.session_state.member_data.loc[member_idx, '自评等级'])
                )
            with col2:
                mutual_grade = st.selectbox(
                    "互评等级",
                    ["", "优秀", "合格", "基本合格", "不合格"],
                    index=["", "优秀", "合格", "基本合格", "不合格"].index(st.session_state.member_data.loc[member_idx, '互评等级'])
                )
            with col3:
                # 新团员锁定为不参评
                if st.session_state.member_data.loc[member_idx, '是否新团员(未满一年)'] == '是':
                    final_grade = st.selectbox("最终评议等级", ["不参评"], disabled=True)
                else:
                    final_grade = st.selectbox(
                        "最终评议等级",
                        ["", "优秀", "合格", "基本合格", "不合格"],
                        index=["", "优秀", "合格", "基本合格", "不合格"].index(st.session_state.member_data.loc[member_idx, '最终评议等级'])
                    )
            
            note = st.text_input("备注信息", value=st.session_state.member_data.loc[member_idx, '备注'])

            # 操作按钮
            col4, col5 = st.columns(2)
            with col4:
                if st.button("💾 保存修改", type="primary"):
                    # 更新数据
                    st.session_state.member_data.loc[member_idx, '自评等级'] = self_grade
                    st.session_state.member_data.loc[member_idx, '互评等级'] = mutual_grade
                    st.session_state.member_data.loc[member_idx, '最终评议等级'] = final_grade
                    st.session_state.member_data.loc[member_idx, '备注'] = note
                    save_member_data(st.session_state.member_data)
                    st.success(f"✅ 已更新团员「{selected_member}」的信息！")
            with col5:
                if st.button("🗑️ 删除该团员", type="secondary"):
                    # 删除数据
                    st.session_state.member_data = st.session_state.member_data.drop(member_idx).reset_index(drop=True)
                    save_member_data(st.session_state.member_data)
                    st.success(f"✅ 已删除团员：{selected_member}")
                    st.rerun()  # 刷新页面

    # 第三步：投票数据统计与结果结算
    st.subheader("📊 第三步：投票统计与结果结算")
    if len(st.session_state.member_data) == 0:
        st.info("📭 暂无团员数据，请先导入/添加！")
    else:
        # 加载投票数据
        df_votes = load_votes_data()
        st.write(f"📈 投票进度：已有 **{len(df_votes)}** 人完成投票（总人数：{len(st.session_state.member_data)}）")
        
        # 实时票数统计
        if len(df_votes) > 0:
            st.markdown("### 📝 实时互评票数统计")
            # 初始化票数统计字典
            vote_counts = {
                name: {"优秀": 0, "合格": 0, "基本合格": 0, "不合格": 0} 
                for name in st.session_state.member_data['姓名'].tolist()
            }
            
            # 解析所有投票数据
            for _, row in df_votes.iterrows():
                try:
                    votes = json.loads(row['投票详情'])
                    for p_name, p_grade in votes.items():
                        if p_name in vote_counts and p_grade in vote_counts[p_name]:
                            vote_counts[p_name][p_grade] += 1
                except:
                    continue  # 跳过格式错误的投票数据
            
            # 展示票数表格
            stats_df = pd.DataFrame.from_dict(vote_counts, orient='index').reset_index()
            stats_df.rename(columns={'index': '姓名'}, inplace=True)
            st.dataframe(stats_df, use_container_width=True)
            
            # 一键结算互评等级
            if st.button("🪄 根据最高票自动结算「互评等级」", type="primary"):
                for idx, row in st.session_state.member_data.iterrows():
                    name = row['姓名']
                    if name in vote_counts:
                        # 找到最高票的等级
                        max_grade = max(vote_counts[name], key=vote_counts[name].get)
                        # 有票数才更新
                        if sum(vote_counts[name].values()) > 0:
                            st.session_state.member_data.loc[idx, '互评等级'] = max_grade
                save_member_data(st.session_state.member_data)
                st.success("✅ 互评等级已根据最高得票自动填充！")
                st.rerun()

        # 最终结果预览
        st.markdown("### 📋 最终评议结果预览")
        st.dataframe(st.session_state.member_data, use_container_width=True)

        # 规则校验与导出
        col6, col7 = st.columns(2)
        with col6:
            if st.button("🔍 校验评优规则", type="primary"):
                validate_evaluation(st.session_state.member_data, st.session_state.total_members)
        with col7:
            if st.button("📤 导出最终结果（Excel/CSV）", type="secondary"):
                if validate_evaluation(st.session_state.member_data, st.session_state.total_members):
                    final_df = generate_excel(st.session_state.member_data, st.session_state.class_name)
                    # 下载按钮
                    st.download_button(
                        label="💾 点击下载表格",
                        data=final_df.to_csv(index=False, encoding='utf-8-sig'),
                        file_name=f"{st.session_state.class_name}团员教育评议结果.csv",
                        mime="text/csv"
                    )

    # 数据清空功能
    st.divider()
    if st.button("🆘 清空全部数据（含团员+投票）", type="secondary"):
        # 删除持久化文件
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        if os.path.exists(VOTES_FILE):
            os.remove(VOTES_FILE)
        # 重置会话状态
        st.session_state.member_data = load_member_data()
        st.session_state.total_members = 1
        st.success("✅ 已清空所有数据！请刷新页面生效")

# ===================== 团员投票通道 =====================
elif role == "🗳️ 团员投票通道":
    st.title("🗳️ 团员民主互评投票通道")
    st.divider()

    # 加载最新团员数据
    st.session_state.member_data = load_member_data()
    df_mem = st.session_state.member_data

    if len(df_mem) == 0:
        st.warning("⚠️ 管理员尚未录入团员名单，暂无法投票！")
    else:
        # 第一步：选择投票人身份
        all_names = df_mem['姓名'].tolist()
        voter_name = st.selectbox(
            "🤔 请选择您的姓名（仅可投票一次）",
            ["请选择..."] + all_names,
            index=0
        )

        if voter_name != "请选择...":
            # 检查是否已投票
            df_votes = load_votes_data()
            voted_list = df_votes['投票人'].tolist()

            if voter_name in voted_list:
                st.success(f"🎉 亲爱的 {voter_name}，您已完成投票！感谢您的参与！")
                st.info("📌 若需修改请联系管理员重置您的投票记录")
            else:
                # 投票说明
                max_excellent = int(len(df_mem) * 0.3)
                st.info(f"""
                👋 {voter_name}，您好！请完成以下评议：
                📌 互评说明：仅评价其他团员（新团员无需评价）
                📌 优秀限制：您评价的「优秀」人数≤{max_excellent}人（含自评）
                📌 提交后不可修改，请认真填写！
                """)

                # 第二步：投票表单
                with st.form("voting_form", clear_on_submit=True):
                    st.markdown("### 📝 团员互评打分")
                    vote_dict = {}  # 存储互评结果

                    # 生成互评项（跳过自己、新团员）
                    for _, row in df_mem.iterrows():
                        target_name = row['姓名']
                        is_new = row['是否新团员(未满一年)']

                        # 跳过自己
                        if target_name == voter_name:
                            continue
                        # 新团员无需评价
                        if is_new == "是":
                            st.write(f"ℹ️ {target_name}（新入团未满一年，无需评价）")
                            continue

                        # 互评选项
                        vote_dict[target_name] = st.radio(
                            f"您对「{target_name}」的评价：",
                            ["优秀", "合格", "基本合格", "不合格"],
                            index=1,  # 默认合格
                            horizontal=True,
                            key=f"vote_{target_name}"
                        )
                        st.divider()

                    # 第三步：自评打分
                    st.markdown("### 📝 个人自评打分")
                    self_eval = st.radio(
                        f"您对自己（{voter_name}）的评价：",
                        ["优秀", "合格", "基本合格", "不合格"],
                        index=1,
                        horizontal=True,
                        key="self_vote"
                    )

                    # 提交按钮
                    submit_btn = st.form_submit_button("🗳️ 确认提交投票", type="primary")

                    # 提交校验与保存
                    if submit_btn:
                        # 统计优秀数量（互评+自评）
                        excellent_count = list(vote_dict.values()).count("优秀")
                        if self_eval == "优秀":
                            excellent_count += 1

                        # 校验优秀比例
                        if excellent_count > max_excellent:
                            st.error(f"""
                            ❌ 提交失败！
                            您评价的「优秀」人数为 {excellent_count} 人，
                            超过支部总人数30%的上限（{max_excellent}人），
                            请减少「优秀」评价人数后重新提交！
                            """)
                        else:
                            # 保存投票数据
                            new_vote = pd.DataFrame([{
                                '投票人': voter_name,
                                '投票详情': json.dumps(vote_dict, ensure_ascii=False)
                            }])
                            df_votes = pd.concat([df_votes, new_vote], ignore_index=True)
                            save_votes_data(df_votes)

                            # 更新自评等级到团员数据
                            latest_df = load_member_data()
                            latest_df.loc[latest_df['姓名'] == voter_name, '自评等级'] = self_eval
                            save_member_data(latest_df)

                            # 反馈成功
                            st.success("""
                            ✅ 投票提交成功！
                            感谢您的认真参与，可关闭此页面。
                            """)
                            st.balloons()

# ===================== 底部说明 =====================
st.divider()
st.markdown("""
<div style="text-align: center; color: #666;">
    © 2026 团员教育评议投票系统 | 技术支持：团支书
</div>
""", unsafe_allow_html=True)