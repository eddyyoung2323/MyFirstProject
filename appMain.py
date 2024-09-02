import streamlit as st
import requests
from mainMain import run_app
import base64
import os, random, logging
from PIL import Image

current_dir = os.path.dirname(os.path.abspath(__file__))

css_file = os.path.join(current_dir, 'css', 'style.css')

log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_file = os.path.join(log_dir, 'app.log')

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logging.root.addHandler(console_handler)

file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)
logging.root.addHandler(file_handler)

logging.root.setLevel(logging.INFO)

logger = logging.getLogger(__name__)

def get_base64_of_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def get_file_content_as_string(filepath):
    with open(filepath, 'r') as f:
        return f.read()


js_file = os.path.join(current_dir, 'static', 'js', 'audio_processing.js')
js_content = get_file_content_as_string(js_file)

st.markdown(f'<script>{js_content}</script>', unsafe_allow_html=True)

image1_base64 = get_base64_of_image(os.path.join(current_dir, 'static', 'images', '1.jpg'))
image2_base64 = get_base64_of_image(os.path.join(current_dir, 'static', 'images', '2.jpg'))

with open(css_file) as f:
    css = f.read()

css = css.replace('url(\'/static/images/1.jpg\')', f'url(data:image/jpeg;base64,{image1_base64})')
css = css.replace('url(\'/static/images/2.jpg\')', f'url(data:image/jpeg;base64,{image2_base64})')
st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

LOGIN_API_URL = "http://127.0.0.1:8090/api/collections/users/auth-with-password"
SIGNUP_API_URL = "http://127.0.0.1:8090/api/collections/users/records"
INVITE_CODE_API_URL = "http://127.0.0.1:8090/api/collections/invite_code/records"
USER_API_URL = "http://127.0.0.1:8090/api/collections/users/records"
API_KEY_API_URL = "http://127.0.0.1:8090/api/collections/api_key/records"

def display_logo():
    st.markdown("""
        <style>
        .block-container {
            margin-top: -1rem;
            padding-top: 0rem;
            padding-bottom: 0rem;
        }
        </style>
        """, unsafe_allow_html=True)
    
    col1, = st.columns(1)
    
    with col1:
        logo = Image.open("0.1/static/images/logo.png")
        logo = logo.resize((227, 43))
        st.image(logo, use_column_width=False)
        
def get_user_api_key(username, auth_token):
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        user_response = requests.get(f"{USER_API_URL}?filter=(username='{username}')", headers=headers)
        if user_response.status_code != 200:
            st.error("无法获取用户信息")
            return None
        
        user_data = user_response.json().get('items', [])[0]
        api_key_id = user_data.get('api_key_id')
        
        if not api_key_id:
            st.error(f"用户 {username} 没有关联的API密钥ID")
            return None
        
        api_key_response = requests.get(f"{API_KEY_API_URL}/{api_key_id}", headers=headers)
        if api_key_response.status_code != 200:
            st.error("无法获取API密钥")
            return None
        
        api_key_data = api_key_response.json()
        return api_key_data.get('key')
    
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {e}")
        return None
    except IndexError:
        st.error(f"用户名 {username} 不存在")
        return None
    
def check_credentials(username, password):
    try:
        response = requests.post(LOGIN_API_URL, json={
            'identity': username,
            'password': password
        })
        if response.status_code == 200:
            return True, response.json().get('token')
        else:
            return False, None
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {e}")
        return False, None

if 'last_api_key_index' not in st.session_state:
    st.session_state.last_api_key_index = -1

