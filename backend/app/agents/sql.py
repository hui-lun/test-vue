from app.config import llm
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain.agents.agent_types import AgentType
import os

DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
db = SQLDatabase.from_uri(DATABASE_URL)
toolkit = SQLDatabaseToolkit(llm=llm, db=db)


# Add table info and foreign key hints
table_info = db.get_table_info()
table_info += """
-- Foreign key relationships:
- systeminfo.id → server.system_id
- lan_system_map.lan → system_lan_info.lan_key
- lan_system_map.id → systeminfo.id
- mlan_system_map.mlan → system_mlan_info.mlan_key
- mlan_system_map.id → systeminfo.id
- psu_system_map.psu → system_psu_info.psu_key
- psu_system_map.id → systeminfo.id
- server_pcie_map.pcieinfo → pcie_info.pcie_key
- server_pcie_map.(projectmodel, gbtsn) ↔ server.(projectmodel, gbtsn)
- storage_connector_map.connector → connector_info.connector_key
- storage_connector_map.id → storageinfo.id
- server_storage_map.id → storageinfo.id
- server_storage_map.(projectmodel, gbtsn) ↔ server.(projectmodel, gbtsn)
"""


agent_sql = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
)