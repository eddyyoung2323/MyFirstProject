import streamlit as st
import json
from config_manage import get_user_configurations, save_configuration, delete_configuration, validate_config_name, update_default_configuration

def hide_and_clear_sidebar():
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"][aria-expanded="true"] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.empty()

def generate_sidebar_inputs(defaults=None, username=None, auth_token=None):
    if 'inputs' not in st.session_state or not isinstance(st.session_state['inputs'], list):
        st.session_state['inputs'] = defaults if defaults else ["默认随机", [], "默认随机",  "默认随机", "", "默认随机",  "默认随机",  "默认随机", "", "45%"]

    while len(st.session_state['inputs']) < 10:
        st.session_state['inputs'].append("")

    try:
        default_value = int(st.session_state['inputs'][9].rstrip('%'))
    except (IndexError, ValueError, AttributeError):
        default_value = 45

    # user_configurations = get_user_configurations(username, auth_token)
    user_configurations = []
    # Sidebar Inputs
    options1 = ["默认随机", "自定义", "校园情色", "都市言情", "奇幻玄幻", "家庭乱伦", "仙侠武侠"]
    options2 = ["默认随机", "纯爱", "帅哥", "痴女", "出轨", "乱伦", "舒服的性爱", "3P/多P", "偷情"]
    options3 = ["默认随机", "自定义", "家", "办公室", "车内", "豪华酒店", "公园", "宿舍", "野外", "电影院", "会议室"]
    options4 = ["默认随机", "自定义", "老师", "学生", "大夫", "老板", "下属", "患者", "邻居", "水电工"]
    options5 = ["默认随机", "自定义", "中国人","日本人", "韩国人", "白种人", "黑人", "拉丁裔", "中东人"]
    options6 = ["默认随机", "自定义", "安静沉稳", "热情奔放", "幽默可爱", "诚实可靠", "成熟体贴", "斯文温和", "才华横溢", "专注认真"]
    

    selected_genre = st.sidebar.selectbox(
        "题材", 
        options1,
        index=options1.index(st.session_state['inputs'][0]) if st.session_state['inputs'][0] in options1 else 0,
        key='text_input_1_select'
    )

    if selected_genre == "自定义":
        custom_genre = st.sidebar.text_input(
            "请输入自定义题材 (最多4个字符)",
            value=st.session_state['inputs'][0] if st.session_state['inputs'][0] not in options1 else "",
            max_chars=32,
            key='text_input_1_custom'
        )
        st.session_state['inputs'][0] = custom_genre
    else:
        st.session_state['inputs'][0] = selected_genre
   
    st.session_state['inputs'][1] = st.sidebar.multiselect(
        "情色类型",
        options2[1:],
        default=st.session_state['inputs'][1],
        key='text_input_2'
    )

    selected_location = st.sidebar.selectbox(
        "地点", 
        options3,
        index=options3.index(st.session_state['inputs'][2]) if st.session_state['inputs'][2] in options3 else 0,
        key='text_input_3_select'
    )

    if selected_location == "自定义":
        custom_location = st.sidebar.text_input(
            "请输入自定义地点 (最多4个字符)",
            value=st.session_state['inputs'][2] if st.session_state['inputs'][2] not in options3 else "",
            max_chars=32,
            key='text_input_3_custom'
        )
        st.session_state['inputs'][2] = custom_location
    else:
        st.session_state['inputs'][2] = selected_location


    selected_profile_m = st.sidebar.selectbox(
        "情人身份", 
        options4,
        index=options4.index(st.session_state['inputs'][3]) if st.session_state['inputs'][3] in options4 else 0,
        key='text_input_4_select'
    )

    if selected_profile_m == "自定义":
        custom_profile_m = st.sidebar.text_input(
            "请输入自定义情人身份 (最多4个字符)",
            value=st.session_state['inputs'][3] if st.session_state['inputs'][3] not in options4 else "",
            max_chars=32,
            key='text_input_4_custom'
        )
        st.session_state['inputs'][3] = custom_profile_m
    else:
        st.session_state['inputs'][3] = selected_profile_m
  
    st.session_state['inputs'][4] = st.sidebar.text_input(
        "情人名字",
        st.session_state['inputs'][4],
        key='text_input_name1'
    )
 
    selected_ethnicity = st.sidebar.selectbox(
        "情人血统", 
        options5,
        index=options5.index(st.session_state['inputs'][5]) if st.session_state['inputs'][5] in options5 else 0,
        key='text_input_5_select'
    )

    if selected_ethnicity == "自定义":
        custom_ethnicity = st.sidebar.text_input(
            "请输入自定义情人血统 (最多4个字符)",
            value=st.session_state['inputs'][5] if st.session_state['inputs'][5] not in options5 else "",
            max_chars=32,
            key='text_input_5_custom'
        )
        st.session_state['inputs'][5] = custom_ethnicity
    else:
        st.session_state['inputs'][5] = selected_ethnicity

    selected_personality = st.sidebar.selectbox(
        "情人性格", 
        options6,
        index=options6.index(st.session_state['inputs'][6]) if st.session_state['inputs'][6] in options6 else 0,
        key='text_input_6_select'
    )

    if selected_personality == "自定义":
        custom_personality = st.sidebar.text_input(
            "请输入自定义情人性格 (最多4个字符)",
            value=st.session_state['inputs'][6] if st.session_state['inputs'][6] not in options6 else "",
            max_chars=32,
            key='text_input_6_custom'
        )
        st.session_state['inputs'][6] = custom_personality
    else:
        st.session_state['inputs'][6] = selected_personality 

    selected_profile_f = st.sidebar.selectbox(
        "我的身份", 
        options4,
        index=options4.index(st.session_state['inputs'][7]) if st.session_state['inputs'][7] in options4 else 0,
        key='text_input_7_select'
    )

    if selected_profile_f == "自定义":
        custom_profile_f = st.sidebar.text_input(
            "请输入自定义我的身份 (最多4个字符)",
            value=st.session_state['inputs'][7] if st.session_state['inputs'][7] not in options4 else "",
            max_chars=32,
            key='text_input_7_custom'
        )
        st.session_state['inputs'][7] = custom_profile_f
    else:
        st.session_state['inputs'][7] = selected_profile_f
 
    st.session_state['inputs'][8] = st.sidebar.text_input(
        "我的名字",
        st.session_state['inputs'][8],
        key='text_input_name2'
    )
    st.session_state['inputs'][9] = f"{st.sidebar.slider('铺垫剧情占比', min_value=0, max_value=100, value=default_value, step=5, format='%d%%', key='text_input_8')}%"

    show_save_config = st.sidebar.checkbox("💾  保存此配置", key='show_save_config')
    if show_save_config:
        config_name = st.sidebar.text_input("输入配置名称 (最多10个字符)", key="config_name", max_chars=10)
        save_config_button = st.sidebar.button("💻  点击保存故事配置")

        if save_config_button:
            if config_name:
                existing_names = [config['name'] for config in user_configurations]
                is_valid, error_message = validate_config_name(config_name, existing_names)
                
                if is_valid:
                    active_configurations = [config for config in user_configurations if config.get('on', True)]
                    if len(active_configurations) >= 10:
                        st.sidebar.error("您已达到最大配置数量（10个）。请停用一个现有配置后再保存新的配置。")
                    else:
                        config = list(st.session_state['inputs'])  # Convert tuple to list
                        config[1] = list(config[1])  # Ensure multiselect values are lists
                        if save_configuration(config_name, username, config, auth_token):
                            user_configurations = get_user_configurations(username, auth_token)
                            configuration_names = [config['name'] for config in user_configurations]
                            st.rerun()
                else:
                    st.sidebar.error(error_message)
            else:
                st.sidebar.error("请填写一个故事配置名称。")

    return st.session_state['inputs']
    
