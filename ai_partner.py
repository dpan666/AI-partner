import os
import streamlit as st
from openai import OpenAI
from datetime import datetime
import json

# 页面设置
st.set_page_config(
    page_title="AI-智能伴侣",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
    }
)

# 截取会话对象中倒数第二行用户的对话函数
def session_split(obj):
    try:
        str =obj['message'][-2]['content']
        if len(str) <= 15:
            return str
        else:
            return str[:15]+'...'
    except:
        try:
            str = obj['message'][-1]['content']
            if len(str) <= 15:
                return str
            else:
                return str[:15] + '...'
        except:
            return '...'

# 获取当前会话时间函数
def now_session_time():
    return datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

# 保存会话信息函数
def save_session():
    # 1.保存当前会话信息
    if st.session_state.message:
        # 构建新的会话对象
        session_data = {
            'nick_name': st.session_state.nick_name,
            'nature': st.session_state.nature,
            'rule': st.session_state.rule,
            'current_session': st.session_state.current_session,
            'message': st.session_state.message,
        }
        # 创建一个文件夹
        if not os.path.exists('./sessions'):
            os.mkdir('sessions')
        # 保存会话数据
        with open(f'./sessions/{st.session_state.current_session}.json', 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=4)

# 加载所有所有的会话列表信息
def load_sessions():
    session_list = []
    # 加载sessions文件夹下的所有json文件
    if os.path.exists('./sessions'):
        file_list = os.listdir('./sessions')
        for file in file_list:
            if file.endswith('.json'):
                with open(f'./sessions/{file}','r',encoding='utf-8') as f:
                    obj = json.load(f)
                    session_list.append({'time':file[:-5],'session':session_split(obj)})
    return session_list[::-1]

# 加载指定会话信息
def load_session(session_time):
    try:
        if os.path.exists(f'./sessions/{session_time}.json'):
            with open(f'./sessions/{session_time}.json','r',encoding='utf-8') as f:
                session_data = json.load(f)
                st.session_state.message = session_data['message']
                st.session_state.nick_name = session_data['nick_name']
                st.session_state.nature = session_data['nature']
                st.session_state.current_session = session_data['current_session']
    except Exception:
        st.error('加载会话失败!')

# 根据会话时间删除指定会话
def del_session(session_time):
    try:
        if os.path.exists(f'./sessions/{session_time}.json'):
            os.remove(f'./sessions/{session_time}.json')
    except Exception:
        st.error('删除失败')

# 大标题
st.title('AI智能伴侣')

# logo
st.logo('./resources/logo.png')
# 初始化对话信息
if 'message' not in st.session_state:
    st.session_state.message = []
# 初始化昵称信息
if 'nick_name' not in st.session_state:
    st.session_state.nick_name = '小甜甜'
# 初始化性格信息
if 'nature' not in st.session_state:
    st.session_state.nature = '活泼开朗的可爱女孩'
# 初始化规则信息
if 'rule' not in st.session_state:
    st.session_state.rule = '''1. 每次只回1条消息
2. 禁止任何场景或状态描述性文字
3. 匹配用户的语言
4. 回复简短，像微信聊天一样
5. 有需要的话可以用❤️🌸等emoji表情
6. 用符合伴侣性格的方式对话
7. 回复的内容, 要充分体现伴侣的性格特征'''
# 会话标识
if 'current_session' not in st.session_state:
    st.session_state.current_session = now_session_time()

# 系统提示词
system_prompt = f"""
你叫{st.session_state.nick_name}，现在是用户的真实伴侣，请完全代入伴侣角色。：
伴侣性格:{st.session_state.nature}
规则:{st.session_state.rule}       
你必须严格遵守上述规则来回复用户。
"""

# 遍历展示聊天信息
for message in st.session_state.message:
    st.chat_message(message['role']).write(message['content'])

# 消息输入框
prompt = st.chat_input('请输入......')

if prompt:
    st.chat_message('user').write(prompt)
    print('--->调用ai大模型,提示词:', prompt)
    # 保存用户输入的提示词
    st.session_state.message.append({'role': 'user', 'content': prompt})  # 存入消息

    # 调用AI大模型
    client = OpenAI(
        base_url='http://localhost:11434/v1/',
        api_key='ollama',  # required but ignored
    )
    chat_completion = client.chat.completions.create(
        messages=[
            {'role': 'system', 'content': system_prompt},
            *st.session_state.message
        ],
        model='qwen2.5-coder:7b',
        stream=True,
    )

    # 流式输出
    response_message = st.empty()  # 创建一个空组件,用于展示大模型返回的结果
    full_response = ''  # 初始化保存的
    for chunk in chat_completion:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            full_response += content
            response_message.chat_message('assistant').write(full_response)
    # 保存大模型返回的结果用于页面展示
    st.session_state.message.append({'role': 'assistant', 'content': full_response})

# 保存会话信息（必须在侧边栏渲染之前，确保侧边栏读取到最新数据）
save_session()

# 左侧侧边栏
with st.sidebar:  # with streamlit中的上下文管理器,只要在with语句块中,所有组件都会被渲染到侧边栏中
    st.header('AI控制面板')
    if st.button('新建会话', width='stretch', icon='✏️'):
        if not st.session_state.message:
            st.warning('当前已是最新会话')
        else:
            # 1.保存当前会话信息
            save_session()
            # 2.清空当前会话
            st.session_state.message = []
            st.session_state.current_session = now_session_time()
            # 3.刷新页面
            st.rerun()
    # 会话历史
    st.header('会话历史')
    session_list = load_sessions()
    for session in session_list:
        col1,col2 = st.columns([0.85,0.15])
        with col1:
            # 加载会话信息
            if st.button(':'+session['session'],icon = '🤓',width='stretch',key=session['time']+'_load',type='primary' if session['time'] ==st.session_state.current_session else 'secondary'):
                load_session(session['time'])
                st.rerun()
        with col2:
            # 删除会话
            if st.button('',icon = '❌',width='stretch',key=session['time']+'_del'):
                del_session(session['time'])
                if session['time'] == st.session_state.current_session:
                    st.session_state.message = []
                st.rerun()
    # 伴侣信息
    st.header('伴侣信息')
    # 昵称输入框
    nick_name = st.text_input('昵称', value=st.session_state.nick_name)
    if nick_name:
        st.session_state.nick_name = nick_name
    # 性格输入框
    nature = st.text_area('性格', value=st.session_state.nature)
    if nature:
        st.session_state.nature = nature
    # 规则输入框
    rule = st.text_area('规则', value=st.session_state.rule)
    if rule:
        st.session_state.rule = rule