def register_user(username, password, invitation_code):
    try:
        filter_query = f'invite_code="{invitation_code}" && used=0'
        response = requests.get(f"{INVITE_CODE_API_URL}?filter={filter_query}")
        if not response.ok:
            raise ValueError(f'邀请码验证失败。状态码: {response.status_code}')
        
        result_list = response.json()
        if len(result_list['items']) == 0:
            raise ValueError('邀请码无效')
        
        invite_code_record = result_list['items'][0]
        if invite_code_record['used'] == 1:
            raise ValueError('邀请码已被使用')
        
        api_key_response = requests.get(f"{API_KEY_API_URL}?filter=(kind='trial')")
        if not api_key_response.ok:
            raise ValueError(f'无法获取API密钥。状态码: {api_key_response.status_code}')

        api_keys = api_key_response.json().get('items', [])
        if not api_keys:
            raise ValueError("没有可用的试用API密钥")

        if 'last_api_key_index' not in st.session_state:
            st.session_state.last_api_key_index = -1

        st.session_state.last_api_key_index = (st.session_state.last_api_key_index + 1) % len(api_keys)
        next_api_key = api_keys[st.session_state.last_api_key_index]

        print(f"Current API key index: {st.session_state.last_api_key_index}")
        print(f"Selected API key ID: {next_api_key['id']}")

        user_data = {
            'username': username,
            'password': password,
            'passwordConfirm': password,
            'api_key_id': next_api_key['id'],
            'invite_code': invitation_code, 
            'credits': 10
        }
        user_response = requests.post(SIGNUP_API_URL, json=user_data)
        
        if not user_response.ok:
            raise ValueError(f'注册失败。状态码: {user_response.status_code}')
        
        user = user_response.json()
        
        current_used_count = invite_code_record['used']

        new_used_count = current_used_count + 1

        invite_code_id = invite_code_record['id']
        update_response = requests.patch(f"{INVITE_CODE_API_URL}/{invite_code_id}", json={'used': new_used_count})

        if not update_response.ok:
            raise ValueError(f'邀请码更新失败。状态码: {update_response.status_code}')
        
        return user['id'] 
    
    except requests.exceptions.RequestException as e:
        st.error(f"网络请求错误: {str(e)}")
        return None
    except ValueError as e:
        st.error(str(e))
        return None
    except Exception as e:
        st.error(f"未预期的错误: {str(e)}")
        return None
    
def get_user_credits(username, auth_token):
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{USER_API_URL}?filter=(username='{username}')", headers=headers)
        if response.status_code == 200:
            items = response.json().get('items', [])
            if items:
                user_data = items[0]
                return user_data['id'], user_data['credits']
            else:
                st.error(f"用户名 {username} 不存在")
                return None, None
        else:
            st.error("无法获取用户点数")
            return None, None
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {e}")
        return None, None

def update_user_credits(user_id, new_credits, auth_token):
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.patch(f"{USER_API_URL}/{user_id}", json={"credits": new_credits}, headers=headers)
        if response.status_code == 200:
            return True
        else:
            st.error("无法更新用户点数")
            return False
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {e}")
        return False

