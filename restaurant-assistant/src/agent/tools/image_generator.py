from openai import OpenAI


class ImageGenerator:
    def __init__(self):
        self.client = OpenAI()

    def generate_image(self, description):
        # Sometimes this request fails with the following error:
        # openai.BadRequestError: Error code: 400 - {'error': {'code': 'content_policy_violation', 'message':
        # 'Your request was rejected as a result of our safety system. Image descriptions generated from your prompt
        # may contain text that is not allowed by our safety system. If you believe this was done in error,
        # your request may succeed if retried, or by adjusting your prompt.',
        # 'param': None, 'type': 'invalid_request_error'}}
        response = self.client.images.generate(
            model="dall-e-3",
            prompt=description,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        return response.data[0].url


if __name__ == "__main__":
    drawer = ImageGenerator()
    print(drawer.generate_image("A drawing of a cat."))