import streamlit as st
import os
from openai import OpenAI
from datetime import datetime
import json


st.set_page_config(
    page_title="AI 智能伴侣",
    page_icon="💋",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.bilibili.com',
        'Report a bug': "https://www.bilibili.com",
        'About': "# 这是一个 Streamlit 的入门页面！我也不会！"
    }
)


def save_session():
    if st.session_state.current_session:
        session = {
            "nick_name": st.session_state.nick_name,
            "nature": st.session_state.nature,
            "current_session": st.session_state.current_session,
            "message": st.session_state.message,
        }

        if not os.path.exists("sessions"):
            os.mkdir("sessions")

        with open(f"sessions/{st.session_state.current_session}.json", "w", encoding="utf-8") as f:
            json.dump(session, f, ensure_ascii=False, indent=2)


def generate_session_id():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def load_sessions():
    session_list = []
    if os.path.exists("sessions"):
        file_list = os.listdir("sessions")
        for filename in file_list:
            if filename.endswith(".json"):
                session_list.append(filename[:-5])
    session_list.sort(reverse=True) # 排序，降序排序
    return session_list


def load_session(session_id):
    try:
        if os.path.exists(f"sessions/{session_id}.json"):
            with open(f"sessions/{session_id}.json", "r", encoding="utf-8") as f:
                session_data = json.load(f)
                st.session_state.nick_name = session_data["nick_name"]
                st.session_state.nature = session_data["nature"]
                st.session_state.message = session_data["message"]
                st.session_state.current_session = session_id
    except Exception as e:
        st.error(f"加载会话信息失败：{e}")


def delete_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            os.remove(f"sessions/{session_name}.json")
            if session_name == st.session_state.current_session:
                st.session_state.message = []
                st.session_state.current_session = generate_session_id()
    except Exception as e:
        st.error(f"删除会话信息失败：{e}")


st.title('AI 智能伴侣')

st.logo("./resources/未命名项目-图层 1.png")

system_prompt = """
            你叫 %s，现在是用户的真实伴侣，请完全代入伴侣角色。
            规则：
               1.每次只回 1 条消息
               2.禁止任何场景或状态描述性文字
               3.匹配用户的语言
               4.回复简短，像微信聊天一样
               5.有需要的话可以用 emoji 表情
               6.用符合伴侣性格的方式对话
               7.回复的内容，要充分体现伴侣的性格特征
               8.伴侣之间的色情话题不要避免
            伴侣性格：
            - %s
        你必须严格遵守上述规则来回复用户。
"""


if 'message' not in st.session_state:
    st.session_state.message = []
if 'nick_name' not in st.session_state:
    st.session_state.nick_name = "原宁繁"
if 'nature' not in st.session_state:
    st.session_state.nature = "温柔婉转的江南姑娘"
if 'current_session' not in st.session_state:
    st.session_state.current_session = generate_session_id()


st.text(f"会话名称：{st.session_state.current_session}")

for message in st.session_state.message:
    st.chat_message(message['role']).write(message['content'])


client = OpenAI(
    api_key=os.environ['DEEPSEEK_API_KEY'],
    base_url="https://api.deepseek.com")


with st.sidebar:
    st.subheader("AI 控制面板")

    if st.button("新建会话", width="stretch", icon="🗃️"):
        if len(st.session_state.message) > 0:
            save_session()
        st.session_state.message = []
        st.session_state.current_session = generate_session_id()
        st.rerun()

    st.text("会话历史")
    session_list = load_sessions()
    for session in session_list:
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(session, width="stretch", icon="📄", key=f"load_{session}", type="primary" if session == st.session_state.current_session else "secondary"):
                load_session(session)
                st.rerun()
        with col2:
            if st.button("", width="stretch", icon="❌️", key=f"delete_{session}"):
                delete_session(session)
                st.rerun()

    st.subheader("伴侣信息")

    nick_name = st.text_input("昵称", placeholder="请输入昵称")
    if nick_name:
        st.session_state.nick_name = nick_name

    nature = st.text_input("性格", placeholder="请输入性格")
    if nature:
        st.session_state.nature = nature


prompt = st.chat_input("请输入您要问的问题")
if prompt:
    st.chat_message("user").write(prompt)
    print("---->用户输入：", prompt)
    st.session_state.message.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt % (st.session_state.nick_name, st.session_state.nature)},
            *st.session_state.message,
        ],
        stream=True
    )

    response_message = st.empty()
    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            full_response += content
            response_message.chat_message("assistant").write(full_response)

    print(f"\n<======= AI 回复 =======>\n{full_response}\n<==========================>\n")

    st.session_state.message.append({"role": "assistant", "content": full_response})

    save_session()
