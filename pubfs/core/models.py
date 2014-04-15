
import mongoengine as db

class BaseObject(db.Document):
    meta = {'allow_inheritance': True}
    
    name = db.StringField(required=True)
    tags = db.ListField(db.StringField())
    revision = db.IntField(default=1)


