import streamlit as st
import logging, os

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


def handle_llm_error(e):
    logger.error(f"LLM Error: {e}")
    st.error(f"LLM Error: {e}")

def handle_tts_error(e):
    logger.error(f"Text-to-Speech Error: {e}")
    st.error(f"Text-to-Speech Error: {e}")

def handle_audio_processing_error(e):
    logger.error(f"生成故事时发生错误: {str(e)}")
    st.error(f"生成故事时发生错误: {str(e)}")
    print(f"Error details: {e}") 

def handle_config_error(e):
    logger.error(f"Configuration Error: {e}")
    st.error(f"Configuration Error: {e}")

def handle_credit_error():
    logger.error("您的点数已经全部使用，请购买更多点数或者跟我们联系book@xuegre.com.")
    st.error("您的点数已经全部使用，请购买更多点数或者跟我们联系book@xuegre.com.")
