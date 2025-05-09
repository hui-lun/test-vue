import requests
from pymongo import MongoClient
from langchain_core.messages import HumanMessage
import re
import datetime
import time

PROXY_SERVER = "http://10.1.8.5:5000/favicon.ico"
MONGO_URI = "mongodb://admin:password@192.168.1.166:27017/admin"
DB_NAME = "bdm_chat"
BAREBONE_COLLECTION_NAME = "server_spec_barebone"
pattern = r'[A-Za-z0-9]+-[A-Za-z0-9]'

inference_server_url = "http://192.168.1.193:8090/v1"

collection_fields_cache = {}

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def fetch_qvl(model, sku, gbt_pn):
    try:
        response = requests.get(PROXY_SERVER, params={"Model": model, "SKU": sku, "gbt_pn": gbt_pn}, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data:
            print("one data沒資料2")
            return "no_one_data"
        return data
    except Exception as e:
        print("one data沒資料1")
        return "no_one_data"

def insert_qvl(data):
    collection = db[QVL_COLLECTION_NAME]
    collection.delete_many({})
    if isinstance(data, list):
        data['time'] = datetime.datetime.utcnow()
        collection.insert_many(data)
    else:
        data['time'] = datetime.datetime.utcnow()
        collection.insert_one(data)
    print("QVL data inserted into MongoDB successfully.")

def init_fields_cache(COLLECTION_NAME):
    col = db[COLLECTION_NAME]
    doc = col.find_one()
    fields = []
    if doc:
        def extract_fields(d, prefix=""):
            for k, v in d.items():
                if k == '_id':
                    continue
                full_key = f"{prefix}.{k}" if prefix else k
                fields.append(full_key)
                if isinstance(v, dict):
                    extract_fields(v, full_key)
        extract_fields(doc)
    collection_fields_cache[COLLECTION_NAME] = fields

def fields_cache(COLLECTION_NAME):
    col = db[COLLECTION_NAME]
    doc = col.find_one()
    fields = []
    if doc:
        for k in doc.keys():
            if k != '_id':
                fields.append(k)
    collection_fields_cache[COLLECTION_NAME] = fields

def get_qvl_data(projectmodel,barebone_gbtsn):
    global QVL_COLLECTION_NAME
    QVL_COLLECTION_NAME = f"qvl_collection_{projectmodel.replace('-', '_')}"  #replace - to _
    collections = db.list_collection_names()
    print(f"All collection name : {collections}")
    if f"qvl_collection_{projectmodel.replace('-', '_')}" not in collections:
        if re.match(pattern, projectmodel):
            modelname = projectmodel.split('-')
            model = f"{modelname[0]}-{modelname[1]}"
            sku = f"{modelname[2]}"
            gbt_pn = f"{barebone_gbtsn}"
            result = fetch_qvl(model, sku, gbt_pn)
            if result == "no_one_data":
                return "no_one_data"
            else:
                insert_qvl(result)
                return "one_data"
    else:
        print(f"{QVL_COLLECTION_NAME} is exist")
        return "one_data"

def query_database(query: str) -> str:
    """
    Generates and executes MongoDB queries based on user input.
    Attempts to extract project model and query related QVL data.
    """
    global response_time
    global search_time

    # Try to extract the project model pattern from user query
    match = re.search(pattern, query, re.IGNORECASE)
    print(f"match: {match}")

    if match:
        try:
            result = None
            max_retries = 5
            retry_count = 0

            # First: search for project model and barebone number from spec database
            print("----------------search spec database start-----------------")
            while not isinstance(result, dict) and retry_count < max_retries:
                llm_query_code = generate_code_from_llm(query, llm, "barebone")
                exec_globals = {"db": db, "server_spec_barebone": db[BAREBONE_COLLECTION_NAME]}
                exec(llm_query_code, exec_globals)
                result = exec_globals.get("result", "No result returned.")
                retry_count += 1
                print("Retrying: get project model and barebone number")

            if isinstance(result, dict):
                projectmodel = result.get('projectmodel')
                barebone_gbtsn = result.get('barebone_gbtsn')

                # Second: query QVL data using project model and barebone number
                start_time = time.time()
                qvl_return = get_qvl_data(projectmodel, barebone_gbtsn)
                end_time = time.time()
                search_time = end_time - start_time
                print("----------------search spec database finish-----------------")

                try:
                    print("----------------search QVL start-----------------")
                    qvl_result = "No result returned."
                    retry_count = 0
                    start_time = time.time()

                    while qvl_result == "No result returned." and retry_count < max_retries and qvl_return == 'one_data':
                        print(f"Attempt {retry_count + 1} of {max_retries}")
                        try:
                            llm_query_code = generate_code_from_llm(query, llm, "qvl")
                            exec_globals = {
                                "db": db,
                                QVL_COLLECTION_NAME: db[QVL_COLLECTION_NAME],
                                BAREBONE_COLLECTION_NAME: db[BAREBONE_COLLECTION_NAME]
                            }
                            exec(llm_query_code, exec_globals)
                            qvl_result = exec_globals.get("result", "No result returned.")

                            if qvl_result != "No result returned.":
                                print(f"Found result on attempt {retry_count + 1}: {qvl_result}")
                            else:
                                print("No result, retrying...")
                        except Exception as e:
                            print(f"Error on attempt {retry_count + 1}: {e}")

                        retry_count += 1

                    end_time = time.time()
                    response_time = end_time - start_time
                    print("----------------search QVL finish-----------------")

                    # If QVL cannot be queried, fallback to spec-based search
                    if qvl_return == "no_one_data":
                        print("Project model not found, fallback to spec search")
                        llm_query_code = generate_code_from_llm(query, llm, "spec")
                        exec_globals = {"db": db, "server_spec_barebone": db[BAREBONE_COLLECTION_NAME]}
                        exec(llm_query_code, exec_globals)
                        result = exec_globals.get("result", "No result returned.")
                        return str(result)
                    else:
                        return str(qvl_result)
                except Exception as e:
                    print(f"Error while searching QVL: {e}")
                    return "Error during QVL query."

        except Exception as e:
            return f"Error executing query: {str(e)}"

    else:
        # If project model is not found, fallback to spec-based search
        print("No project model found.")
        llm_query_code = generate_code_from_llm(query, llm, "spec")
        exec_globals = {"db": db, "server_spec_barebone": db[BAREBONE_COLLECTION_NAME]}
        exec(llm_query_code, exec_globals)
        result = exec_globals.get("result", "No result returned.")
        print(f"result: {result}")
        return str(result)

def generate_code_from_llm(query: str, llm,status) -> str:
    if status == "barebone":
        #use spec_barebone db to search projectmodel and gbtsn
        init_fields_cache(BAREBONE_COLLECTION_NAME)
        fields = collection_fields_cache.get(BAREBONE_COLLECTION_NAME, [])
        fields_str = ", ".join(fields)

        prompt = f"""
            You are a Python assistant generating code to query a MongoDB collection named {BAREBONE_COLLECTION_NAME}.
            The collection is already available as a variable named {BAREBONE_COLLECTION_NAME}.
            All field names are case-sensitive. The available fields in the collection are: {fields_str}. Use the exact field names as shown.

            Do not create MongoDB clients or import libraries.

            When asked for project model-related information, follow this rule:

            Step 1: Extract the full project model (e.g., "R283-Z90-AAD1-000") from the user input.
            Step 2: Query MongoDB like this:
                result = db.{BAREBONE_COLLECTION_NAME}.find_one({{"ProjectModel": "<project_model>"}}, {{"ProjectModel": 1, "barebone_gbtsn": 1}})
            Step 3: Assign both the barebone_gbtsn and projectmodel to a dictionary named `result`, like this:
            result = {{
                "barebone_gbtsn": doc.get("barebone_gbtsn"),
                "projectmodel": doc.get("ProjectModel")
            }} if doc else "barebone not found."

            JUST FIND "ProjectModel" and "barebone_gbtsn"!!!!!!!!!!!!!!
            Respond ONLY with executable Python code wrapped in triple backticks.

            User query: {query}
        """
    elif status == "qvl":
        #use qvl
        fields_cache(QVL_COLLECTION_NAME)
        fields_qvl = collection_fields_cache.get(BAREBONE_COLLECTION_NAME, [])
        fields_barebone = collection_fields_cache.get(QVL_COLLECTION_NAME, [])
        merged_fields = fields_qvl + fields_barebone   #merage spec and QVL database
        fields_str = ", ".join(merged_fields)

        prompt = f"""
            You are a Python assistant generating code to query two MongoDB collections.

            Collections:
            1. {QVL_COLLECTION_NAME} (e.g., qvl_collection_R283_Z90_AAD1_000)
            - This represents the QVL (qualified vendor list) for a specific server model (e.g., R283-Z90-AAD1-000).
            - Do NOT use or assume the existence of a field like "projectmodel" to identify the model; the collection itself is already model-specific.
            - Extract relevant component information based on the user query and available field names.

            2. {BAREBONE_COLLECTION_NAME} (variable: `server_spec_barebone`)
            - This contains metadata or reference information about the server model (e.g., CPU brand, socket type, etc).
            - You may refer to this collection if needed to clarify or filter based on technical criteria.

            Facts:
            - MongoDB connection string: {MONGO_URI}
            - Database name: {DB_NAME}
            - All field names are case-sensitive. The available fields in the collection are: {fields_str}. Use the exact field names as shown.

            Behavior:
            - For each matched QVL document, return a dictionary only containing the subset of those fields which actually exist in that document.
            - Example: if only "CPU_1" and "DDR_15" exist in a document, return {{ "CPU_1": value, "DDR_15": value }}.
            - If no documents contain any of the relevant fields, do not return anything for that collection.
            - Always assign the result to a variable named `result`.
            - For the BAREBONE collection, do the same for relevant fields in the collection, return the result as `result`.
            - Do not create MongoDB clients or import libraries.
            - Please explain step-by-step in the code using comments.

            Respond only with valid executable Python code wrapped in triple backticks.

            User query: {query}
            """
    else:
        #use spec, doesn't include projectmodel
        fields = collection_fields_cache.get(BAREBONE_COLLECTION_NAME, [])
        fields_str = ", ".join(fields)
        prompt = f"""
            You are an assistant generating **Python code** to query a MongoDB collection named `{BAREBONE_COLLECTION_NAME}`.
            The collection object `{BAREBONE_COLLECTION_NAME}` is already available as a variable in the environment.

            Do NOT create new MongoDB collection.
            Do NOT import any libraries.

            Collections:
            1. {BAREBONE_COLLECTION_NAME} (variable: `server_spec_barebone`)
            - This contains metadata or reference information about the server model (e.g., CPU brand, socket type, etc).
            - You may refer to this collection if needed to clarify or filter based on technical criteria.

            Facts:
            - MongoDB connection string: {MONGO_URI}
            - Database name: {DB_NAME}
            - All field names are case-sensitive. The available fields in the collection are: {fields_str}. Use the exact field names as shown.

            Behavior:
            - Note: The "server name" in the user question refers to the field `ProjectModel` in the collection.
            - Output only valid Python code wrapped in triple backticks, like this:
                ```python\n# your code here\n```\n"
            - The final result must be stored in a variable named `result`.
            - Please note that all values in the query are strings, not numbers. For example, a value like `GPUQty: '2'` should be treated as a string.
            - Please only respond with the `ProjectModel` field.
            - Use logical operators like `$or`, `$all`, `$regex`, or others as needed to match the query's intent.
            
            User question:\n{query}
            """

    response = llm.invoke([HumanMessage(content=prompt)])
    code = response.content.strip()

    if code.startswith("```python") and code.endswith("```"):
        code = code[len("```python"):-3].strip()
    elif code.startswith("```") and code.endswith("```"):
        code = code[3:-3].strip()

    print(code)
    return code

def search_database(query):
    result = query_database(query)
    summary_prompt = f"""You are given a user query and the system's response. \
Please list the all result in a concise and organized format.

User Query:
{query}

System Response:
{result}

Final Answer:
"""
    response = llm.invoke(summary_prompt)
    return response