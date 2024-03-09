# step 1
to use this project first install all requirements in a virtual environment using anaconda and pip.
the file to use is pip_requirements.txt
# step 2
update the file /.streamlit/secrets.toml to contain a reference to the ODBC DSN. in this example the DSN is named SQLConnect.
[connections.app_db_mssql]
url = "mssql+pyodbc://username:password@SQLConnect"
# step 3
to be able to query the database, a vector database is needed. in this case a local Chromadb vectorstore is used. this is the special sauce for this project. 
if you want to use your own vector store, you can use the train function to set it up. you can run parts of the code that are commented out since these are a onetime action. make sure to first execute the get_training_plan_generic function. after this add ddl, documentation and most importantly sql/question. in case of the train_function an excel file is used to collect the sql/question entries.
first 
# step 3
use streamlit to start the project launching it in headless mode on port 8888 using this command (remove the --server.port parameter to use the default port of 8501):
**nohup streamlit run your_app.py --server.port 8888 &**
# step 4
use askdb: followed by the question you want to ask the db to see if the project works. gpt_3.5_long is the model used, but might be outdated by the time you use this project.