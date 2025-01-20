examples = [
    {
        "input": "List all active machines.",
        "query": "SELECT * FROM mtConnect WHERE State = 'ACTIVE';"
    },
    {
        "input": "Get the total number of parts produced by machine 73.",
        "query": "SELECT SUM(PartCount) FROM mtConnect WHERE machine = 73;"
    },
    {
        "input": "Find the time when machine 73 was interrupted.",
        "query": "SELECT originalTime FROM mtConnect WHERE machineId = 73 AND State = 'INTERRUPTED';"
    },
    {
        "input": "Retrieve all machine parts and thier operations.",
        "query": "SELECT partsName, partsOperation FROM machineParts;"
    },
    {
        "input": "Find all machines with deleted parts.",
        "query": "SELECT machineId FROM machineParts WHERE isDelete = '1';"
    },
    {
        "input": "Get the finish logs for machine 45",
        "query": "SELECT * FROM machinePartrsFinish WHERE machineId = 45;"
    },
    {
        "input": "Find the total scrap parts for all machines.",
        "query": "SELECT SUM(scrapParts) AS totalScrapParts FROM machinePartsFinish;"
    },
    {
        "input": "List all machines and their current order status.",
        "query": "SELECT machineId, currentOrderStatus FROM machineParts;"
    },
    {
        "input": "Get all machine parts logs after '2023-01-01'.",
        "query": "SELECT * FROM machinePartsLog WHERE insertTime > '2023-01-01';"
    },
    {
        "input": "Find machines with load greater than 50 on the X-axis",
        "query": "SELECT machineId, Xload FROM mtConnect WHERE Xload > 50;"
    },
    {
        "input": "List planned start and finish dates for all parts.",
        "query": "SELECT partsName, PlannedStartDate, PlannedFinishDate FROM machineParts"
    },
    {
        "input": "Get the rework and scrap parts count for machine 101.",
        "query": "SELECT reworkParts, scrapParts FROM machinePartsFinish WHERE machineId = 101;"
    },
    {
        "input": "Find all emergency stops recorded.",
        "query": "SELECT machineId, EmergencyStop, originalTime FROM mtConnect WHERE EmergencyStop IS NOT NULL;"
    },
    {
        "input": "Calculate the remaining estimated quantity for all parts.",
        "query": "SELECT SUM(remainingEstimatedQuantity) AS totalRemaining FROM machineParts;"
    },
    {
        "input": "Find tools used by machine 88.",
        "query": "SELECT toolid FROM mtConnect WHERE machineId = 88;"
    },
    {
        "input": "Retrieve all operations performed on parts with cycle time less than 10 minutes.",
        "query": "SLECT partsName, partsOperation FROM machineParts WHERE partsCycleTime < 10;"
    }
]


import streamlit as st
from operator import itemgetter
import chromadb
from langchain_groq import ChatGroq

from langchain.chains import create_sql_query_chain

from langchain_community.tools import QuerySQLDataBaseTool
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.embeddings import OllamaEmbeddings

from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, FewShotChatMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.example_selectors import SemanticSimilarityExampleSelector

from langchain_chroma import Chroma

chromadb.api.client.SharedSystemClient.clear_system_cache()


db_user="root"
db_password=""
db_host ="127.0.0.1"
db_name="precima"
db = SQLDatabase.from_uri(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}")

llm = ChatGroq(
    api_key="",
    model="llama3-70b-8192",
    temperature=0
)

# ollama embeddings
ollama_embeddings = OllamaEmbeddings(model="nomic-embed-text")

# few shot prompt setup
example_prompt = ChatPromptTemplate.from_messages(
    [("human", "{input}\nSQLQuery"), ("ai", "{query}")]
)

few_shot_prompt = FewShotChatMessagePromptTemplate(
    example_prompt=example_prompt,
    examples=examples,
    # input_variables=["input","top_k"],
    input_variables=["input"],
)

try:
    vectorstore = Chroma(persist_directory="./chroma_data")
except Exception as e:
    print(f"Error connecting Chroma: {e}")
# vectorstore.delete_collection()

example_selector = SemanticSimilarityExampleSelector.from_examples(
    examples,
    ollama_embeddings,
    vectorstore,
    k=2,
    input_keys=["input"]
)
few_shot_prompt = FewShotChatMessagePromptTemplate(
    example_prompt=example_prompt,
    example_selector=example_selector,
    input_variables=["input", "top_k"]
)

# Final Prompt
final_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a MySQL expert. Given an input question, create a syntactically correct MySQL query to run. Unless otherwise specificed.\n\nHere is the relevant table info: {table_info}\n\nBelow are a number of examples of questions and their corresponding SQL queries."),
        few_shot_prompt,
        ("human", "{input}"),
    ]
)

# create a query generation chain
generate_query = create_sql_query_chain(llm, db, final_prompt)

execute_query = QuerySQLDataBaseTool(db=db)

# Define prompt template
answer_prompt = PromptTemplate.from_template(
    """Given the following user question, corresponding SQL Query, and SQL result answer the question.
    Remove text like Here is the answer: Which can cause an error while executing SQL Query.

    Question: {question}
    Query: {query}
    SQL Result: {result}
    Answer: """
)

# Define the rephrase_answer chain
rephrase_answer = answer_prompt | llm | StrOutputParser()

# define chain
chain = (
    RunnablePassthrough.assign(query=generate_query).assign(
        result=itemgetter("query") | execute_query
    )
    | rephrase_answer
)

st.title("Precima Agent")
user_query = st.text_input("Enter your query")
execute_query = st.button("Execute")

if execute_query and user_query:
    with st.spinner("Processing your Query.."):
        try:
            # Generate SQL Query 
            warning = "Give only sql qury without any additional things like ticks or quotes. As I will just execute this query in my database directly."
            query_prompt = warning + user_query
            query = generate_query.invoke({"question": query_prompt})

            st.write(f"Generated SQL Query: {query}")

            # Executing SQL Query
            execute_query_tool = QuerySQLDataBaseTool(db=db)
            sql_result = execute_query_tool.invoke(query)

            # Format the SQL result
            if isinstance(sql_result, list):
                formatted_result = "\n".join([f"- {row[0]}" for row in sql_result])
            else:
                formatted_result = str(sql_result)

            response = chain.invoke({"question": user_query, "input": user_query, "top_k": 1, "table_info": "some table info"})

            st.subheader("Generated SQL Query")
            st.write(query)
            
            st.subheader("SQL Query Result")
            st.write(formatted_result)

            st.subheader("Rephrased Answer")
            st.write(response)

        except Exception as e:
            st.error(f"Error: {e}")

