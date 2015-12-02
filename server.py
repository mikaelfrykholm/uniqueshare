import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import tornado.platform.twisted
tornado.platform.twisted.install()
import tornado.ioloop
import tornado.web
import hashlib
from os.path import join, getsize, exists
import mutagen
import pickle
import time
from twisted.internet import reactor
from kademlia.network import Server

if os.path.isfile('self.cache.pickle'):
    kserver = Server.loadState('self.cache.pickle')
else:
    kserver = Server()
    kserver.bootstrap([("185.97.32.250", 8468)])
kserver.saveStateRegularly('self.cache.pickle', 10)
kserver.listen(8468)

class FileServer(tornado.web.RequestHandler):
    def initialize(self, cache):
        self.cache=cache

    def get(self, arg):
        filename = self.cache[arg]
        with open(filename,"rb") as fp:
            self.set_header("Content-Type", "audio/mpeg")
            self.set_header('content-length',os.stat(fp.fileno()).st_size)
#            self.set_header('Content-Disposition',' inline; filename="{}"'.format(os.path.basename(fp.name)))
            self.write(fp.read())
            self.finish()

class MainHandler(tornado.web.RequestHandler):
    def initialize(self, dht, cache):
        self.dht = dht
        self.dht.set("key","value")
        self.cache=cache
        if not cache:
            self.scan()

    def scan(self):
        if exists("save.p"):
            self.cache = pickle.load(open( "save.p", "rb" ))
        for root, dirs, files in os.walk('/home/mikael/Music/Ablaze my sorrow'):
            for name in files:
                if name.startswith('.'):
                    continue
                with open(join(root, name),'rb') as fp:
                    print(fp.name)
                    #if 'user.sha256' not in attrs:
                    #    h = hashlib.sha256(fp.read())
                    #    sum = h.digest()
                    #    attrs['user.sha256'] = sum
                    modified = os.stat(fp.fileno()).st_mtime
                    if fp.name in self.cache:
                        if 'modified' in self.cache[fp.name]:
                            print(modified, self.cache[fp.name]['modified'])
                            if modified <= self.cache[fp.name]['modified']:
                                print("Optimized!")
                                continue
                    try:
                        rid = os.getxattr(fp.fileno(),'user.musicbrainz.recordingid').decode('utf-8')
                    except Exception as e:
                        rid = False
                    #    #import pdb;pdb.set_trace()
                    if rid:
                        self.cache["mbid:"+rid] = fp.name
                        self.cache[fp.name] = {}
                        self.cache[fp.name]['modified'] = modified
                        continue
                    else:
                        try:
                            metadata = mutagen.File(fp.name,easy=True)
                        except Exception as e:
                            metadata = False
                    if not metadata:
                        print("Missing!")
                        continue
                    if 'musicbrainz_trackid' in metadata:
                        os.setxattr(fp.fileno(),'user.musicbrainz.recordingid',metadata['musicbrainz_trackid'][0].encode('utf-8'))
                        self.cache[metadata['musicbrainz_trackid'][0]] = fp.name
                        if not fp.name in self.cache:
                            self.cache[fp.name] = {}
                        self.cache[fp.name]['modified'] = int(time.time())
                        #import pdb;pdb.set_trace()
        for key in cache:
            self.dht.set(key,"http://185.97.32.250:8468/by-mbid/"+key)
            #import pdb;pdb.set_trace()
    @tornado.web.asynchronous
    def get(self, arg):
        if arg == 'playlist':
            self.write("""<html><head>
              <script type="text/javascript">
    navigator.registerProtocolHandler("mbid","http://185.97.32.250:8468/by-mbid/%s","Musicbrainzhandler");
  </script>
  </head><body>
  <ul>
  <li><a href="mbid:b99529f5-da06-483c-80bc-7a1b510d0cb5"> 01 - Erased relieved</a></li>
  <li><a href="mbid:0dab7ebd-7b51-49e6-a0ac-b785a5b91155">02 - Suicidal</a></li>
  </body>
  """)

            self.finish()
            return
        if arg == "playlist.m3u8":
                self.write(
                    "mbid:b99529f5-da06-483c-80bc-7a1b510d0cb5\n"
                    "mbid:0dab7ebd-7b51-49e6-a0ac-b785a5b91155"
                )
                self.finish()
                return
        def respond(value):
            if value:
                self.write(value.encode("utf-8"))
            else: 
                self.write("None found")
            self.finish()
        d = self.dht.get(arg)
        d.addCallback(respond)

if __name__ == "__main__":
    cache = {}
    app = tornado.web.Application([
        (r"/by-mbid/(.*)", FileServer,{"cache":cache}),
        (r"/(.*)", MainHandler,{"dht":kserver,"cache":cache}),
    ])
    app.listen(8468)
    tornado.ioloop.IOLoop.current().start()

