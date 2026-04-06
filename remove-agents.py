#to list agents in current foundry
import os
from dotenv import load_dotenv 
import json

load_dotenv(override=True)
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
client = AIProjectClient(
    endpoint=os.getenv("PROJECT_ENDPOINT"),
    credential=DefaultAzureCredential(),
)
agents = list(client.agents.list())
for agent in agents:
    #delete the agent
    print(f"Deleting agent: {agent.name}")
    client.agents.list_versions(agent.name)  
    client.agents.delete(agent.name) 
     