import musicbrainzngs
import requests

def sources(recordingid):
    res = requests.get('http://185.97.32.250:8468/mbid:{}'.format(recordingid))
    #import pdb;pdb.set_trace()
    if not b'None' in res.content:
        return res.content.decode('utf-8')
musicbrainzngs.set_useragent("mb.py", "0", contact="mikael@frykholm.com")
res = musicbrainzngs.search_artists("Ablaze")
for artist in res['artist-list']:
    print(artist['name'], artist['id'])
#import pdb;pdb.set_trace()
res = musicbrainzngs.browse_releases(artist='d2c0d69e-e3ca-45a4-a540-6ce42c617599', limit=100)
for release in res['release-list']:
    print(release['title'])
    recordings = musicbrainzngs.browse_recordings(release=release['id'])
    for rec in recordings['recording-list']:
#        import pdb;pdb.set_trace()
        print("\t\t",rec['title'],'\t', end='')
        print(sources(rec['id']))
#import pdb;pdb.set_trace()
