import json
import time
from typing import List, Optional

from dotenv import load_dotenv, find_dotenv
from openai import OpenAI

from api.prompts import ASSISTANT_PROMPT, TOOL_VECTOR_SEARCH_OUTPUT, TOOL_IMAGE_GENERATOR_OUTPUT
from api.tools.image_generator import ImageGenerator
from api.tools.mongo_searcher import MongoSearcher


class AssistantResponse:
    def __init__(self, reply: str, restaurant_ids: List[str] = None, image_url: str = None):
        self.reply = reply
        self.restaurant_ids = restaurant_ids
        self.image_url = image_url
        self.thread_id = None


class Assistant:
    def __init__(self, assistant_id: Optional[str] = None, thread_id: Optional[str] = None):
        self.client = OpenAI()

        self.mongo_search_tool = MongoSearcher()
        self.image_generator = ImageGenerator()

        if assistant_id:
            self.assistant = self.client.beta.assistants.retrieve(assistant_id)
        else:
            self.assistant = self.client.beta.assistants.create(
                name="Restaurant Advisor",
                instructions=ASSISTANT_PROMPT,
                tools=[
                    MongoSearcher.get_assistant_definition(), ImageGenerator.get_assistant_definition()
                ],
                model="gpt-4-1106-preview"
            )

        if thread_id:
            self.thread = self.client.beta.threads.retrieve(thread_id)
        else:
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
        print(f"Running assistant with the following prompt: {ASSISTANT_PROMPT}")
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
                msg = messages.data[0]
                role = msg.role
                content = msg.content[0].text.value
                print(f"{role.capitalize()}: {content}")
                try:
                    content_json = json.loads(content)
                    reply = content_json["reply"] if "reply" in content_json else content
                    restaurant_ids = content_json["restaurant_ids"] if "restaurant_ids" in content_json else []
                    image_url = content_json["image_url"] if "image_url" in content_json else None
                    return AssistantResponse(reply=reply, restaurant_ids=restaurant_ids, image_url=image_url)
                except:
                    return AssistantResponse(content, [], None)

            elif run_status.status == 'requires_action':
                print("Function Calling")
                required_actions = run_status.required_action.submit_tool_outputs.model_dump()
                print(required_actions)
                tool_outputs = []

                for action in required_actions["tool_calls"]:
                    func_name = action['function']['name']
                    arguments = json.loads(action['function']['arguments'])

                    if func_name == "searchForRestaurants":
                        search_result = self.mongo_search_tool.search(query=arguments['query'])
                        options = []
                        for i, result in enumerate(search_result):
                            options.append(f"Option {i}: {result['description']}.\nRestaurant Id: {result['restaurant_id']}")
                            restaurant_ids.append(result['restaurant_id'])
                        output = TOOL_VECTOR_SEARCH_OUTPUT.format(options='\n'.join(options))
                        print(f"MongoDB vector search result: {output}")
                        tool_outputs.append({
                            "tool_call_id": action['id'],
                            "output": output
                        })
                    elif func_name == "generateImage":
                        try:
                            generated_image_url = self.image_generator.generate_image(description=arguments['description'])
                            print(f"Generated image url: {generated_image_url} by description: {arguments['description']}")
                            output = TOOL_IMAGE_GENERATOR_OUTPUT.format(generated_image_url=generated_image_url)
                        except Exception as e:
                            print(e)
                            output = "Request has been rejected by the safety system. Please try again with a different query."
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


if __name__ == "__main__":
    load_dotenv(find_dotenv())
    assistant = Assistant()
    assistant.run("I want to eat sushi")