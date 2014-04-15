

if __name__ == "__main__":
    import sys
    from fuse import FUSE
    #from pubfs.fs.audio import AudioFilesystem
    from pubfs.fs.driver import PubfsDriver
    import mongoengine
    import logging

    if len(sys.argv) != 2:
        print("usage: driver <mount>")
        sys.exit(1)

    mongoengine.connect('pubfs')
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler(sys.stdout))


    #fuse = FUSE(AudioFilesystem(), sys.argv[1], foreground=True)
    fuse = FUSE(PubfsDriver(), sys.argv[1], foreground=True)
