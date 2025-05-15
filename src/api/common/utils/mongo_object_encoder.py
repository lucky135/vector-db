import datetime
import json
from bson import ObjectId

class MyJsonEncoder(json.JSONEncoder):
    """
        Contains custom encoder logic to handle serializing of bson documents from mongodb database
    """
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

def get_serialized_mongo_document(document):
    """
    Converts the MongoDB document into a JSON-serializable format and returns a JSON.
    
    Args:
        document (dict): The MongoDB document to serialize.
    
    Returns:
        serialized JSON data.
    """
    # Use json.dumps with MyJsonEncoder to serialize the document
    return json.loads(json.dumps(document, indent=4,  cls=MyJsonEncoder))
