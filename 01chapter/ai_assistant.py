import json
import os.path

import streamlit as st
from openai import OpenAI
import datetime

st.set_page_config(
    page_title="AI智能助理",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={}
)

#保存会话信息的函数
def save_session():
    if st.session_state.current_session:
        save_message = {
            "nickname": st.session_state.nick_name,
            "character": st.session_state.character,
            "current_session": st.session_state.current_session,
            "messages": st.session_state.messages
        }

        if not os.path.exists("sessions"):
            os.mkdir("sessions")
        with open(f"sessions/{st.session_state.current_session}.json", "w", encoding="utf-8") as f:
            json.dump(save_message, f, ensure_ascii=False, indent=2)

#获取当前时间
def get_now_time()->str:
    return datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

#加载所有会话列表
def load_sessions():
    session_list = []
    if os.path.exists("sessions"):
        fill_list = os.listdir("sessions")
        for filename in fill_list:
            if filename.endswith(".json"):
                session_list.append(filename[:-5])
    session_list.sort(reverse=True)
    return session_list

#加载制定历史会话
def load_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            with open(f"sessions/{session_name}.json", "r", encoding="utf-8") as f:
                session_data = json.load(f)
                st.session_state.nick_name = session_data["nickname"]
                st.session_state.character = session_data["character"]
                st.session_state.current_session = session_data["current_session"]
                st.session_state.messages = session_data["messages"]
    except Exception as e:
        st.error("加载会话失败")

def delete_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            os.remove(f"sessions/{session_name}.json")
            if session_name == st.session_state.current_session:
                st.session_state.messages = []
                st.session_state.current_session = get_now_time()
    except Exception as e:
        st.error("删除会话失败")

st.title("AI智能助理")

#系统提示词
system_prompt = "你叫%s,是一个非常博学的助理,上知天文下知地理,无所不知,能用浅显的语言讲清楚难解的问题,你的性格是%s"

#初始化聊天信息
if "messages" not in st.session_state:
    st.session_state.messages = []

if "nick_name" not in st.session_state:
    st.session_state.nick_name = "智者"

if "character" not in st.session_state:
    st.session_state.character = "内敛智慧博知"

if "current_session" not in st.session_state:
    st.session_state.current_session = get_now_time()

st.text(f"会话名称:{st.session_state.current_session}")
#展示聊天信息
for message in st.session_state.messages:
    st.chat_message(message["role"]).write(message["content"])
    # if message["role"] == "user":
    #     st.chat_message("user").write(message["content"])
    # else:
    #     st.chat_message("assistant").write(message["content"])

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"   # 不校验
)

#侧边栏
with st.sidebar:
    st.subheader("助理控制面板")
    if st.button("新建会话", width="stretch", icon="🖋️"):
        #1.保存当前会话
        save_session()

        #2.创建新会话
        if st.session_state.messages:
            st.session_state.messages = []
            st.session_state.current_session = get_now_time()
            save_session()
            st.rerun() #重新运行当前页面

    st.text("历史会话")
    session_list = load_sessions()
    for session in session_list:
        col1, col2 = st.columns([4,1])
        with col1:
            if st.button(session, width="stretch", icon="📝", key=f"load_{session}", type=("primary" if session==st.session_state.current_session else "secondary")):
                load_session(session)
                st.rerun()
        with col2:
            if st.button("", width="stretch", icon="❌", key=f"delete_{session}"):
                delete_session(session)
                st.rerun()

    st.divider()

    st.subheader("助理信息")
    nickname = st.text_input("助理昵称", placeholder="请输入助理的昵称", value=st.session_state.nick_name)
    if nickname:
        st.session_state.nick_name = nickname
    character = st.text_area("性格", placeholder="请输入助理的性格", value=st.session_state.character)
    if character:
        st.session_state.character = character



prompt = st.chat_input("请输入您要问的问题:")
if prompt:
    st.chat_message("user").write(prompt)
    #保存用户输入的提示词
    st.session_state.messages.append({"role": "user", "content": prompt})

    params = {
        "model": "deepseek-r1:7b",
        "messages": [
            {"role": "system", "content": system_prompt%(st.session_state.nick_name, st.session_state.character)},
            *st.session_state.messages
        ],
        "stream": True
    }
    resp = client.chat.completions.create(**params)

    resp_message = st.empty()
    full_resp = ""
    for chunk in resp:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            full_resp += content
            resp_message.chat_message("assistant").write(full_resp)


    # st.chat_message("assistant").write(resp.choices[0].message.content)
    st.session_state.messages.append({"role": "assistant", "content": full_resp})

    save_session()



