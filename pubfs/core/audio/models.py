
from pubfs.core.models import db, BaseObject
import datetime

class InvalidAudioFileError(Exception):
    pass


class Artist(BaseObject):
    genres = db.ListField(db.StringField())

    @property
    def albums(self):
        if not hasattr(self, '_albums'):
            self._albums = Album.objects(artist=self)
        return self._albums


class Album(BaseObject):
    artist = db.ReferenceField(Artist, required=False)
    release_date = db.DateTimeField()
    #cover_image = db.ImageField()
    is_compilation = db.BooleanField(default=False)
    is_live = db.BooleanField(default=False)

    @property
    def tracks(self):
        if not hasattr(self, '_tracks'):
            self._tracks = Track.objects(album= self)
        return self._tracks


class Track(BaseObject):
    album = db.ReferenceField(Album)
    number = db.IntField()
    disc = db.IntField()
    content = db.FileField()
    duration = db.IntField()
    sha1 = db.StringField()

    @classmethod
    def import_track(cls, path):
        from hsaudiotag import auto
        import mimetypes
        import hashlib
        tags = auto.File(path)

        if not tags.valid:
            raise InvalidAudioFileError("invalid audio file")

        if not tags.title.strip():
            raise InvalidAudioFileError("missing track title")

        lookup = tags.artist.strip()
        if not lookup:
            raise InvalidAudioFileError("missing artist name")

        artist = Artist.objects(name__iexact=lookup)
        artist = artist[0] if artist.count() else Artist(name=lookup)

        lookup = tags.album.strip()
        if not lookup:
            raise InvalidAudioFileError("missing album name")

        album = Album.objects(name__iexact=lookup)
        album = album[0] if album.count() else Album(name=lookup)

        if not artist.id:
            baseg = tags.genre.strip()
            artist.genres = [baseg] if baseg else []
            #print("Saving artist:", artist.to_json())
            artist.save()
        else:
            #print("Found artist:", artist.to_json())
            pass

        if not album.id:
            #print("Saving album:", album.to_json())
            if tags.year and tags.year.isdigit():
                album.release_date = datetime.datetime(int(tags.year), 1, 1)
            album.artist = artist
            album.save()
        else:
            pass
            #print("Found album:", album.to_json())

        dup = Track.objects(name__iexact=tags.title.strip(), album=album)
        if dup.count():
            #print("duplicate track")
            return

        track = Track(
            name=tags.title.strip(),
            number=tags.track,
            disc=tags.disc,
            duration=tags.duration,
            album=album
        )

        (filetype, encoding) = mimetypes.guess_type(path)
        '''
        fp = open(path, 'rb')
        track.content.put(fp, filetype=filetype)
        '''

        sha1 = hashlib.sha1()
        track.content.new_file(filename=os.path.basename(path), filetype=filetype)
        with open(path, 'rb') as fp:
            chunk = fp.read(0x1000)
            while chunk:
                track.content.write(chunk)
                sha1.update(chunk)
                chunk = fp.read(0x1000)

        track.content.close()
        track.sha1 = sha1.hexdigest()
        track.save()

        #print("Saved track:", track.to_json())



