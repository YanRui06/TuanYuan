import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 页面基础设置
st.set_page_config(
    page_title="团员教育评议投票系统",
    page_icon="🏫",
    layout="wide"
)

# 初始化会话状态（存储数据）
if 'member_data' not in st.session_state:
    st.session_state.member_data = pd.DataFrame({
        '姓名': [],
        '是否新团员(未满一年)': [],
        '是否有处分/挂科': [],
        '自评等级': [],
        '互评等级': [],
        '最终评议等级': [],
        '备注': []
    })

if 'class_name' not in st.session_state:
    st.session_state.class_name = ""

if 'total_members' not in st.session_state:
    st.session_state.total_members = 1

# 核心函数：校验优秀比例和评优资格
def validate_evaluation(df, total_members):
    max_excellent = int(total_members * 0.3)  # 30%上限
    excellent_count = len(df[df['最终评议等级'] == '优秀'])
    
    # 检查挂科/处分人员评优
    disqualified_excellent = df[(df['是否有处分/挂科'] == '是') & (df['最终评议等级'] == '优秀')]
    if len(disqualified_excellent) > 0:
        st.error(f"❌ 错误：以下团员有处分/挂科，不能评为优秀：{', '.join(disqualified_excellent['姓名'].tolist())}")
        return False
    
    # 检查新团员参评
    new_member_evaluate = df[(df['是否新团员(未满一年)'] == '是') & (df['最终评议等级'] != '不参评')]
    if len(new_member_evaluate) > 0:
        st.error(f"❌ 错误：以下新团员(未满一年)不能参评，需标记为'不参评'：{', '.join(new_member_evaluate['姓名'].tolist())}")
        return False
    
    # 检查优秀比例
    if excellent_count > max_excellent:
        st.error(f"❌ 错误：优秀团员数量({excellent_count}人)超过30%上限({max_excellent}人)，请调整！")
        return False
    
    st.success(f"✅ 校验通过！优秀团员数量({excellent_count}人) ≤ 30%上限({max_excellent}人)")
    return True

# 核心函数：生成Excel文件
def generate_excel(df, class_name):
    # 整理输出格式
    output_df = df[['姓名', '是否新团员(未满一年)', '是否有处分/挂科', '自评等级', '互评等级', '最终评议等级', '备注']].copy()
    output_df.columns = ['姓名', '是否新团员', '是否有处分/挂科', '自评等级', '互评等级', '最终评议等级', '备注']
    
    # 添加统计信息
    stats_df = pd.DataFrame({
        '姓名': ['统计信息', '', ''],
        '是否新团员': [f'团支部总人数：{st.session_state.total_members}', f'优秀上限：{int(st.session_state.total_members*0.3)}', f'实际优秀人数：{len(df[df["最终评议等级"]=="优秀"])}'],
        '是否有处分/挂科': ['', '', ''],
        '自评等级': ['', '', ''],
        '互评等级': ['', '', ''],
        '最终评议等级': ['', '', ''],
        '备注': [f'导出时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}', '公示期：3天', f'制表人：{class_name}团支书']
    })
    
    final_df = pd.concat([output_df, stats_df], ignore_index=True)
    
    # 保存为Excel
    file_name = f"{class_name}团员教育评议结果.xlsx"
    final_df.to_excel(file_name, index=False, engine='openpyxl')
    return file_name, final_df

# 页面布局
st.title("🏫 团员教育评议投票统计系统")
st.divider()

# 第一步：录入团支部基础信息
st.subheader("📋 第一步：录入团支部基础信息")
col1, col2 = st.columns(2)
with col1:
    class_name = st.text_input("请输入班级名称（如：2023级计算机1班）", value=st.session_state.class_name)
    st.session_state.class_name = class_name
with col2:
    total_members = st.number_input("请输入团支部总人数（智慧团建人数）", min_value=1, value=st.session_state.total_members)
    st.session_state.total_members = total_members

