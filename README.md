# GPT4LL
#### Video demo: https://youtu.be/JZoX-K1C7mo
#### Description: 

  * Personal chatbot: The main function of the project
  * Chat storage: I store all the chats in a database. You can access them anytime by extending the menu. Each chat has a summarize subject title that gives you a brief overview of what was talked about.
  * Chat editing: You can edit any chat that you had by clicking on the Edit button. You can change the content of the chat. You can also add or delete messages from the chat.
  * Chat deletion: You can delete any chat that you had with me by clicking on the Delete button. This will permanently remove the chat from the database and free up some space.
  * Model selection: You can choose different LLM models. One is free to use, the other costs money to use but will not be used for commercial purposes.
  * Login page: A login page is used to prevent unauthorized access to the chats. You need to enter your username and password to access the chat interface. You can logout from the chat interface.
  * Summarized subject: The subject had to be summarized to fit into the side bar. I had to write some code to summarize it and to make sure it worked in all cases. The summarizing is done using a parallel call to an LLM using it's own system message.
  * Subject grouping: The subjects are stored in a sqlite database (as is the chat history). To show them grouped in the sidebar I had to write a function that parsed the date of the chat and put it into one of four categories: today, yesterday, last week and older.    Obviously the ordering of the subjects had to be done right.
  * Chat search: Chat history can be searched, effectively querying the underlying messages in the database and returning only the corresponding subject headers, which makes it very efficient.
  * Parallel processing: To support this, I had to implement asynchronous processing, meaning you can run several processes at once. This saves times, since I can have the LLM finish a reaction and generate a subject at the same time.
  * Streaming text: The models that support this had streaming text enabled. This in combination with parallel processing was difficult to get to work properly.
  * Features I turned off because I didn't use them (I put code for this in another branch of this project, check it out):
   - I also added the possibility to upload images. To do this I had to implement a new route in the processing to the LLM's.
   - Web search. It was possible to query a web search using the Bing connector.
   - Summarize text. Possible to summarize the text that was entered in the chat.
