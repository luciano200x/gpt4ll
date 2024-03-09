import pandas as pd
from vanna.base import VannaBase
from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
import gpt4free.g4f as g4f

class MyGPT4(VannaBase):
    def __init__(self, client=None, config=None):
        VannaBase.__init__(self, config=config)

        if client is not None:
            self.client = client
            return

    def system_message(self, message: str) -> any:
        return {"role": "system", "content": message}

    def user_message(self, message: str) -> any:
        return {"role": "user", "content": message}

    def assistant_message(self, message: str) -> any:
        return {"role": "assistant", "content": message}

    def submit_prompt(self, prompt, **kwargs):
        if prompt is None:
            raise Exception("Prompt is None")

        if len(prompt) == 0:
            raise Exception("Prompt is empty")

        model = g4f.models.gpt_4_turbo

        try:
            content = g4f.ChatCompletion.create(
                model=model,
                messages=prompt
            )
            if content and content is not None:
                return str(content)
        except Exception as e:
            print(e)

class MyVanna(ChromaDB_VectorStore, MyGPT4):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        MyGPT4.__init__(self, g4f, config=config)

vn = MyVanna()

# TRAINING schema information, only once is needed
# df_information_schema = vn.run_sql("SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME IN ('Artikelstam','debiteurenstam','Gebruikers','Klachten','Medewerkers','relaties','uren','werken','Registraties','Registratieregels')")
# This will break up the information schema into bite-sized chunks that can be referenced by the LLM
# plan = vn.get_training_plan_generic(df_information_schema)
# st.write(plan)
# vn.train(plan=plan)

# REMOVE TRAINING DATA
# vn.remove_training_data(id='29a7acc9-25e0-46ba-9003-979605f60cb8-doc')
# vn.remove_collection("sql")

# ADD TRAINING DATA TABLE SCHEMAS DDL
ddl = """"""
# vn.train(ddl=ddl)

# ADD DOCUMENTATION
documentation = """
"""
# vn.train(documentation=documentation)

# CHECK CURRENT TRAINING DATA
# training_data = vn.get_training_data()
# st.write(training_data)

# Replace YOUR_EXCEL_FILE_PATH with the path to your Excel file
excel_file_path = ''

# Using pandas to read the specified range within 'Blad1' sheet
try:
    # Specifying the sheet name and range of cells to read
    df = pd.read_excel(excel_file_path, sheet_name='Blad1', skiprows=1, nrows=51)
except Exception as e:
    print(f"Failed to read Excel file: {e}")
    exit()

# Assuming vn is an instance of your training model object
# Make sure to instantiate or import your training model accordingly

# Loop through each row in the dataframe
for _, row in df.iterrows():
    # Extract question
    question = row.iloc[1]
    # Extracting the T-SQL query from cell
    query = row.iloc[2]

    # Ensuring that the query is a string and not NaN or None
    if pd.notnull(query):
        sql = query
        try:
            # Add your function or method to execute the SQL command here, e.g.,
            print(question,sql)
            # vn.train(question=question,sql=sql)
            print(f"Training with query: {sql}")
        except Exception as e:
            print(f"Failed to train with query {sql}: {e}")