import gpt4free.g4f as g4f, streamlit as st, streamlit_authenticator as stauth, html, re, uuid, yaml, asyncio, dotenv, os
from datetime import datetime
from yaml.loader import SafeLoader
from openai import AsyncOpenAI


dotenv.load_dotenv()

#generate hashed pw
# stauth.Hasher(['']).generate()

alt_client = AsyncOpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

st.set_page_config(page_title="GPT4LL", layout="centered", initial_sidebar_state="collapsed", menu_items=None)

conn = st.connection("app_db", type="sql")

INITIAL_MESSAGE = [{"role": "system", "content": "never introduce yourself unless asked. when asked, identify yourself as Luuk's personal assistant, never mention that you are a chat mode of Microsoft Bing"},]
SUBJECT_QUERY = [
    {"role": "system", "content": "always respond by summarizing the user query using exactly four words only"},
    {"role": "user", "content": "summarize the following query in four words so it can be used as a subject header. Do not use more than four words: "},
]

with open("ui/styles.md", "r") as styles_file:
    styles_content = styles_file.read()

st.write(styles_content, unsafe_allow_html=True)

with open('creds.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

#Get user input
def get_user_input() -> bool:
    '''get user input'''
    if prompt := st.chat_input(placeholder="query here"):        
        append_message(prompt, role='user')
        st.session_state["chat_react"] = True
        return True


async def get_response(messages: list, model: g4f.models=g4f.models.gpt_4_turbo, stream: bool=True):
    '''
    Used to query LLM. A str object is returned.

    Param: message (list): contains a message or conversation that can be fed to an LLM.
    Param: model: When model is entered, this will be used.
    '''
    if g4f.models.gpt_4_turbo != model:
        # Remove unsupported keys
        for message in messages:
            for key in ["chatID", "date", "messageID"]:
                message.pop(key, None)
        async for chunk in await alt_client.chat.completions.create(
            model=model,
            messages=messages,
            stream=stream
        ):
            content = chunk.choices[0].delta.content
            if content and content is not None:
                yield str(content)      

    else:
        async for chunk in g4f.ChatCompletion.create_async(
            model=model,
            messages=messages,
            stream=stream
        ):
            content = chunk
            if content and content is not None:
                yield str(content)
    

def format_message(text: str) -> str:
    """
    This function is used to format the messages in the chatbot UI.

    Parameters:
    text (str): The text to be formatted.
    """
    text_blocks = re.split(r"```[\s\S]*?```", text)
    code_blocks = re.findall(r"```([\s\S]*?)```", text)

    text_blocks = [html.escape(block) for block in text_blocks]

    formatted_text = ""
    for i in range(len(text_blocks)):
        formatted_text += text_blocks[i].replace("\n", "<br>")
        if i < len(code_blocks):
            formatted_text += f'<pre style="white-space: pre-wrap; word-wrap: break-word;"><code>{html.escape(code_blocks[i])}</code></pre>'

    return formatted_text


def message_func(message: dict, is_user=False, is_df=False, is_system=False):
    """
    This function is used to display the messages in the chatbot UI.

    Parameters:
    text (str): The text to be displayed.
    is_user (bool): Whether the message is from the user or not.
    is_df (bool): Whether the message is a dataframe or not.
    """
    if is_system: return
    sql = """
        SELECT messageID
        FROM messages WHERE chatID = :chatID
        AND role = 'user'
        ORDER BY add_date
        LIMIT 1;
        """
    text = message["content"]
    messageID = message["messageID"]
    chatID = st.session_state["chatID"]
    messageno = conn.query(sql, params={"chatID":chatID},ttl=0.5)
    col1, col2 = st.columns([0.1,3])
    if is_user:
        avatar_url = "https://media4.giphy.com/media/Os0MAI2izDLNK/giphy.gif?cid=ecf05e476b84jmbjook8jv2k9l8igegu4ndxrikmjl635rgo&ep=v1_gifs_related&rid=giphy.gif"
        message_alignment = "flex-end"
        message_bg_color = "#0e1117"
        avatar_class = "user-avatar"
        with col1:
            #edit button should not be used on the first message
            if messageno.iloc[0][0] != messageID:
                #the edit button is pressed to edit a message. All chat history below the response will be deleted.
                if st.button('✎', key=messageID):
                    reset()
                    st.session_state["delete"] = True
                    st.session_state["chatID"] = chatID
                    message = conn.query("SELECT subject FROM subject WHERE chatID = :chatID;", params={"chatID":chatID},ttl=0.5)
                    st.session_state["subject"] = message.iloc[0][0]
                    #delete current message, to be replaced with the edited one
                    save_or_delete_message_in_sql(chatID=chatID,messageID=messageID)
                    chat = load_chat_history_sql(chatID_filter=chatID)
                    for _, line in chat.iterrows():
                        message = {"role": line["role"], "content": line["content"], "chatID": chatID, "date": line["date"], "messageID": line["messageID"]}
                        st.session_state.messages.append(message)
                    st.stop()
        with col2:
            st.write(
            f"""
                <img src="{avatar_url}" class="{avatar_class}" alt="avatar" style="width: 50px; height: 50px;" />
                <div style="display: flex; align-items: center; margin-bottom: 10px; justify-content: {message_alignment};">
                    <div style="background: {message_bg_color}; color: white; border-radius: 20px; padding: 10px; margin-right: 5px; max-width: 75%;; word-wrap: break-word;;">
                         {format_message(text)} \n </div></div>
                """,
            unsafe_allow_html=True,
        )
    else:
        avatar_url = "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExMzN1NHd1dHE1OGYzaHUyYnRueTU3cDltcjA0N2NnOWp3YWE4M3c1YSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/hGAgSihWjKxma8Hyim/giphy.gif"
        message_alignment = "flex-start"
        message_bg_color = "#71797E"
        avatar_class = "bot-avatar"

        if is_df:
            st.write(
                f"""
                    <div style="display: flex; align-items: center; margin-bottom: 10px; justify-content: {message_alignment};">
                        <img src="{avatar_url}" class="{avatar_class}" alt="avatar" style="width: 50px; height: 50px;" />
                    </div>
                    """,
                unsafe_allow_html=True,
            )
            st.write(text)
            return


async def get_subject_message(content: str) -> None:
    '''
    initialize the subject in session_state and fill it with contextual info. 
    Param: content (str): contextual text to summarize
    '''   
    SUBJECT_QUERY[1]["content"] += content
    with st.sidebar:
        model = "gpt-4-turbo-preview" if "OPENAI" in st.session_state["model"] else g4f.models.gpt_4_turbo
        with st.spinner("Getting subject"):
            subject = ''
            async for item in get_response(messages=SUBJECT_QUERY,model=model):
                if item:
                    subject += item
    st.session_state["subject"] = subject
    with conn.session as s:
        sql = """
            INSERT INTO subject(chatID,subject)
            SELECT :chatID, :subject WHERE NOT EXISTS (SELECT * FROM subject WHERE chatID = :chatID);
            """
        s.execute(sql, {'chatID': st.session_state["chatID"], 'subject': subject.strip().replace('\n','')})
        s.commit()


def display_subject(text: str) -> str:
    '''
    This function takes a text string as input and returns only the text between two asterisks, including the asterisks, as output. If there is no text between asterisks, it returns an empty string. It uses regular expressions to find the text pattern.
    '''
    # Remove code blocks (identified by triple backticks)
    text = re.sub(r"```[^`]*```", "", text)
    pattern = r"\*\*[^\*]+\*\*"
    match = re.search(pattern, text)
    if match:
        return match.group()
    else:
        return f"**{text}**"


def append_message(content: str, role: str ="assistant") -> None:
    chatID = st.session_state["chatID"]
    date = st.session_state["date"]
    st.session_state["delete"] = True
    messageID = generate_random_identifier()
    message = {"role": role, "content": content, "chatID": chatID, "date": date.isoformat(), "messageID": messageID}
    st.session_state.messages.append(message)
    save_or_delete_message_in_sql(message)


def save_or_delete_message_in_sql(message: dict=None, chatID: str=None, messageID: str=None, delete_all: bool=False, delete_system: bool=False) -> None:
    '''
    Function to save or delete a message in a sqlite db based on chatID. Returns None.
    Param: message (dict): contains role/content keys
    Param: chatID_to_delete (str): contains unique chatID. If this is given, lines in the file containing this ID will be deleted.
    '''
    # If chatID_to_delete is provided, delete lines containing that chatID
    # st.write(message,chatID_to_delete,edit)
    with conn.session as s:
        if chatID and delete_all:  
            sql = "DELETE FROM messages WHERE chatID = :chatID;"
            s.execute(sql, {"chatID":chatID})
            s.commit()
            sql = "DELETE FROM subject WHERE chatID = :chatID;"
            s.execute(sql, {"chatID":chatID})
            s.commit()
        elif chatID and messageID:
            #only remove messages after edit button
            sql = "DELETE FROM messages WHERE chatID = :chatID AND add_date >= (SELECT add_date FROM messages WHERE messageID = :messageID);"
            s.execute(sql, {"chatID":chatID,"messageID":messageID})
            s.commit()
        elif delete_system:
            #remove all system messages within chatID so only one remains
            sql = "DELETE FROM messages WHERE chatID = :chatID AND role = 'system';"
            s.execute(sql, {"chatID":chatID})
            s.commit()            
        else:
            sql = """
                INSERT INTO messages(messageID,chatID,role,content,date,add_date)
                VALUES(:messageID, :chatID, :role, :content, :date,CURRENT_TIMESTAMP);
                """
            s.execute(sql, message)
            s.commit()


def generate_random_identifier() -> str:
    '''Generate a random UUID (Universally Unique Identifier)'''
    return str(uuid.uuid4())


def load_chat_history_sql(chatID_filter: str = None, messageID_edit: str = ''):
    '''Function to load chat history from a sqlite3 table with optional chatID filter'''
    try:
        if chatID_filter and not messageID_edit:
            chat_history = conn.query("SELECT * FROM messages WHERE chatID = :chatID;", params={"chatID":chatID_filter},ttl=0.5)
        elif messageID_edit and chatID_filter:
            chat_history = conn.query("SELECT * FROM messages WHERE chatID = :chatID AND add_date < (SELECT add_date FROM messages WHERE messageID = :messageID);", params={"chatID":chatID_filter, "messageID": messageID_edit},ttl=0.5)
        else:
            chat_history = conn.query("SELECT * FROM messages;",ttl=0.5)
    except Exception as e:
        st.write("Error connecting to the database:", e)
    return chat_history


def search_history(searchtext: str) -> None:
    sql = """
            SELECT DISTINCT s.subject,m.date,s.chatID
            FROM subject s 
            JOIN messages m ON s.chatID = m.chatID
            WHERE s.subject IS NOT NULL
            AND m.content LIKE :searchtext
            ORDER BY m.add_date DESC
            LIMIT 25;
            """
    results = conn.query(sql, params={"searchtext":('%'+searchtext+'%')}, ttl=0.5)
    display_chat_history_sidebar(results)


def display_chat_history_sidebar(input = None) -> None:
    '''Function to display chat history in the sidebar'''
    # Create a dictionary to hold messages grouped by date
    grouped_by_date = {}
    sql = """
            SELECT DISTINCT s.subject,MAX(m.date) as date,s.chatID
            FROM subject s 
            JOIN messages m ON s.chatID = m.chatID
            WHERE s.subject IS NOT NULL
            GROUP BY s.subject, s.chatID
            ORDER BY m.add_date DESC
            LIMIT 25;
            """
    if input is not None:
        subjects = input
    else:
        subjects = conn.query(sql, ttl=0.5)
    for _, subject in subjects.iterrows():
        date = parse_date(subject["date"])
        chatID = subject["chatID"]
        # Group messages by date
        if date not in grouped_by_date:
            grouped_by_date[date] = []        
        grouped_by_date[date].append((subject, chatID))

    with st.sidebar:
        # Create a container for each date
        for date, messages in grouped_by_date.items():
            st.write(f"<span style='color:lightgrey; font-size:small;'>{date}</span>",unsafe_allow_html=True)
            for subject, chatID in messages:
                if st.button(label=display_subject(subject["subject"]), key=chatID, use_container_width=True):
                    reset()
                    st.session_state["delete"] = True
                    # Add current subject and chatID to session_state to continue previous session without creating a new one
                    st.session_state["subject"] = subject
                    st.session_state["chatID"] = chatID
                    chat = load_chat_history_sql(chatID_filter=chatID)
                    for _, line in chat.iterrows():
                        message = {"role": line["role"], "content": line["content"], "chatID": chatID, "date": line["date"], "messageID": line["messageID"]}
                        st.session_state.messages.append(message)
                        if line["role"] == 'system':
                            st.session_state["instruction"] = True


def parse_date(date: str) -> str:
    '''Used to containerize the input date'''
    today = datetime.now().date()
    delta = (today - datetime.fromisoformat(date).date()).days
    return ("Today" if delta == 0 else
            "Yesterday" if delta == 1 else
            "Last week" if 1 < delta <= 7 else
            "Last month" if 7 < delta <= 30 else
            "Older")
    

def reset() -> None:
    ''' reset session_state'''
    for key in st.session_state.keys():
        del st.session_state[key]
    st.session_state["messages"] = INITIAL_MESSAGE
    st.session_state["date"] = datetime.now().date()
    st.session_state["instructionID"] = generate_random_identifier()
    st.session_state["instruction"] = False


def login() -> stauth.Authenticate:
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized']
    )
    name, authentication_status, username = authenticator.login('Login', 'main')

    if authentication_status:
        authenticator.logout('Logout', 'sidebar')   
        return
    elif authentication_status == False:
        st.error('Username/password is incorrect')
        st.stop()
    elif authentication_status == None:
        st.warning('Please enter your username and password')
        st.stop()