def display_sidebar(username):
    if 'redirect' not in st.session_state:
        st.session_state['redirect'] = False
    
    # if st.session_state['hide_sidebar']:
    #     hide_and_clear_sidebar()
    #     return None, None
    
    # user_configurations = get_user_configurations(username, '')
    user_configurations = []

    configuration_names = [config['name'] for config in user_configurations]

    if st.session_state.get('reset_config', False):
        st.session_state['selected_config'] = ""
        st.session_state['reset_config'] = False

    selected_config = st.sidebar.selectbox(
        "👜   我的预存配置", 
        [""] + configuration_names,
        key='selected_config',
        format_func=lambda x: "选择配置" if x == "" else x
    )

    if selected_config:
        selected_config_data = next((config for config in user_configurations if config['name'] == selected_config), None)
        if selected_config_data:
            try:
                loaded_config = json.loads(selected_config_data['json'])
                config_dict = {}
                for item in loaded_config:
                    key, value = next(iter(item.items()))
                    config_dict[key] = value

                st.session_state['inputs'] = [
                    config_dict.get('「题材」', '默认随机'),
                    config_dict.get('「情色类型」', '').split('、') if config_dict.get('「情色类型」') else [],
                    config_dict.get('「地点」', '默认随机'),
                    config_dict.get('「情人身份」', '默认随机'),
                    config_dict.get('「情人名字」', ''),
                    config_dict.get('「情人血统」', '默认随机'),
                    config_dict.get('「情人性格」', '默认随机'),
                    config_dict.get('「我的身份」', '默认随机'),
                    config_dict.get('「我的名字」', ''),
                    config_dict.get('「铺垫剧情占比」', '45%')
                ]
                st.sidebar.success(f"配置已加载: {selected_config}")
            except json.JSONDecodeError as e:
                st.sidebar.error(f"JSON 解析错误: {e}")
                st.sidebar.error(f"原始 JSON 数据: {selected_config_data['json']}")
        else:
            st.sidebar.error("无法加载所选配置")

        delete_config_button = st.sidebar.button("🗑  删除配置")

        if delete_config_button and selected_config:
            selected_config_data = next((config for config in user_configurations if config['name'] == selected_config), None)
            if selected_config_data:
                if delete_configuration(selected_config_data['id'], ''):
                    st.session_state['reset_config'] = True
                    st.rerun()
                else:
                    st.sidebar.error("删除配置失败")
            else:
                st.sidebar.error("无法删除所选配置")
    
    inputs = generate_sidebar_inputs(st.session_state.get('inputs', []), username, '')
    st.session_state['inputs'] = inputs

    st.experimental_set_query_params(redirect=True)
    
    redirect_url = "http://139.9.45.75"
    generate_story_button = st.sidebar.button(f"🚀 确认定制", key="redirect_button")

    if generate_story_button:
        st.session_state['redirect'] = True
        st.rerun()

    if st.session_state.get('redirect'):
        st.session_state['redirect'] = False
        st.markdown(f'<meta http-equiv="refresh" content="0;url={redirect_url}">', unsafe_allow_html=True)
        
       
      
    return inputs, generate_story_button
