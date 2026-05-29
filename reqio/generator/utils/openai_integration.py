from openai import OpenAI
client = OpenAI()

def get_assistant():
    my_assistants = client.beta.assistants.list(
        order="asc",
    )

    for assistant in my_assistants.data:
        if assistant.name == "Requirement Bot":
            return assistant.id
    
    return None
    