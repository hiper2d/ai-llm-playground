import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from langchain.embeddings import OpenAIEmbeddings
from langchain.tools import Tool
from langchain.vectorstores import MongoDBAtlasVectorSearch
from pydantic.v1 import BaseModel
from pymongo import MongoClient
from pymongo.server_api import ServerApi


class SingleTextArg(BaseModel):
    question: str


class MongoDbSearchTool:
    def __init__(self):
        username = quote_plus(os.getenv("MONGO_GMATE_USERNAME"))
        password = quote_plus(os.getenv("MONGO_GMATE_PASSWORD"))
        cluster = os.getenv("MONGO_GMATE_CLUSTER")
        database_name = os.getenv("MONGO_GMATE_DATABASE")

        uri = f"mongodb+srv://{username}:{password}@{cluster}.q1ds6re.mongodb.net/?retryWrites=true&w=majority"
        client = MongoClient(uri, server_api=ServerApi('1'))
        print(client.admin.command('ping'))
        db = client[database_name]
        restaurants_collection = db["restaurants"]
        embeddings = OpenAIEmbeddings()

        self.vectorstore = MongoDBAtlasVectorSearch(restaurants_collection, embeddings, index_name="vector_geo_index")

    def search(self, query: str):
        search_result = self.vectorstore.similarity_search_with_score(
            query=query,
            k=2,
            pre_filter={
                "geoWithin": {
                    "circle": {
                        "center": {
                            "type": "Point",
                            "coordinates": [-82.3355502759486, 28.17619853788267]
                        },
                        "radius": 10000
                    },
                    "path": "location"
                }
            },
            post_filter_pipeline=[{
                "$project": {
                    "embedding": 0,
                    "location": 0
                }
            }]
        )
        # print(list(map(lambda x: search_result[0].metadata['_id'], search_result)))
        ans = []
        for res in search_result:
            doc, score = res
            page_content = doc.page_content
            meta = doc.metadata
            ans.append({
                "restaurant_id": meta['id'],
                "description": page_content,
            })
        return ans

    def as_tool(self):
        return Tool(
            name="RestaurantSearch",
            func=self.search,
            description="Search for restaurant and restaurant menu information",
            args_schema=SingleTextArg,
        )


if __name__ == '__main__':
    load_dotenv('../.env')
    MongoDbSearchTool().search("sushi")
