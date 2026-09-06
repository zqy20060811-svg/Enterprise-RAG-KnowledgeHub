import streamlit as st
import requests
import uuid

# ===================== 配置区 =====================
BACKEND_URL = "http://127.0.0.1:8000"
CHAT_API = f"{BACKEND_URL}/api/chat/stream"

# ===================== 页面初始化 =====================
st.title("📚 企业知识库智能问答")

# 初始化会话ID
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# 展示历史消息
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ===================== 核心交互逻辑 =====================
prompt = st.chat_input("请输入你的问题...")

if prompt:
    # 1. 保存用户问题并展示
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. 构建请求数据
    payload = {
        "query": prompt,
        "session_id": st.session_state.session_id
    }

    # 3. 调用后端流式接口
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            with requests.post(
                    CHAT_API,
                    json=payload,
                    stream=True,
                    timeout=120
            ) as response:

                if response.status_code != 200:
                    st.error(f"❌ 请求失败！状态码：{response.status_code}")
                else:
                    # 4. 流式接收并显示（打字机效果）
                    for chunk in response.iter_content(chunk_size=1, decode_unicode=True):
                        if chunk:
                            full_response += chunk
                            message_placeholder.markdown(full_response + "▌")

                    message_placeholder.markdown(full_response)

        except requests.exceptions.ConnectionError:
            st.error("❌ 无法连接到后端服务！请检查后端是否启动（uvicorn main:app --reload）")
        except Exception as e:
            st.error(f"❌ 发生错误：{str(e)}")

    # 5. 保存AI回答
    st.session_state.messages.append({"role": "assistant", "content": full_response})
