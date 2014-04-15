

def test_fs():
    from pubfs.fs.audio import AudioFilesystem
    fs = AudioFilesystem()
    print(">>> Artists <<<<")
    print("   ", '\n    '.join(fs.readdir("", 0)))
    print()

    print()
    print(">>> Accept Albums <<<")
    print("   ", '\n    '.join(fs.readdir("Accept", 0)))
    print()

    print()
    print(">>> Breaker Tracks <<<")
    print("   ", '\n    '.join(fs.readdir("Accept/Breaker", 0)))
    print()


if __name__ == "__main__":
    from pubfs.core.audio.models import Track
    from mongoengine import connect
    import os
    import sys

    connect("pubfs")

    test_fs()
    sys.exit(0)

    #tracks = (
    #    "/storage/Music/Iced Earth/The Blessed And The Damned/Burning Times.mp3",
    #    "/storage/Music/Accept/Breaker/01 - Starlight.mp3",
    #    "/storage/Music/Accept/Breaker/02 - Breaker.mp3",
    #    "/storage/Music/Accept/Balls To The Wall/01 - Balls To The Wall.mp3"
    #)

    tracks = []

    for (dirpath, dirs, files) in os.walk("/storage/Music"):
        for f in files:
            t = f.lower()
            if t.endswith(".mp3") or t.endswith(".m4a"):
                tracks.append(os.path.join(dirpath, f))

    #print("tracks:", len(tracks))
    #print("track[0]:", tracks[0])
    #sys.exit(0)

    i = 1
    count = len(tracks)
    for t in tracks:
        print("{:>4}/{:>4}: {}".format(i, count, os.path.basename(t)))
        Track.import_track(t)
        i += 1
        #pass

