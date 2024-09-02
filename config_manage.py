import streamlit as st
import requests
import json

def get_user_configurations(username, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(f"http://127.0.0.1:8090/api/collections/configurations/records?filter=(user='{username}')", headers=headers)
    if response.status_code == 200:
        return response.json().get('items', [])
    else:
        st.error(f"无法获取用户配置. Status code: {response.status_code}, Response: {response.text}")
        return []

def update_default_configuration(username, auth_token, config_json):
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    response = requests.get(f"http://127.0.0.1:8090/api/collections/configurations/records?filter=(user='{username}')&filter=(name='default')", headers=headers)
    
    if response.status_code == 200:
        items = response.json().get('items', [])
        if items:
            default_config = items[0]
            config_id = default_config['id']
            
            data = {
                "json": json.dumps(config_json)
            }
            update_response = requests.patch(f"http://127.0.0.1:8090/api/collections/configurations/records/{config_id}", json=data, headers=headers)
            
            if update_response.status_code == 200:
                return True
            else:
                st.sidebar.error(f"更新默认配置失败: {update_response.text}")
                return False
        else:
            st.sidebar.error("未找到默认配置")
            return False
    else:
        st.sidebar.error(f"获取默认配置失败: {response.text}")
        return False
    
def save_configuration(name, username, config_json, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    new_config = []
    keys = ["「题材」", "「情色类型」", "「地点」", "「情人身份」", "「情人名字」", "「情人血统」", "「情人性格」", "「我的身份」", "「我的名字」", "「铺垫剧情占比」"]
    for key, value in zip(keys, config_json):
        if isinstance(value, list):
            value = "、".join(value)  
        new_config.append({key: value})
    data = {
        "name": name,
        "user": username,
        "type": "user",
        "json": json.dumps(new_config, ensure_ascii=False) 
    }
    response = requests.post("http://127.0.0.1:8090/api/collections/configurations/records", json=data, headers=headers)
    if response.status_code == 200:
        st.sidebar.success("配置已保存")
        return True
    else:
        st.sidebar.error(f"保存配置失败: {response.text}") 
        return False

def delete_configuration(config_id, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    data = {"user": "none"}
    response = requests.patch(f"http://127.0.0.1:8090/api/collections/configurations/records/{config_id}", json=data, headers=headers)
    if response.status_code == 200:
        st.sidebar.success("配置已删除")
        return True
    else:
        st.sidebar.error(f"删除配置失败: {response.text}")
        return False

def validate_config_name(name, existing_names):
    if name in existing_names:
        return False, "配置名称已存在，请使用不同的名称。"
    if len(name) > 10:
        return False, "配置名称不能超过10个字符。"
    return True, ""

def update_user_credits(user_id, new_credits, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.patch(f"http://127.0.0.1:8090/api/collections/users/records/{user_id}", json={"credits": new_credits}, headers=headers)
    if response.status_code == 200:
        return True
    else:
        st.error("无法更新用户点数")
        return False