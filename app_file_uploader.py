# 导入依赖
import streamlit as st
import requests

# ===================== 【和你后端完全一致，一字不差】 =====================
BACKEND_URL = "http://127.0.0.1:8000"
API_TOKEN = "600123"
HEADERS = {"token": API_TOKEN}

# ===================== 页面 =====================
st.title("📚 知识库文件上传管理")

# -------------------- 1. 文件上传 --------------------
st.markdown("### 📤 上传文档（TXT/PDF/DOCX）")
uploaded_file = st.file_uploader("选择文件", type=["txt", "pdf", "docx"])

if uploaded_file:
    st.info(f"当前文件：{uploaded_file.name}")

    if st.button("✅ 上传到知识库"):
        with st.spinner("处理中..."):
            try:
                # 调用后端接口
                files = {
                    "file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
                }
                response = requests.post(
                    f"{BACKEND_URL}/file/upload",
                    files=files,
                    headers=HEADERS
                )
                res = response.json()
                msg = res.get("msg", "")

                # ===================== 核心：原样显示后端返回的提示 =====================
                if "跳过" in msg:
                    st.warning(msg)  # 重复：黄色警告
                elif "成功" in msg:
                    st.success(msg)  # 成功：绿色
                else:
                    st.error(msg)  # 失败：红色

            except Exception as e:
                st.error(f"连接后端失败：{str(e)}")

# -------------------- 2. 按文件名删除 --------------------
st.divider()
st.markdown("### 🗑️ 删除知识库文件")
filename = st.text_input("输入完整文件名（如：测试文档）")
if st.button("🗑️ 删除文件"):
    if filename:
        try:
            res = requests.post(
                f"{BACKEND_URL}/vector/delete",
                params={"filename": filename},
                headers=HEADERS
            ).json()
            msg = res.get("msg", "")
            st.success(msg) if "成功" in msg else st.error(msg)
        except:
            st.error("连接失败")
    else:
        st.warning("请输入文件名")

# -------------------- 3. 清空全部数据 --------------------
st.divider()
st.markdown("### ⚠️ 清空整个知识库")
if st.button("💥 清空所有数据"):
    try:
        res = requests.post(f"{BACKEND_URL}/vector/clear", headers=HEADERS).json()
        msg = res.get("msg", "")
        st.success(msg) if "成功" in msg else st.error(msg)
    except:
        st.error("连接失败")