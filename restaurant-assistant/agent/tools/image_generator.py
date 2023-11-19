from openai import OpenAI


class ImageGenerator:
    def __init__(self):
        self.client = OpenAI()

    def generate_image(self, description):
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
    print(drawer.generate_image("A drawing of a cat. It has black and white short fur, and eyes of different color: green and blue"))