# 第二步：添加/编辑团员信息
st.subheader("✏️ 第二步：录入/编辑团员信息")
tab1, tab2, tab3 = st.tabs(["批量导入(Excel)", "添加单名团员", "编辑现有团员"])

with tab1:
    st.info("💡 提示：请确保Excel文件包含必备列：`姓名`。可选列包：`是否新团员(未满一年)`, `是否有处分/挂科`, `自评等级`, `互评等级`, `最终评议等级`, `备注`等")
    # 可以提供一个下载模板的功能
    template_df = pd.DataFrame(columns=['姓名', '是否新团员(未满一年)', '是否有处分/挂科', '自评等级', '互评等级', '最终评议等级', '备注'])
    st.download_button("下载Excel模板", data=template_df.to_csv(index=False, encoding='utf-8-sig'), file_name="团员导入模板.csv", mime="text/csv")
    
    uploaded_file = st.file_uploader("📥 选择Excel文件进行上传", type=['xlsx', 'xls'])
    if uploaded_file is not None:
        if st.button("开始导入数据", type="primary"):
            try:
                df_imported = pd.read_excel(uploaded_file, dtype=str) # 读取为字符串防止格式问题
                
                # 检查必备列
                if '姓名' not in df_imported.columns:
                    st.error("❌ 导入失败！Excel文件中没有找到名为『姓名』的列！")
                else:
                    standard_cols = list(st.session_state.member_data.columns)
                    
                    # 处理缺失列，统一设置为默认值或空字符串
                    for col in standard_cols:
                        if col not in df_imported.columns:
                            if col in ['是否新团员(未满一年)', '是否有处分/挂科']:
                                df_imported[col] = '否'
                            else:
                                df_imported[col] = ''
                    
                    # 仅保留所需列，清理空值（将NaN和字符串nan转为空）
                    df_imported = df_imported[standard_cols].fillna('')
                    df_imported = df_imported.replace('nan', '')
                    
                    # 过滤姓名为空的行
                    df_imported = df_imported[df_imported['姓名'].str.strip() != '']
                    
                    if len(df_imported) > 0:
                        # 姓名去重合并
                        combined_df = pd.concat([st.session_state.member_data, df_imported])
                        combined_df = combined_df.drop_duplicates(subset=['姓名'], keep='last').reset_index(drop=True)
                        st.session_state.member_data = combined_df
                        st.success(f"✅ 成功读取并导入 {len(df_imported)} 名团员的数据！（如果遇到同名数据，已进行覆盖处理）")
                    else:
                        st.warning("⚠️ 没找到有效的团员姓名数据。")
            except Exception as e:
                st.error(f"❌ 读取文件出错：{str(e)}")

with tab2:
    col1, col2, col3 = st.columns(3)
    with col1:
        member_name = st.text_input("团员姓名")
    with col2:
        is_new_member = st.selectbox("是否新团员(未满一年)", ["否", "是"])
    with col3:
        has_punishment = st.selectbox("是否有处分/挂科", ["否", "是"])
    
    if st.button("添加团员", type="primary"):
        if not member_name:
            st.warning("请输入团员姓名！")
        else:
            # 检查是否已存在
            if member_name in st.session_state.member_data['姓名'].tolist():
                st.warning(f"团员{member_name}已存在，请勿重复添加！")
            else:
                new_row = pd.DataFrame({
                    '姓名': [member_name],
                    '是否新团员(未满一年)': [is_new_member],
                    '是否有处分/挂科': [has_punishment],
                    '自评等级': [""],
                    '互评等级': [""],
                    '最终评议等级': ["不参评" if is_new_member == "是" else ""],
                    '备注': [""]
                })
                st.session_state.member_data = pd.concat([st.session_state.member_data, new_row], ignore_index=True)
                st.success(f"✅ 成功添加团员：{member_name}")