def get_story_previews(auth_token):
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get("http://127.0.0.1:8090/api/collections/story/records?perPage=100", headers=headers)
        if response.status_code == 200:
            stories = response.json().get('items', [])
            selected_stories = random.sample(stories, min(6, len(stories)))
            previews = []
            for story in selected_stories:
                title = story.get('name', 'Untitled')
                text = story.get('storytext', '')
                sentences = text.split('。')
                max_start = max(0, len(sentences) - 5)
                if max_start > 0:
                    start = random.randint(0, max_start)
                    preview_sentences = sentences[start:start+5]
                else:
                    preview_sentences = sentences[:5]
                preview = '。'.join(preview_sentences) + '。' if preview_sentences else ''
                previews.append((title, preview))
            return previews
        else:
            st.error(f"无法获取故事预览。状态码: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"获取故事预览时发生错误: {str(e)}")
        return []

if 'inputs' not in st.session_state:
    st.session_state.inputs = False
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'auth_token' not in st.session_state:
    st.session_state.auth_token = None
if 'signup_mode' not in st.session_state:
    st.session_state.signup_mode = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'credits' not in st.session_state:
    st.session_state.credits = None
if 'story_generated' not in st.session_state:
    st.session_state.story_generated = False

st.markdown("""
    <style>
    div[class*="stButton"] > button {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

if st.session_state.signup_mode:
    display_logo()
    st.markdown(f'</br></br></br><h3 style="text-align:center">✑&nbsp;&nbsp;注册新用户&nbsp;&nbsp;</h3>', unsafe_allow_html=True)
    form_css = """
    <style>
    [data-testid="stForm"] {
        border: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    .stForm > div > div > div > div {
        border: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    </style>
    """
    st.markdown(form_css, unsafe_allow_html=True)
    with st.form("signup_form"):
        username = st.text_input("❀&nbsp;&nbsp;用户名", key="username1")
        password = st.text_input("❅&nbsp;&nbsp;密码（至少8位）", type="password")
        password_confirm = st.text_input("❅&nbsp;&nbsp;确认密码", type="password", key="password1")
        invitation_code = st.text_input("⛦&nbsp;&nbsp;邀请码")
        
        col1, col2 = st.columns(2)
        with col1:
            confirm_button = st.form_submit_button("➯&nbsp;&nbsp;确认")
        with col2:
            back_to_login_button = st.form_submit_button("♲&nbsp;&nbsp;返回")

    if confirm_button:
        if password != password_confirm:
            st.error("密码不匹配")
        else:
            # user_id = register_user(username, password, invitation_code)
            # if user_id:
            #     st.success("注册成功！请登录。")
            #     st.session_state.signup_mode = False
            #     st.rerun()
            # else:
            #     st.error("注册失败，请检查错误信息并重试。")
            st.success("注册成功！请登录。")
            st.session_state.signup_mode = False
            st.rerun()

    if back_to_login_button:
        st.session_state.signup_mode = False
        st.rerun()

if not st.session_state.logged_in and not st.session_state.signup_mode:
    display_logo()
    st.markdown(f'</br></br></br></br><h3 style="text-align:center">✞&nbsp;&nbsp;登陆&nbsp;&nbsp;</h3>', unsafe_allow_html=True)
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
    username = st.text_input("❀&nbsp;&nbsp;用户名", key="username2")
    password = st.text_input("❅&nbsp;&nbsp;密码", type="password", key="password2")
    col1, col2 = st.columns(2)
    with col1:
        login_button = st.button("➯&nbsp;&nbsp;确认")
    with col2:
        signup_mode_button = st.button("✑&nbsp;&nbsp;注册新用户")
    
    if login_button:
        # success, token = check_credentials(username, password)
        # if success:
        #     st.session_state.logged_in = True
        #     st.session_state.auth_token = token
        #     st.session_state.username = username
        #     st.rerun()
        # else:
        #     st.error("用户名或者密码无效")

        st.session_state.logged_in = True
        st.session_state.auth_token = ''
        st.session_state.username = username
        st.rerun()

    if signup_mode_button:
        st.session_state.signup_mode = True
        st.rerun()
        
if st.session_state.logged_in:
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
    # if st.session_state.credits is None:
    #     st.session_state.user_id, st.session_state.credits = get_user_credits(st.session_state.username, st.session_state.auth_token)

    api_key = 'yLYf7jv3nuuGMePWA6PL8DApS5x3fsY27T9bwGhL'
    # if st.session_state.user_id is not None and st.session_state.credits is not None:
    #     api_key = get_user_api_key(st.session_state.username, st.session_state.auth_token)
    if api_key:
        if api_key:
            inputs, generate_story_button = run_app(st.session_state.logged_in, st.session_state.username, api_key)
        else:
            st.error("无法获取API密钥，请联系管理员")

        if not st.session_state.story_generated:
            st.markdown("</br></br><div style='color: #444; font-size:1rem; text-align: center;'>✢✢✢✢✢✢&nbsp;&nbsp;&nbsp;&nbsp;尝鲜一下&nbsp;&nbsp;&nbsp;&nbsp;✢✢✢✢✢✢</div>", unsafe_allow_html=True)
            # previews = get_story_previews(st.session_state.auth_token)
            # cols = st.columns(3)
            # for i, (title, preview) in enumerate(previews):
            #     with cols[i % 3]:
            #         with st.expander(f'✢&nbsp;&nbsp;&nbsp;&nbsp;{title}', expanded=False):
            #             st.markdown(f'<p>{preview}</p>', unsafe_allow_html=True)
                        
        logout_button = st.button("🛏 &nbsp;&nbsp;&nbsp;登出")
        if logout_button:
            st.session_state.logged_in = False
            st.session_state.auth_token = None
            st.session_state.username = None
            st.session_state.user_id = None
            st.session_state.credits = None
            st.rerun()

    else:
        st.error("用户信息无效，请重新填写。")
        st.session_state.logged_in = False
        st.rerun() 