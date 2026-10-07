import streamlit as st
import requests

# ===================== 配置区 =====================
BACKEND_URL = "http://127.0.0.1:8000"

# ===================== 页面 =====================
st.title("📚 知识库文件管理")

# -------------------- 1. 文件上传 --------------------
st.markdown("### 📤 上传文档（TXT/PDF/DOCX）")
uploaded_file = st.file_uploader("选择文件", type=["txt", "pdf", "docx"])

if uploaded_file:
    st.info(f"当前文件：{uploaded_file.name}")
    if st.button("✅ 上传到知识库"):
        with st.spinner("解析与向量化中..."):
            try:
                files = {
                    "file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
                }
                res = requests.post(
                    f"{BACKEND_URL}/api/documents/upload",
                    files=files
                ).json()
                msg = res.get("msg", "")

                if "跳过" in msg:
                    st.warning(msg)
                elif "成功" in msg:
                    st.success(msg)
                else:
                    st.error(msg)
                st.rerun()
            except Exception as e:
                st.error(f"连接后端失败：{str(e)}")

# -------------------- 2. 文档列表 --------------------
st.divider()
st.markdown("### 📋 已上传文档")
try:
    res = requests.get(f"{BACKEND_URL}/api/documents").json()
    docs = res.get("data", [])
    if docs:
        for doc in docs:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{doc['filename']}**")
            with col2:
                st.caption(f"{doc.get('chunk_count', 0)} 个分块")
            with col3:
                if st.button("🗑️", key=f"del_{doc['filename']}"):
                    del_res = requests.delete(
                        f"{BACKEND_URL}/api/documents/{doc['filename']}"
                    ).json()
                    st.success(del_res.get("msg", ""))
                    st.rerun()
    else:
        st.caption("暂无文档，请先上传")
except Exception as e:
    st.error(f"获取文档列表失败：{str(e)}")

# -------------------- 3. 清空知识库 --------------------
st.divider()
st.markdown("### ⚠️ 清空整个知识库")
if st.button("💥 清空所有数据"):
    try:
        res = requests.post(f"{BACKEND_URL}/api/kb/clear").json()
        st.success(res.get("msg", ""))
        st.rerun()
    except:
        st.error("连接失败")