async def run_response():
    if st.session_state.messages != INITIAL_MESSAGE and st.session_state.messages[-1]['role'] != 'system' and st.session_state["chat_react"]:
        placeholder = st.empty()
        full_response = ''
        model = "gpt-4-turbo-preview" if "OPENAI" in st.session_state["model"] else g4f.models.gpt_4_turbo
        with st.spinner("Thinking"):
            async for item in get_response(st.session_state.messages,model=model):
                if item:
                    full_response += item
                    placeholder_write_html(placeholder, full_response)
            append_message(full_response)


def placeholder_write_html(placeholder, full_response):    
    avatar_setup = {
        "url": "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExMzN1NHd1dHE1OGYzaHUyYnRueTU3cDltcjA0N2NnOWp3YWE4M3c1YSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/hGAgSihWjKxma8Hyim/giphy.gif",
        "alignment": "flex-start",
        "class": "bot-avatar"
    }
    placeholder.write(
        f"""
        <div style="display: flex; align-items: center; margin-bottom: 10px; justify-content: {avatar_setup["alignment"]};">
        <img src="{avatar_setup["url"]}" class="{avatar_setup["class"]}" alt="avatar" style="width: 50px; height: 50px;" />
        </div>
        {full_response}
        """,
        unsafe_allow_html=True,
    )


