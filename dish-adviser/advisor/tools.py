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
    # user_location: (longitude, latitude)
    # search_radius: in meters
    #
    # Location in MongoDb: [longitude, latitude]
    # Google Maps API location: [latitude, longitude]
    # It's important to keep in mind the difference between formats.
    # It's MongoDb format everywhere in the code.
    def __init__(self, user_lon_lat=(-82.33554135164104, 28.175078895215975), search_radius_miles=5):
        username = quote_plus(os.getenv("MONGO_GMATE_USERNAME"))
        password = quote_plus(os.getenv("MONGO_GMATE_PASSWORD"))
        cluster = os.getenv("MONGO_GMATE_CLUSTER")
        database_name = os.getenv("MONGO_GMATE_DATABASE")

        self.user_location = user_lon_lat
        self.search_radius = search_radius_miles

        uri = f"mongodb+srv://{username}:{password}@{cluster}.q1ds6re.mongodb.net/?retryWrites=true&w=majority"
        client = MongoClient(uri, server_api=ServerApi('1'))
        print(client.admin.command('ping'))
        db = client[database_name]
        restaurants_collection = db["restaurants"]
        embeddings = OpenAIEmbeddings()

        self.vectorstore = MongoDBAtlasVectorSearch(restaurants_collection, embeddings, index_name="vector_geo_index")
        self.db = db
        self.restaurants_collection = restaurants_collection
        self.embeddings = embeddings

    def search(self, query: str):
        # The code below suddenly stopped working with the following error: "$vectorSearch is not allowed"
        # The issue discussion thread: https://www.mongodb.com/community/forums/t/vectorsearch-is-not-allowed/248934
        #
        # search_result = self.vectorstore.similarity_search_with_score(
        #     query=query,
        #     k=2,
        #     pre_filter={
        #         "geoWithin": {
        #             "circle": {
        #                 "center": {
        #                     "type": "Point",
        #                     "coordinates": [-82.3355502759486, 28.17619853788267]
        #                 },
        #                 "radius": 10000
        #             },
        #             "path": "location"
        #         }
        #     },
        #     post_filter_pipeline=[{
        #         "$project": {
        #             "embedding": 0,
        #             "location": 0
        #         }
        #     }]
        # )
        # search_result = self.db.command('aggregate', 'vector_geo_index', pipeline=query, cursor={})
        # for res in search_result:
        #     doc, score = res
        #     page_content = doc.page_content
        #     meta = doc.metadata
        #     ans.append({
        #         "restaurant_id": meta['id'],
        #         "description": page_content,
        #     })

        # I decided not to use `MongoDBAtlasVectorSearch` and `$vectorSearch`
        # Instead, I created a MongoDB native query that uses `$search` with the `knnBeta` operator
        # The `knnBeta` operator is deprecated in favor of `$vectorSearch` but it still works
        mongo_query = [
            {
                "$search": {
                    "index": "vector_geo_index",
                    "knnBeta": {
                        "vector": self.embeddings.embed_query(query),
                        "path": "embedding",
                        "k": 2,
                        "filter": {
                            "geoWithin": {
                                "circle": {
                                    "center": {
                                        "type": "Point",
                                        "coordinates": self.user_location
                                    },
                                    "radius": 16000 # radius in meters: https://www.mongodb.com/docs/atlas/atlas-search/geoWithin/
                                    # I spend a lot of time trying to understand what units I should use for the radius
                                    # Read about radian raduis here: https://www.mongodb.com/docs/manual/core/indexes/index-types/geospatial/2d/calculate-distances/#std-label-calculate-distance-spherical-geometry
                                },
                                "path": "location"
                            }
                        }
                    }
                }
            },
            {
                "$project": {
                    "text": 1
                }
            }
        ]

        search_result = self.restaurants_collection.aggregate(mongo_query)
        ans = []
        for doc in search_result:
            ans.append({
                "restaurant_id": str(doc['_id']),
                "description": doc['text'],
            })
        return ans

    def as_langchain_tool(self) -> Tool:
        return Tool(
            name="RestaurantSearch",
            func=self.search,
            description="Search for restaurant and restaurant menu information",
            args_schema=SingleTextArg,
        )


if __name__ == '__main__':
    load_dotenv('../.env')
    MongoDbSearchTool().search("sushi")
