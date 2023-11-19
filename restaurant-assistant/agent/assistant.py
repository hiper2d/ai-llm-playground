import time
from typing import List, Optional

from dotenv import load_dotenv, find_dotenv
from openai import OpenAI

from agent.tools.image_generator import ImageGenerator
from agent.tools.mongo_searcher import MongoSearcher

ASSISTANT_PROMPT = """You are a restaurant advisor, your goal is to find the best restaurant and dishes for the user. \
As a restaurant advisor, you know the user's location. Don't format the answer. Don't use lists. \
You only allowed to use new lines."""

VECTOR_SEARCH_PROMPT = """Search for restaurant and restaurant menu information by restaurant or dish description. \
Respond using a JSON with restaurant_description and restaurant_id fields."""

VECTOR_SEARCH_PARAM_PROMPT = "The query to search for restaurants by restaurant or dish description."

IMAGE_GENERATOR_PROMPT = """Generate an image of a dish by description. \
Useful when a user wants to see the dish before ordering it.\
Use this tool only if a user asks for an image of a dish."""

IMAGE_GENERATOR_PARAM_PROMPT = "The detailed description of the dish."


class AssistantResponse:
    def __init__(self, reply: str, restaurant_ids: List[str] = None, image_url: str = None):
        self.reply = reply
        self.restaurant_ids = restaurant_ids
        self.image_url = image_url


class Assistant:
    def __init__(self):
        self.client = OpenAI()
        # print(self.client.models.list())
        self.mongo_search_tool = MongoSearcher()
        self.image_generator = ImageGenerator()

        self.assistant = self.client.beta.assistants.create(
            name="Restaurant Advisor",
            instructions=ASSISTANT_PROMPT,
            tools=[{
                "type": "function",
                "function": {
                    "name": "searchForRestaurants",
                    "description": VECTOR_SEARCH_PROMPT,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": VECTOR_SEARCH_PARAM_PROMPT},
                        },
                        "required": ["query"]
                    }
                }
            },
                {
                    "type": "function",
                    "function": {
                        "name": "generateImage",
                        "description": IMAGE_GENERATOR_PROMPT,
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string", "description": IMAGE_GENERATOR_PARAM_PROMPT},
                            },
                            "required": ["description"]
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
        print(f"Running assistant with prompt {ASSISTANT_PROMPT}")
        # print(run.model_dump_json(indent=4))

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
                # Loop through messages and print content based on role
                msg = messages.data[0]
                role = msg.role
                content = msg.content[0].text.value
                print(f"{role.capitalize()}: {content}")
                return AssistantResponse(content, restaurant_ids)
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
                        output += "Don't format the answer. Don't use lists. You only allowed to use new lines."
                        tool_outputs.append({
                            "tool_call_id": action['id'],
                            "output": output
                        })
                    elif func_name == "generateImage":
                        generated_image_url = self.image_generator.generate_image(description=arguments['description'])
                        print(f"Generated image url: {generated_image_url} by description: {arguments['description']}")
                        output = f"Here is the image of the dish: {generated_image_url}. \
                        Include it into your reply as a simple URL without any formatting. \
                        Add a description so the user can understand what is on the image."
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