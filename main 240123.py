import gpt4free.g4f as g4f, streamlit as st, streamlit_authenticator as stauth, html, re, json, uuid, yaml, asyncio 
from datetime import datetime
from yaml.loader import SafeLoader

#generate hashed pw
# stauth.Hasher(['']).generate()

st.set_page_config(page_title="GPT4LL", page_icon="️‍‍☠️", layout="centered", initial_sidebar_state="collapsed", menu_items=None)

conn = st.connection("app_db", type="sql")

INITIAL_MESSAGE = [{"role": "system", "content": "never introduce yourself unless asked. when asked, identify yourself as Luuk's personal assistant, never mention that you are a chat mode of Microsoft Bing"},]
SUBJECT_QUERY = [
    {"role": "system", "content": "always respond by summarizing the user query using exactly four words only"},
    {"role": "user", "content": "summarize the following query in four words so it can be used as a subject header: "},
]

# '''TODO: 
# * streaming text --> DONE!
# * fix probleem met reload --> DONE
# * edit knop toevoegen --> DONE
# * custom instruction ook opslaan in chat history
# * clear chat history knop toevoegen
# * inlog pagina toevoegen --> DONE
# * user specific chat history 
# * doorzoeken chat history toevoegen
# * parralize llm tbv onderwerp -> DONE
# * fouten afvangen -> DONE
# * unit tests schrijven
# * streamlit user interface toevoegen --> DONE
# * chathistorie toevoegen (opslaan als JSONL?) --> DONE
# * toevoegen custom system prompt --> DONE
# * toevoegen openAI API als fallback
# * db gebruiken voor history ipv jsonl --> IN PROGRESS
# * abo chatgpt opzeggen :)
# '''

with open("ui/styles.md", "r") as styles_file:
    styles_content = styles_file.read()

st.write(styles_content, unsafe_allow_html=True)

