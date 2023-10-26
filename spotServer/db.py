import pymongo


class DB():
    def __init__(self):
        myclient = pymongo.MongoClient("mongodb://localhost:27017")
        self.db = myclient["spot-server"]

# global db
# db = DB()

# OriginalKeyPair = "mateoisgreat"
# RegionalKeyPair = "1234"
# data = {
#     "APIKeyPair": OriginalKeyPair,
#     "Regions": {
#         "place1": {
#             "KeyPair": RegionalKeyPair,
#             "instances": []
#         }
#     }
# }
# db.db.aws.insert_one(data)
# db.db.aws.update_many({"APIKeyPair": OriginalKeyPair},{"$set": {"Regions.place2": {"KeyPair": "1234", "instances": ["1", "2", "3"]}}})
# db.db.aws.update_many({"APIKeyPair": OriginalKeyPair},{"$push": {"Regions.place2.instances": "4"}})

# # how to get all regions an api key is calling
# for x in db.db.aws.find({"APIKeyPair": OriginalKeyPair}):
#   print(list(x["Regions"].keys()))
# # how get all apikeys installed
# for x in db.db.aws.find():
#   print(x["APIKeyPair"]) 

# db.db.aws.aggregate(
#         { "$match": {
#         "APIKeyPair" : OriginalKeyPair
#     }},
#     { "$unwind": "$Regions"},
#     { "$group:": {
#         "_id": "$Regions.KeyPair",
#         "count": {"$sum": "1" }
#     }}
# )
# {$set:{“address.permanent address”:{“state”: “UP”, “country”: “India”}}}