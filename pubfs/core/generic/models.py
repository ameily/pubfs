
from pubfs.models import BaseObject, db


class GenericFile(BaseObject):
    path = db.StringField()
    content = db.FileField()