with open('creds.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

#Get user input
def get_user_input() -> None:
    '''get user input'''
    if prompt := st.chat_input(placeholder="query here"):
        subject = get_subject_message(prompt)
        append_message(prompt, subject ,role='user')
        st.session_state["chat_react"] = True


def get_streaming_response(messages: list, model: g4f.models=g4f.models.gpt_4_turbo, stream: bool=False) -> list:
    '''
    Used to query LLM. A list object is returned.

    Param: message (list): contains a message or conversation that can be fed to an LLM.
    Param: model (g4f.models): When model is entered, this will be used.
    '''
    try:
        response = g4f.ChatCompletion.create(
            model=model,
            messages=messages,
            stream=stream
        )
    except Exception as e:
        #fallback on different model in case of exception
        if 'CaptchaChallenge' in str(e) and model != g4f.models.gpt_4_0613:
            st.write('Using different model')
            response = get_streaming_response(messages=messages,model=g4f.models.gpt_4_0613)
    if response:
        return response


# def get_OPENAI


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
    text = message["content"]
    messageID = message["messageID"]
    chatID = st.session_state["chatID"]
    col1, col2 = st.columns([1,8])
    if is_user:
        avatar_url = "https://avataaars.io/?accessoriesType=Round&avatarStyle=Transparent&clotheColor=PastelYellow&clotheType=Hoodie&eyeType=Hearts&eyebrowType=SadConcernedNatural&facialHairColor=Black&facialHairType=Blank&graphicType=SkullOutline&hairColor=BrownDark&hatColor=PastelOrange&mouthType=Grimace&skinColor=Pale&topType=WinterHat4"
        message_alignment = "flex-end"
        message_bg_color = "#0a0a0a"
        avatar_class = "user-avatar"
        with col1:
            #the edit button is pressed to edit a message. All chat history below the response will be deleted.
            if message["counter"] > 1:
                if st.button('edit', key=messageID):
                    reset()
                    st.session_state["delete"] = True
                    st.session_state["subject"] = message["subject"]
                    st.session_state["chatID"] = chatID
                    chatsql = load_chat_history_sql(chatID_filter=chatID, messageID_edit=messageID)
                    chat = load_chat_history(chatID_filter=chatID, messageID_edit=messageID)
                    #delete current message, to be replaced with the edited one
                    save_or_delete_message_in_jsonl(None,chatID)
                    save_or_delete_message_in_sql(None,chatID)
                    hstr = chat[chatID]
                    #rebuild the new chat history
                    for line in hstr:
                        append_message(content=line["content"], role=line["role"])
                    st.stop()
        with col2:
            st.write(
            f"""
                <img src="{avatar_url}" class="{avatar_class}" alt="avatar" style="width: 50px; height: 50px;" />
                <div style="display: flex; align-items: center; margin-bottom: 10px; justify-content: {message_alignment};">
                    <div style="background: {message_bg_color}; color: white; border-radius: 20px; padding: 10px; margin-right: 5px; max-width: 75%;;">
                        {format_message(text)} \n </div></div>
                """,
            unsafe_allow_html=True,
        )
    else:
        avatar_url = "https://avataaars.io/?accessoriesType=Blank&avatarStyle=Transparent&clotheColor=Blue02&clotheType=ShirtScoopNeck&eyeType=Close&eyebrowType=Angry&facialHairColor=Auburn&facialHairType=BeardLight&graphicType=Hola&hairColor=PastelPink&hatColor=White&mouthType=ScreamOpen&skinColor=Pale&topType=LongHairDreads"
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


def get_subject_message(content: str) -> str:
    '''
    initialize the subject in session_state and fill it with contextual info. 
    Param: content (str): contextual text to summarize
    '''
    global conn
    if "subject" not in st.session_state:
        SUBJECT_QUERY[1]["content"] += content
        with st.sidebar:
            with st.spinner("Getting subject"):
                subject = str(get_streaming_response(messages=SUBJECT_QUERY,model=g4f.models.gpt_35_turbo))
        st.session_state["subject"] = subject
        with conn.session as s:
            sql = """
                INSERT INTO subject(chatID,subject)
                VALUES(:chatID, :subject);
                """
            s.execute(sql, {'chatID': st.session_state["chatID"], 'subject': subject})
            s.commit()
    else:
        subject = st.session_state["subject"]
    return subject


def append_message(content: str, subject: str = "", role: str ="assistant") -> None:
    chatID = st.session_state["chatID"]
    date = st.session_state["date"]
    st.session_state["delete"] = True
    messageID = generate_random_identifier()
    #count messages per subject, excluding the system messages
    filtered_messages = [message for message in st.session_state.messages if "system" not in message["role"]]
    message_count = len(filtered_messages)
    message = {"role": role, "content": content, "chatID": chatID, "subject": subject, "date": date.isoformat(), "messageID": messageID, "counter": message_count}
    st.session_state.messages.append(message)
    # Save the message to a JSONL file
    save_or_delete_message_in_jsonl(message)
    save_or_delete_message_in_sql(message)


def save_or_delete_message_in_jsonl(message: dict, chatID_to_delete: str=None, filename: str="chat_history.jsonl") -> None:
    '''
    Function to save or delete a message in a JSONL file based on chatID. Returns None.
    Param: message (dict): contains role/content keys
    Param: chatID_to_delete (str): contains unique chatID. If this is given, lines in the file containing this ID will be deleted.
    '''
    # If chatID_to_delete is provided, delete lines containing that chatID
    if chatID_to_delete:
        with open(filename, "r") as file:
            lines = file.readlines()
        with open(filename, "w") as file:
            for line in lines:
                if chatID_to_delete not in json.loads(line).get("chatID", ""):
                    file.write(line)
    else:
        # Save the message to the file
        with open(filename, "a") as file:
            json_record = json.dumps(message)
            file.write(json_record + "\n")


def save_or_delete_message_in_sql(message: dict, chatID_to_delete: str=None) -> None:
    '''
    Function to save or delete a message in a sqlite db based on chatID. Returns None.
    Param: message (dict): contains role/content keys
    Param: chatID_to_delete (str): contains unique chatID. If this is given, lines in the file containing this ID will be deleted.
    '''
    # If chatID_to_delete is provided, delete lines containing that chatID
    global conn
    with conn.session as s:
        if chatID_to_delete:  
            sql = "DELETE FROM messages WHERE chatID = :chatID;"
            s.execute(sql, {"chatID":chatID_to_delete})
            sql = "DELETE FROM subject WHERE chatID = :chatID;"
            s.execute(sql, {"chatID":chatID_to_delete})
            s.commit()

        else:
            sql = """
                INSERT INTO messages(messageID,chatID,role,content,date,add_date)
                VALUES(:messageID, :chatID, :role, :content, :date,CURRENT_TIMESTAMP);
                """
            values = message 
            s.execute(sql, values)
            s.commit()


def generate_random_identifier() -> str:
    '''Generate a random UUID (Universally Unique Identifier)'''
    return str(uuid.uuid4())


def load_chat_history(filename: str = "chat_history.jsonl", chatID_filter: str = None, messageID_edit: str = '') -> dict:
    '''Function to load chat history from a JSONL file with optional chatID filter'''
    chat_history = {}
    edit_message_reached = False  # Flag to indicate if the message to be edited has been reached
    try:
        with open(filename, "r") as file:
            for line in file:
                if edit_message_reached:
                    break  # Stop processing further lines once the message to be edited is reached

                record = json.loads(line)
                chatID = record["chatID"]
                subject = record.get("subject")
                date = record.get("date")
                messageID = record.get("messageID")
                counter = record.get("counter")

                # Check if we are filtering by chatID
                if chatID_filter is not None and chatID != chatID_filter: continue

                # Set the flag if the message to be edited is reached
                if messageID_edit is not None and messageID == messageID_edit:
                    edit_message_reached = True
                    continue  # Skip the current message and stop appending further messages            

                if chatID not in chat_history:
                    chat_history[chatID] = []
                chat_history[chatID].append({
                    "role": record["role"],
                    "content": record["content"],
                    "subject": subject,
                    "date": date,
                    "messageID": messageID,
                    "counter": counter,
                },)
    except FileNotFoundError:
        print("No chat history found.")
    return chat_history


def load_chat_history_sql(chatID_filter: str = None, messageID_edit: str = '') -> dict:
    '''Function to load chat history from a sqlite3 table with optional chatID filter'''
    global conn
    chat_history = {}
    st.write(chatID_filter, messageID_edit)
    try:
        if chatID_filter and not messageID_edit:
            records = conn.query("SELECT * FROM messages WHERE chatID = :chatID;", params={"chatID":chatID_filter})
        elif messageID_edit and chatID_filter:
            records = conn.query("SELECT * FROM messages WHERE chatID = :chatID AND date_add < (SELECT date_add FROM messages WHERE messageID = :messageID);", params={"chatID":chatID_filter, "messageID": messageID_edit})
        else:
            records = conn.query("SELECT * FROM messages;")
        for record in records:
            st.write(f"record: {record}")
            messageID = record[0]
            chatID = record[1]
            role = record[2]
            content = record[3]
            date = record[4]

            if chatID not in chat_history:
                chat_history[chatID] = []
            chat_history[chatID].append({
                "role": role,
                "content": content,
                "date": date,
                "messageID": messageID,
            },)
    except Exception as e:
        print("Error connecting to the database:", e)
    return chat_history


def display_chat_history_sidebar(chat_history: dict) -> None:
    '''Function to display chat history in the sidebar'''
    # Create a dictionary to hold messages grouped by date
    grouped_by_date = {}
    for item in reversed(list(chat_history.items())):
        msg = item[1]
        chatID = item[0]
        if msg[0]["role"] == "system" and len(msg) == 1:
            continue
        elif msg[0]["role"] == "system" and len(msg) != 1:
            subject = msg[1]['subject']
        else:
            subject = msg[0]['subject']
        date = parse_date(msg[0]['date'])
        # Group messages by date
        if date not in grouped_by_date:
            grouped_by_date[date] = []
        grouped_by_date[date].append((subject, chatID))

    with st.sidebar:
        # Create a container for each date
        for date, messages in grouped_by_date.items():
            st.write(f"<span style='color:lightgrey; font-size:small;'>{date}</span>",unsafe_allow_html=True)
            for subject, chatID in messages:
                if st.button(label=subject, key=chatID, use_container_width=True):
                    reset()
                    st.session_state["delete"] = True
                    # Add current subject and chatID to session_state to continue previous session without creating a new one
                    st.session_state["subject"] = subject
                    st.session_state["chatID"] = chatID
                    chat = load_chat_history(chatID_filter=chatID)
                    hstr = chat[chatID]
                    for line in hstr:
                        st.session_state.messages.append(line)


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
    st.session_state["instructionactive"] = False


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

login()

# st.image("media/bckgrnd.png")
st.title("GPT4LL")
st.caption("expand sidebar to load history, give custom instruction or reset chat")

# messages = []

if st.sidebar.button("Reset Chat"):
    reset()
    st.session_state["chatID"] = generate_random_identifier()
    st.session_state["delete"] = False

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
    st.session_state["instructionactive"] = False
if "chat_react" not in st.session_state:
    st.session_state["chat_react"] = False

st.session_state["chat_react"] = False

get_user_input()

# Set a custom (system) instruction for the LLM.
if instruction := st.sidebar.text_area(label='Custom instruction for LLM',key=st.session_state["instructionID"],placeholder='Custom instruction for LLM',label_visibility='collapsed'):
    st.caption('custom instruction active')
    if not st.session_state["instructionactive"]:
        append_message(instruction, role='system')
        st.session_state["instructionactive"] = True

# Load and display chat history
chat_history = load_chat_history()
display_chat_history_sidebar(chat_history)

# display messages
for message in st.session_state.messages:
    message_func(
        message,
        True if message["role"] == "user" else False,
        True if message["role"] == "assistant" else False,
        True if message["role"] == "system" else False,
    )

# Start responding after the initial message to decrease loading time. Also do not respond to system messages.
if st.session_state.messages != INITIAL_MESSAGE and st.session_state.messages[-1]['role'] != 'system' and st.session_state["chat_react"]:
    avatar_url = "https://avataaars.io/?accessoriesType=Blank&avatarStyle=Transparent&clotheColor=Blue02&clotheType=ShirtScoopNeck&eyeType=Close&eyebrowType=Angry&facialHairColor=Auburn&facialHairType=BeardLight&graphicType=Hola&hairColor=PastelPink&hatColor=White&mouthType=ScreamOpen&skinColor=Pale&topType=LongHairDreads"
    message_alignment = "flex-start"
    message_bg_color = "#71797E"
    avatar_class = "bot-avatar"
    with st.spinner("Thinking"):
        full_response = ''
        response = get_streaming_response(st.session_state.messages,stream=True)
        placeholder = st.empty()
        for item in response:
            full_response += item
            placeholder.write(
                f"""
                    <div style="display: flex; align-items: center; margin-bottom: 10px; justify-content: {message_alignment};">
                        <img src="{avatar_url}" class="{avatar_class}" alt="avatar" style="width: 50px; height: 50px;" />
                    </div>
                    {full_response}
                    """,
                unsafe_allow_html=True,
            )
    append_message(full_response, subject=st.session_state["subject"])
    # st.rerun()

# Used to delete current session.
if st.session_state["delete"]:
    if st.button(label='❌'):
        chatID = st.session_state["chatID"]
        save_or_delete_message_in_jsonl(None,chatID)
        save_or_delete_message_in_sql(None,chatID)
        reset()
        st.rerun()
