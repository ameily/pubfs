
from fuse import Operations, FuseOSError, LoggingMixIn
from pubfs.core.audio.models import Artist, Album, Track
import os
import time
import stat
import errno

RootPath = 0
AudioRootPath = 1
AudioArtistPath = 2
AudioAlbumPath = 3
AudioTrackPath = 4
GenericFilePath = 5


class PubfsPath(object):

    def __init__(self, spec):
        self.spec = spec
        self.artist = self.album = self.track = self.fp = None
        self.lock = False

    def acquire(self):
        while self.lock:
            pass
        self.lock = True

    def release(self):
        self.lock = False

class PathParser(object):

    def __init__(self):
        self.db_transforms = {}
        self.fs_transforms = {}

    def clean_fs_part(self, p):
        if p in self.db_transforms:
            return self.db_transforms[p]
        return p

    def clean_db_part(self, p):
        if p in self.fs_transforms:
            return self.fs_transforms[p]

        if '/' in p:
            r = self.fs_transforms[p] = p.replace('/', '-')
            self.db_transforms[r] = p
            p = r
        else:
            self.fs_transforms[p] = self.db_transforms[p] = p
        return p

    def parse(self, path):
        parts = [self.clean_fs_part(p) for p in path.split('/') if p]
        path = None
        if not parts:
            path = PubfsPath(RootPath)
        elif parts[0] == 'Music':
            path = self.parse_audio(parts[1:])
        elif parts[0] == 'Files':
            path = self.parse_generic(parts[1:])
        else:
            raise FuseOSError(errno.ENOENT)

        return path

    def get_artist(self, name):
        try:
            artist = Artist.objects.get(name=name)
            return artist
        except:
            raise FuseOSError(errno.ENOENT)

    def get_album(self, artist, name):
        try:
            album = Album.objects.get(name=name, artist=artist)
            return album
        except:
            raise FuseOSError(errno.ENOENT)

    def get_track(self, album, name):
        (name, ext) = os.path.splitext(name)
        try:
            track = Track.objects.get(name=name, album=album)
            return track
        except:
            raise FuseOSError(errno.ENOENT)

    def parse_audio(self, parts):
        path = None
        if not parts:
            path = PubfsPath(AudioRootPath)
        else:
            path = PubfsPath(1+len(parts))
            path.artist = self.get_artist(parts[0])

            if len(parts) >= 2:
                path.album = self.get_album(path.artist, parts[1])

            if len(parts) >= 3:
                path.track = self.get_track(path.album, parts[2])

            if len(parts) > 3:
                raise FuseOSError(errno.ENOENT)
        return path

    def parse_generic(self, parts):
        return PubfsPath(GenericFilePath)

class PubfsDriver(Operations): #LoggingMixIn

    def __init__(self):
        self.parser = PathParser()
        self.handles = {}
        self.fd = 0

    def open(self, req, flags):
        path = self.parser.parse(req)
        self.fd += 1
        fd = self.fd
        self.handles[fd] = path
        if path.spec == AudioTrackPath:
            path.fp = path.track.content

        return fd

    def release(self, path, fh):
        if fh in self.handles:
            del self.handles[fh]

    def readdir(self, req, fh):
        path = None
        if fh in self.handles:
            path = self.handles[fh]
        else:
            path = self.parser.parse(req)

        ls = []
        if path.spec == RootPath:
            ls += ["Files", "Music"]
        elif path.spec == AudioRootPath:
            for artist in Artist.objects():
                ls.append(self.parser.clean_db_part(artist.name))
        elif path.spec == AudioArtistPath:
            for album in path.artist.albums:
                ls.append(self.parser.clean_db_part(album.name))
        elif path.spec == AudioAlbumPath:
            for track in path.album.tracks:
                name = None
                if track.number:
                    name = "{:>02} - {}".format(track.number, track.name)
                else:
                    name = self.parser.clean_db_part(track.name)
                ls.append(name + ".mp3") #TODO
        elif path.spec == GenericFilePath:
            pass
        else:
            raise FuseOSError(errno.ENODATA)

        ls = ['.', '..'] + sorted(ls)
        return ls

    def getattr(self, req, fh):
        print("getattr(", req, ",", fh, ")")
        path = None
        if fh:
            path = self.handles[fh]
        else:
            path = self.parser.parse(req)

        d = dict(
            st_mode=0,
            st_nlink=2,
            #st_size=0x1000,
            st_ctime=0,
            st_mtime=0,
            st_atime=int(time.time()),
            #st_uid=0,
            #st_gid=0
        )

        ctime_obj = None
        if path.spec == RootPath:
            d['st_mode'] = stat.S_IFDIR | 0o775
        elif path.spec == AudioRootPath or path.spec == GenericFilePath:
            d['st_mode'] = stat.S_IFDIR | 0o775
            #ctime_obj = path.artist
        elif path.spec == AudioArtistPath:
            d['st_mode'] = stat.S_IFDIR | 0o775
            ctime_obj = path.artist
        elif path.spec == AudioAlbumPath:
            d['st_mode'] = stat.S_IFDIR | 0o775
            ctime_obj = path.album
        elif path.spec == AudioTrackPath:
            d['st_mode'] = stat.S_IFREG | 0o664
            ctime_obj = path.track
            d['st_size'] = path.track.content.length

        if ctime_obj:
            d['st_ctime'] = d['st_mtime'] = time.mktime(ctime_obj.id.generation_time.timetuple())

        return d

    def read(self, path, size, offset, fh):
        path = self.handles[fh]
        path.acquire()
        path.fp.seek(offset, 0)
        b = path.fp.read(size)
        path.release()
        return b