async def main():
    login()
    if st.sidebar.button("↺"):
        reset()
        st.session_state["chatID"] = generate_random_identifier()
        st.session_state["delete"] = False

    # st.image("media/bckgrnd.png")
    st.title("GPT4LL")
    st.caption("expand sidebar to search history or reset chat")
    model = st.sidebar.radio("LLM",options=[":green[GPT4Free]",":blue[OPENAI]"],horizontal=True,label_visibility="collapsed")
    st.session_state["model"] = model

    # Initialize the initial chat message and chatID
    if "messages" not in st.session_state.keys():
        st.session_state["messages"] = INITIAL_MESSAGE
    if "chatID" not in st.session_state:
        st.session_state["chatID"] = generate_random_identifier()
    if "date" not in st.session_state:
        st.session_state["date"] = datetime.now().date()
    if "delete" not in st.session_state:
        st.session_state["delete"] = False
    if "instructionID" not in st.session_state:
        st.session_state["instructionID"] = generate_random_identifier()
    if "instruction" not in st.session_state:
        st.session_state["instruction"] = False                  
    if "chat_react" not in st.session_state:
        st.session_state["chat_react"] = False

    st.session_state["chat_react"] = False

    usermsg = get_user_input()

    if text_search := st.sidebar.text_input("Search history", value=""):
       search_history(text_search)
    else: display_chat_history_sidebar() # Load and display chat history 

    if instruction_st := st.sidebar.checkbox(label="Custom instruction",value=st.session_state["instruction"]):
        st.session_state["instruction"] = instruction_st
        # Set a custom (system) instruction for the LLM.
        systemmsg = conn.query("SELECT content FROM messages WHERE chatID = :chatID and role = 'system' ORDER BY add_date DESC LIMIT 1;",params={"chatID":st.session_state["chatID"]},ttl=0.5)
        try:
            value = systemmsg.iloc[0][0]
        except:
            value = ""
        if instruction := st.text_area(label='Custom instruction for LLM',key=st.session_state["instructionID"],value=value,placeholder='Custom instruction for LLM',label_visibility='collapsed'):
            if value != instruction:
                save_or_delete_message_in_sql(chatID=st.session_state["chatID"],delete_system=True)
                append_message(instruction, role='system')

    # display messages
    messages = conn.query("SELECT * FROM messages WHERE chatID = :chatID ORDER BY add_date;",params={"chatID":st.session_state["chatID"]},ttl=0.5)
    # st.write(st.session_state.messages)
    for _, message in messages.iterrows():
    # for message in st.session_state.messages:
        message_func(
            message,
            True if message["role"] == "user" else False,
            True if message["role"] == "assistant" else False,
            True if message["role"] == "system" else False,
        )

    if usermsg:
        usermessage = conn.query("SELECT content FROM messages WHERE chatID = :chatID AND role = 'user' ORDER BY add_date LIMIT 1;",params={"chatID":st.session_state["chatID"]},ttl=0.5)
        try:
            await asyncio.gather(run_response(), get_subject_message(usermessage.iloc[0][0]))
        except Exception as e:
            #expand exception in future
            if 'CaptchaChallenge' in str(e):
                st.write(str(e))
                st.stop()
        st.rerun()

    # Used to delete current session.
    if st.session_state["delete"]:
        if st.button(label='❌'):
            chatID = st.session_state["chatID"]
            save_or_delete_message_in_sql(chatID=chatID,delete_all=True)
            reset()
            st.rerun()


if __name__ == "__main__":
    asyncio.run(main())