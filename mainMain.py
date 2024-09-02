import streamlit as st
import io, base64, zipfile, json, requests, re, logging, os
from io import BytesIO
from cohere_gen import get_llm_response, text_to_speech, get_access_token, split_text
from config_manage import get_user_configurations, save_configuration, delete_configuration, validate_config_name
from error_handle import handle_llm_error, handle_tts_error, handle_audio_processing_error, handle_credit_error
from sidebarMain import display_sidebar
from PIL import Image
from streamlit.components.v1 import html

st.set_page_config(page_title="YeahWrite", layout="wide")
current_dir = os.path.dirname(os.path.abspath(__file__))

log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_file = os.path.join(log_dir, 'app.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

subscription_key = 'PLESAE USE YOUR OWN AZURE SUBSCRIPTION KEY' 
service_region = ''
tts_endpoint = f''
token_endpoint = f''


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
        logo = Image.open("static/images/logo.png")
        logo = logo.resize((227, 42))
        st.image(logo, use_column_width=False)

def store_generated_story(username, auth_token, story_text, prompt_parts):
    try:        
        title_match = re.search(r'《(.*?)》', story_text)
        story_title = title_match.group(1) if title_match else "无题"
        
        joined_prompt = "; ".join(prompt_parts)

        story_data = {
            "name": story_title,
            "storytext": story_text,
            "user": username,
            "configused": joined_prompt 
        }
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post("http://127.0.0.1:8090/api/collections/story/records", json=story_data, headers=headers)
        
        if response.status_code == 200:
            st.success("文字部分已准备好。")
            return True
        else:
            logger.error(f"文字准备时出错。状态码: {response.status_code}, 响应: {response.text}")
            st.error(f"文字准备时出错。状态码: {response.status_code}, 响应: {response.text}")
            return False
    
    except requests.exceptions.RequestException as e:
        logger.error(f"文字准备时发生错误: {str(e)}")
        st.error(f"文字准备时发生错误: {str(e)}")
        return False

def get_text_downloader_html(text, file_label='File'):
    bin_str = base64.b64encode(text.encode()).decode()
    href = f'<a href="data:text/plain;base64,{bin_str}" download="{file_label}">Download {file_label}</a>'
    return href

def run_app(logged_in, username, api_key):
    display_logo()    

    if not st.session_state.story_generated:
        inputs, generate_story_button = display_sidebar(username)
        if inputs is None and generate_story_button is None:
            inputs = st.session_state.get('inputs', [])
            generate_story_button = True 
            st.session_state['inputs'] = inputs
        
        alert1 = st.markdown("</br><div style='font-size:2rem;color: #955;text-align: center;'>⚜&nbsp;&nbsp;<b>梦呓絮语</b>&nbsp;&nbsp;⚜</div></br></br><div style='color: #444; font-size: 1rem; text-align: center;'>⚥&nbsp;&nbsp;欢迎进入为你量身打造的性感文学世界！在这里探索你的秘密幻想。&nbsp;&nbsp;⚥</div><div style='font-size:1rem;color: #a44; text-align: center;'>⚜&nbsp;&nbsp;点击左侧配置面板，开启您的幻想之旅。&nbsp;&nbsp;⚜</div>", unsafe_allow_html=True)

    else:
        inputs = st.session_state.get('inputs', [])
        generate_story_button = False

    generated_text_placeholder = st.empty()

    # def deduct_credit():
    #     nonlocal credits
    #     if credits > 0:
    #         new_credits = credits - 1
    #         if update_user_credits(user_id, new_credits, auth_token):
    #             credits = new_credits
    #             st.sidebar.write(f"你还能生成 {credits} 个故事")
    #             return True
    #     handle_credit_error()
    #     return False

    def create_zip_file(text_content, audio_content):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            zip_file.writestr("story.txt", text_content)
            zip_file.writestr("story.mp3", audio_content.getvalue())
        return zip_buffer.getvalue()
    
    def create_download_link(content, filename, link_text):
        b64 = base64.b64encode(content).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}" class="download-link">{link_text}</a>'
        return href

    st.markdown("""
    <style>
        .download-link {
            display: inline-block;
            padding: 10px 20px;
            border: 1px solid rgb(71, 41, 41);
            background-color: transparent;
            color: rgb(71, 41, 41);
            text-align: center;
            text-decoration: none;
            font-size: 1.2rem;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 5px;
        }
    </style>
    """, unsafe_allow_html=True)

    def generate_story():
        try:
            prompt_parts = []
            if st.session_state.inputs[0] and st.session_state.inputs[0] not in ["默认随机", "自定义"]:
                prompt_parts.append(f"「题材」：{st.session_state.inputs[0]}")
            if st.session_state.inputs[1]:
                prompt_parts.append(f"「情色类型」：{'、'.join(st.session_state.inputs[1])}")
            if st.session_state.inputs[2] and st.session_state.inputs[2] not in ["默认随机", "自定义"]:
                prompt_parts.append(f"「地点」：{st.session_state.inputs[2]}")
            if st.session_state.inputs[3] and st.session_state.inputs[3] not in ["默认随机", "自定义"]:
                prompt_parts.append(f"「情人身份」：{st.session_state.inputs[3]}")
            if st.session_state.inputs[4]:
                prompt_parts.append(f"「情人名字」：{st.session_state.inputs[4]}")
            if st.session_state.inputs[5] and st.session_state.inputs[5] not in ["默认随机", "自定义"]:
                prompt_parts.append(f"「情人血统」：{st.session_state.inputs[5]}")
            if st.session_state.inputs[6] and st.session_state.inputs[6] not in ["默认随机", "自定义"]:
                prompt_parts.append(f"「情人性格」：{st.session_state.inputs[6]}")
            if st.session_state.inputs[7] and st.session_state.inputs[7] not in ["默认随机", "自定义"]:
                prompt_parts.append(f"「我的身份」：{st.session_state.inputs[7]}")
            if st.session_state.inputs[8]:
                prompt_parts.append(f"「我的名字」：{st.session_state.inputs[8]}")
            prompt_parts.append(f"「铺垫剧情占比」：{st.session_state.inputs[9]}")
            
            st.session_state.generated_prompt = "{{角色和任务设定}}：你是一个中文黄色故事生成器，你具备丰富的想象力、生动的描述能力、对女性性欲和性爱的了解，以及设计出引人入胜的情节的能力，注重浪漫情节和细腻感情描写，从而创造出能够让女性看到高潮的淫荡故事。在色情情节部分，充斥着色欲饱满、粗俗、下流淫荡的性行为动作细节，对于性器官的描写要直白和具体，充满亲吻、抚摸、插入、抽插的动作与角色的感受。{{任务要求}}现在请写一个至少1500字以上的「题材」的黄色故事，关于男主角（具体信息参见后面的「情人身份」「情人名字」「情人血统」）和女主角（具体信息参见后面的「我的身份」「我的名字」）发生在「地点」的，必须包含「情色类型」的情节。以女性为第一人称讲述这个故事。整个故事中，开头故事情节描写占总体故事的比重为「铺垫剧情占比」，剩余为色情情节部分。{{其他任务要求}}请在一开始给故事一个独特新颖、引人遐思的标题，整篇文字以女主角的第一人称视觉来讲述故事。下面是用户对本次生成中有关参数和选项的具体要求，记住不要在生成内容的开头部分重复这些要求："+ "； ".join(prompt_parts) + "。"

            st.session_state.story_generated = True
            alert1.empty()  

            temp_alert = st.empty()
            temp_alert.warning("故事生成大概需要1-2分钟的时间；为保护您的隐私，我们不会保留您的故事和语音，请及时保存或下载到本地，如果忘记保存，我们将无法帮您找回。")

            generated_text_placeholder_1 = st.empty()
            audio_placeholder = st.empty()
            link_placeholder = st.empty()
            generated_text_placeholder_2 = st.empty()

            llm_response = get_llm_response(st.session_state.generated_prompt, api_key)
            st.session_state.generated_text = llm_response.strip()
            temp_alert.empty()
            generated_text_placeholder_1.write(st.session_state.generated_text)

            # success = store_generated_story(username, auth_token, st.session_state.generated_text, prompt_parts)

            download_button = get_text_downloader_html(st.session_state.generated_text, 'Generated_Story.txt')
            link_placeholder.markdown(download_button, unsafe_allow_html=True)

            try:
                access_token = get_access_token(subscription_key, token_endpoint)
                text_part1, text_part2 = split_text(st.session_state.generated_text, inputs[9])
                
                audio_content1 = BytesIO(text_to_speech(text_part1, access_token, tts_endpoint))
                audio_content2 = BytesIO(text_to_speech(text_part2, access_token, tts_endpoint))
                
                audio1_b64 = base64.b64encode(audio_content1.getvalue()).decode()
                audio2_b64 = base64.b64encode(audio_content2.getvalue()).decode()
                
                with open(os.path.join(current_dir, 'static', 'audio', '3.mp3'), 'rb') as f:
                    audio3_bytes = f.read()
                audio3_b64 = base64.b64encode(audio3_bytes).decode()
                
                logger.info(f"Audio 1 length: {len(audio1_b64)}")
                logger.info(f"Audio 2 length: {len(audio2_b64)}")
                logger.info(f"Audio 3 length: {len(audio3_b64)}")
                
                with open(os.path.join(current_dir, 'static', 'js', 'audio_processing.js'), 'r') as file:
                    js_code = file.read()
                
                html_code = f"""
                <div id="audio-data" style="display:none;"
                    data-audio1="{audio1_b64}"
                    data-audio2="{audio2_b64}"
                    data-audio3="{audio3_b64}">
                </div>
                <button id="process-audio-btn">处理音频</button>
                <div id="audio-player" style="display: none;">
                    <audio id="audio-element" controls>
                        Your browser does not support the audio element.
                    </audio>
                    <input type="range" id="progress-bar" min="0" max="100" value="0" step="0.1" style="width: 100%;">
                    <span id="current-time">0:00</span> / <span id="duration">0:00</span>
                </div>
                <script>{js_code}</script>
                """
                
                html(html_code, height=200)
                
                logger.info("Audio processing and UI elements added successfully")

            except Exception as audio_error:
                st.warning("音频生成过程中出现问题，但您的故事已成功生成。您可以阅读文本版本。")
                logger.error(f"Audio processing error: {str(audio_error)}")
        except Exception as e:
            if "LLM" in str(e):
                handle_llm_error(e)
            elif "Text-to-Speech" in str(e):
                handle_tts_error(e)
            else:
                handle_audio_processing_error(e)

    if generate_story_button and not st.session_state.story_generated:
        generate_story()
        # if deduct_credit():
        #     generate_story()
    
    if st.session_state.story_generated:
        if st.button("返回首页"):
            for key in list(st.session_state.keys()):
                if key not in ['logged_in', 'auth_token', 'username', 'user_id', 'credits']:
                    del st.session_state[key]
            st.rerun() 

    return inputs, generate_story_button


if __name__ == "__main__":
    logged_in = True
    username = "sample_user"
    api_key = "sample_api_key"

    run_app(logged_in, username,api_key)
