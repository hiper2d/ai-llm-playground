import time
from typing import List, Optional

from dotenv import load_dotenv, find_dotenv
from openai import OpenAI

from agent.tools import MongoDbSearchTool

ASSISTANT_PROMPT = """You are a restaurant advisor, your goal is to find the best restaurant and dishes for the user.
As a restaurant advisor, you know the user's location. Restaurant advisor must never ask for a user address or location."""


class AssistantResponse:
    def __init__(self, reply: str, restaurant_ids: List[str] = None):
        self.reply = reply
        self.restaurant_ids = restaurant_ids


class Assistant:
    def __init__(self):
        self.client = OpenAI()
        # print(self.client.models.list())
        self.mongo_search_tool = MongoDbSearchTool()

        self.assistant = self.client.beta.assistants.create(
            name="Restaurant Advisor",
            instructions=ASSISTANT_PROMPT,
            tools=[{
                "type": "function",
                "function": {
                    "name": "searchForRestaurants",
                    "description": "Search for restaurant and restaurant menu information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The query to search for restaurants"},
                        },
                        "required": ["query"]
                    }
                }
            }],
            model="gpt-4-1106-preview"
        )
        self.thread = self.client.beta.threads.create()

    def run(self, user_message) -> Optional[AssistantResponse]:
        # Add a message to the thread
        self.client.beta.threads.messages.create(
            role="user",
            thread_id=self.thread.id,
            content=user_message
        )
        # Run assistant
        run = self.client.beta.threads.runs.create(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id
        )
        print("Running assistant...")
        print(run.model_dump_json(indent=4))

        restaurant_ids = []
        while True:
            # Wait for 1 second
            time.sleep(1)

            # Retrieve the run status
            run_status = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread.id,
                run_id=run.id
            )
            print(f"Running status: {run_status.status}")

            if run_status.status == 'completed':
                messages = self.client.beta.threads.messages.list(
                    thread_id=self.thread.id
                )
                print(f"There are {len(messages.data)} messaged in the thread")
                # Loop through messages and print content based on role
                msg = messages.data[0]
                role = msg.role
                content = msg.content[0].text.value
                print(f"{role.capitalize()}: {content}")
                return AssistantResponse(content, restaurant_ids)
                break
            elif run_status.status == 'requires_action':
                print("Function Calling")
                required_actions = run_status.required_action.submit_tool_outputs.model_dump()
                print(required_actions)
                tool_outputs = []
                import json
                for action in required_actions["tool_calls"]:
                    func_name = action['function']['name']
                    arguments = json.loads(action['function']['arguments'])

                    if func_name == "searchForRestaurants":
                        search_result = self.mongo_search_tool.search(query=arguments['query'])
                        output = "There few restaurants that match your query:\n"
                        counter = 1
                        for result in search_result:
                            output += f"Option {counter}. {result['description']}\n"
                            restaurant_ids.append(result['restaurant_id'])
                            counter += 1
                        tool_outputs.append({
                            "tool_call_id": action['id'],
                            "output": output
                        })
                    else:
                        raise ValueError(f"Unknown function: {func_name}")

                print("Submitting outputs back to the Assistant...")
                self.client.beta.threads.runs.submit_tool_outputs(
                    thread_id=self.thread.id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )
            else:
                print("Waiting for the Assistant to process...")
                time.sleep(1)
        return None


if __name__ == "__main__":
    load_dotenv(find_dotenv())
    assistant = Assistant()
    assistant.run("I want to eat sushi")