with tab3:
    # 选择要编辑的团员
    if len(st.session_state.member_data) > 0:
        selected_member = st.selectbox("选择要编辑的团员", st.session_state.member_data['姓名'].tolist())
        member_index = st.session_state.member_data[st.session_state.member_data['姓名'] == selected_member].index[0]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            new_self_grade = st.selectbox("自评等级", ["", "优秀", "合格", "基本合格", "不合格"], 
                                        index=list(st.session_state.member_data.loc[member_index, '自评等级']).index(st.session_state.member_data.loc[member_index, '自评等级']) if st.session_state.member_data.loc[member_index, '自评等级'] else 0)
        with col2:
            new_mutual_grade = st.selectbox("互评等级", ["", "优秀", "合格", "基本合格", "不合格"],
                                          index=list(st.session_state.member_data.loc[member_index, '互评等级']).index(st.session_state.member_data.loc[member_index, '互评等级']) if st.session_state.member_data.loc[member_index, '互评等级'] else 0)
        with col3:
            # 新团员默认不参评，不可修改
            if st.session_state.member_data.loc[member_index, '是否新团员(未满一年)'] == "是":
                new_final_grade = st.selectbox("最终评议等级", ["不参评"], disabled=True)
            else:
                new_final_grade = st.selectbox("最终评议等级", ["", "优秀", "合格", "基本合格", "不合格"],
                                             index=list(st.session_state.member_data.loc[member_index, '最终评议等级']).index(st.session_state.member_data.loc[member_index, '最终评议等级']) if st.session_state.member_data.loc[member_index, '最终评议等级'] else 0)
        
        col4, col5 = st.columns(2)
        with col4:
            new_note = st.text_input("备注（如：公示期修改记录）", value=st.session_state.member_data.loc[member_index, '备注'])
        with col5:
            if st.button("保存修改"):
                st.session_state.member_data.loc[member_index, '自评等级'] = new_self_grade
                st.session_state.member_data.loc[member_index, '互评等级'] = new_mutual_grade
                st.session_state.member_data.loc[member_index, '最终评议等级'] = new_final_grade
                st.session_state.member_data.loc[member_index, '备注'] = new_note
                st.success(f"✅ 已更新团员{selected_member}的信息！")
        
        if st.button("删除该团员", type="secondary", icon="🗑️"):
            st.session_state.member_data = st.session_state.member_data.drop(member_index)
            st.success(f"✅ 已删除团员{selected_member}！")
            st.rerun()
    else:
        st.info("暂无团员信息，请先在「添加新团员」标签页录入！")

# 第三步：查看和校验数据
st.subheader("📊 第三步：查看并校验评议结果")
if len(st.session_state.member_data) > 0:
    # 显示当前数据表格
    st.dataframe(st.session_state.member_data, use_container_width=True)
    
    # 校验按钮
    if st.button("🔍 校验评议规则", type="primary"):
        validate_evaluation(st.session_state.member_data, st.session_state.total_members)
    
    # 导出Excel按钮
    if st.button("📥 导出Excel表格", type="secondary"):
        if not st.session_state.class_name:
            st.warning("请先填写班级名称！")
        elif validate_evaluation(st.session_state.member_data, st.session_state.total_members):
            file_name, final_df = generate_excel(st.session_state.member_data, st.session_state.class_name)
            # 提供下载链接
            st.success(f"✅ Excel文件已生成：{file_name}")
            st.download_button(
                label="点击下载Excel文件",
                data=final_df.to_csv(index=False, encoding='utf-8-sig'),
                file_name=file_name.replace('.xlsx', '.csv'),  # Streamlit直接下载Excel需额外配置，先提供CSV（Excel可直接打开）
                mime="text/csv"
            )
else:
    st.info("暂无团员数据，请先录入团员信息！")

# 重置功能
st.divider()
if st.button("🆘 重置所有数据", type="secondary"):
    st.session_state.member_data = pd.DataFrame({
        '姓名': [],
        '是否新团员(未满一年)': [],
        '是否有处分/挂科': [],
        '自评等级': [],
        '互评等级': [],
        '最终评议等级': [],
        '备注': []
    })
    st.session_state.class_name = ""
    st.session_state.total_members = 0
    st.success("✅ 已重置所有数据！")