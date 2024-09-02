import requests
import random

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
            print(f"无法获取故事预览。状态码: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"获取故事预览时发生错误: {str(e)}")
        return []