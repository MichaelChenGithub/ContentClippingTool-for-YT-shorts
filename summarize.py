import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pymongo import MongoClient
import concurrent.futures
import srt
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGODB_URI = os.getenv("MONGODB_URI")
# init the MongoDB client
client = MongoClient(MONGODB_URI)

class Model:
    def __init__(self, system_prompt):
        """
        初始化 Model 類的實例。
        
        參數：
        - system_prompt (str): 系統提示，用於指導 AI 模型生成回應。
        """
        self.system = system_prompt
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system),
                MessagesPlaceholder("examples", optional=True),
                ("human", "follow the system prompt to deal with belowing content: {question}"),
            ]
        )
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.llm_chain = self.prompt | self.llm

    def ask_question(self, question):
        """
        向 AI 模型詢問問題並獲取回應。
        
        參數：
        - question (str): 人類輸入的問題。
        
        返回：
        - (str): AI 模型的回應內容。
        """
        ai_message = self.llm_chain.invoke(question)
        return ai_message.content

    # def parallel_questions(self, questions, max_workers=5):
    #     with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
    #         answers = list(executor.map(self.ask_question, questions))
    #     return answers

    def parallel_questions(self, questions, max_workers=5, sleep_time=15):
        """
        使用多線程並行處理多個問題。
        
        參數：
        - questions (list): 問題列表。
        - max_workers (int): 最大線程數。
        - sleep_time (int): 每次批量處理後的休眠時間（秒）。
        
        返回：
        - (list): 回應列表。
        """
        answers = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            for i in range(0, len(questions), max_workers):
                batch = questions[i:i+max_workers]
                answers.extend(executor.map(self.ask_question, batch))
                time.sleep(sleep_time)
        return answers

def get_subtitles(content):
    """
    處理並解析字幕內容。
    
    參數：
    - content (str): 原始字幕文本內容。
    
    返回：
    - (list): 解析後的字幕對象列表。
    """
    content = content.replace("，", " ") # goodder 的 srt 格式與常見格式不同，需要先處理
    subtitles = list(srt.parse(content))
    return subtitles

def split_for_yt_clipping(subtitles, max_length=2800, overlap=20):
    """
    將字幕切分為適合用來摘要 YouTube 短片的片段，並保留部分重疊。
    
    參數：
    - subtitles (list): 字幕對象列表。
    - max_length (int): 每個片段的最大長度。
    - overlap (int): 片段之間的重疊部分長度。
    
    返回：
    - (list): 切分後的字幕片段列表。
    """
    timestamp_content = []
    temp_subs = []
    transcript_slice = ""

    for subtitle in subtitles:
        temp_sub = f"{subtitle.index}\n{subtitle.start} --> {subtitle.end}\n{subtitle.content}\n\n"
        temp_subs.append(temp_sub)
        transcript_slice += temp_sub + " "
        
        if len(transcript_slice) > (max_length - 100): # Keep some buffer for the next slice
            timestamp_content.append(''.join(temp_subs))
            if overlap:
                transcript_slice = "".join(temp_subs[-overlap:])
                temp_subs = temp_subs[-overlap:]  # Keep the last 'overlap' subtitles for the next slice
            else:
                transcript_slice = ""
                temp_subs = []
    # Add the remaining subtitles if any
    if temp_subs:
        timestamp_content.append(''.join(temp_subs))

    return timestamp_content

def split_transcript(subtitles, max_length=2700):
    """
    將字幕文本按指定最大長度進行切分，用於製作逐字稿。
    
    參數：
    - subtitles (list): 字幕對象列表。
    - max_length (int): 每個文本片段的最大長度。
    
    返回：
    - (list): 切分後的文本片段列表。
    """
    transcript = []
    transcript_slice = ""

    for subtitle in subtitles:
        transcript_slice += subtitle.content + " "
        
        if len(transcript_slice) > max_length:
            transcript.append(transcript_slice)
            transcript_slice = ""

    if transcript_slice:
        transcript.append(transcript_slice)
    return transcript

if __name__ == "__main__":
    # Get the example document
    db = client["goodder_event"]
    collection = db["ai-att-table"]
    query = {"full_duration": {"$gt": 4000}}
    results = collection.find(query).limit(1)
    content = results[0]["transcript"]["text"]
    
    # Get the subtitles
    subtitles = get_subtitles(content)
    timestamp_content = split_for_yt_clipping(subtitles)
    transcript = split_transcript(subtitles)
    print("Data preparation completed.")
    
    # task 1: YT short clipping from timestamp_content
    print("YT short clipping task is running...")
    summarizing_system_prompt = """
    As a professional YouTube Shorts editor, select about one minute of continuous and narrative-rich content from a longer video, adhering to these requirements:

    Objective: Choose sentences that are temporally continuous and narrative-rich.
    Restrictions: Do not include any AI-generated text.
    Format: Report the exact locations of these sentences using timestamps (e.g., from 00:05:30 to 00:05:45).

    The response do not include any introductory or explanatory text.
    """
    summary_model = Model(summarizing_system_prompt)
    summary_list = summary_model.parallel_questions(timestamp_content)
    
    with open('demo_summary_output.txt', 'w') as f:
        for item in summary_list:
            f.write(f"---------\n{item}\n")
    
    # task 2: Add punctuation marks to transcript
    print("Add punctuation marks task is running...")
    punctuation_system_prompt = """
    Add punctuation marks to the following text. If a sentence is already punctuated, leave it as is.
    """
    punctuation_model = Model(punctuation_system_prompt)
    punctuated_list = punctuation_model.parallel_questions(transcript)
    punctuated_content = "".join(punctuated_list)
    
    with open('demo_punctuated_content_output.txt', 'w') as f:
        f.write(punctuated_content)