import gzip
import htmlentitydefs
import HTMLParser
import locale
import os
import re
import sys
import zlib
import urllib2
import email.utils

import datetime
import httplib
import socket
import urllib
from urlparse import parse_qs

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO


std_headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:5.0.1) Gecko/20100101 Firefox/5.0.1',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-us,en;q=0.5',
}




_VALID_URL = r'^((?:https?://)?(?:youtu\.be/|(?:\w+\.)?youtube(?:-nocookie)?\.com/)(?!view_play_list|my_playlists|artist|playlist)(?:(?:(?:v|embed|e)/)|(?:(?:watch(?:_popup)?(?:\.php)?)?(?:\?|#!?)(?:.+&)?v=))?)?([0-9A-Za-z_-]+)(?(1).+)?$'
_LANG_URL = r'http://www.youtube.com/?hl=en&persist_hl=1&gl=US&persist_gl=1&opt_out_ackd=1'
_LOGIN_URL = 'https://www.youtube.com/signup?next=/&gl=US&hl=en'
_AGE_URL = 'http://www.youtube.com/verify_age?next_url=/&gl=US&hl=en'
_NEXT_URL_RE = r'[\?&]next_url=([^&]+)'
_NETRC_MACHINE = 'youtube'
# Listed in order of quality
_available_formats = ['38', '37', '46', '22', '45', '35', '44', '34', '18', '43', '6', '5', '17', '13']
_available_formats_prefer_free = ['38', '46', '37', '45', '22', '44', '35', '43', '34', '18', '6', '5', '17', '13']
_video_extensions = {
    '13': '3gp',
    '17': 'mp4',
    '18': 'mp4',
    '22': 'mp4',
    '37': 'mp4',
    '38': 'video',  # You actually don't know if this will be MOV, AVI or whatever
    '43': 'webm',
    '44': 'webm',
    '45': 'webm',
    '46': 'webm',
}
_video_dimensions = {
    '5': '240x400',
    '6': '???',
    '13': '???',
    '17': '144x176',
    '18': '360x640',
    '22': '720x1280',
    '34': '360x640',
    '35': '480x854',
    '37': '1080x1920',
    '38': '3072x4096',
    '43': '360x640',
    '44': '480x854',
    '45': '720x1280',
    '46': '1080x1920',
}
IE_NAME = u'youtube'


def extract(url):
    for exception in _extract(url):
        pass

    if isinstance(exception, Results):
        return exception.args[0]

    else:
        raise exception


def _extract(url):
    # Extract original video URL from URL with redirection, like age verification, using next_url parameter
    mobj = re.search(_NEXT_URL_RE, url)
    if mobj:
        url = 'http://www.youtube.com/' + urllib.unquote(mobj.group(1)).lstrip('/')

    # Extract video id from URL
    mobj = re.match(_VALID_URL, url)
    if mobj is None:
        yield Trouble(u'ERROR: invalid URL: %s' % url)
        return

    video_id = mobj.group(2)

    # Get video webpage
    # TODO: replace with requests?
    request = urllib2.Request('http://www.youtube.com/watch?v=%s&gl=US&hl=en&has_verified=1' % video_id)
    try:
        video_webpage = urllib2.urlopen(request).read()
    except (urllib2.URLError, httplib.HTTPException, socket.error), err:
        yield Trouble(u'ERROR: unable to download video webpage: %s' % str(err))
        return

    # Attempt to extract SWF player URL
    mobj = re.search(r'swfConfig.*?"(http:\\/\\/.*?watch.*?-.*?\.swf)"', video_webpage)
    if mobj is not None:
        player_url = re.sub(r'\\(.)', r'\1', mobj.group(1))
    else:
        player_url = None

    # Get video info
    for el_type in ['&el=embedded', '&el=detailpage', '&el=vevo', '']:
        video_info_url = ('http://www.youtube.com/get_video_info?&video_id=%s%s&ps=default&eurl=&gl=US&hl=en'
                % (video_id, el_type))
        request = urllib2.Request(video_info_url)
        try:
            video_info_webpage = urllib2.urlopen(request).read()
            video_info = parse_qs(video_info_webpage)
            if 'token' in video_info:
                break
        except (urllib2.URLError, httplib.HTTPException, socket.error), err:
            yield Trouble(u'ERROR: unable to download video info webpage: %s' % str(err))
            return
    if 'token' not in video_info:
        if 'reason' in video_info:
            yield Trouble(u'ERROR: YouTube said: %s' % video_info['reason'][0].decode('utf-8'))
        else:
            yield Trouble(u'ERROR: "token" parameter not in video info for unknown reason')
        return

    # Check for "rental" videos
    if 'ypc_video_rental_bar_text' in video_info and 'author' not in video_info:
        yield Trouble(u'ERROR: "rental" videos not supported')
        return

    # Start extracting information
    #self.report_information_extraction(video_id)

    # uploader
    if 'author' not in video_info:
        yield Trouble(u'ERROR: unable to extract uploader nickname')
        return
    video_uploader = urllib.unquote_plus(video_info['author'][0])

    # title
    if 'title' not in video_info:
        yield Trouble(u'ERROR: unable to extract video title')
        return
    video_title = urllib.unquote_plus(video_info['title'][0])
    video_title = video_title.decode('utf-8')

    # thumbnail image
    if 'thumbnail_url' not in video_info:
        yield Trouble(u'WARNING: unable to extract video thumbnail')
        video_thumbnail = ''
    else:   # don't panic if we can't find it
        video_thumbnail = urllib.unquote_plus(video_info['thumbnail_url'][0])

    # upload date
    upload_date = u'NA'
    mobj = re.search(r'id="eow-date.*?>(.*?)</span>', video_webpage, re.DOTALL)
    if mobj is not None:
        upload_date = ' '.join(re.sub(r'[/,-]', r' ', mobj.group(1)).split())
        format_expressions = ['%d %B %Y', '%B %d %Y', '%b %d %Y']
        for expression in format_expressions:
            try:
                upload_date = datetime.datetime.strptime(upload_date, expression).strftime('%Y%m%d')
            except:
                pass

    # description
    video_description = get_element_by_id("eow-description", video_webpage.decode('utf8'))
    if video_description:
        video_description = clean_html(video_description)
    else:
        video_description = ''

    # token
    video_token = urllib.unquote_plus(video_info['token'][0])

    # Decide which formats to download
    req_format = None

    if 'conn' in video_info and video_info['conn'][0].startswith('rtmp'):
        video_url_list = [(None, video_info['conn'][0])]
    elif 'url_encoded_fmt_stream_map' in video_info and len(video_info['url_encoded_fmt_stream_map']) >= 1:
        url_data_strs = video_info['url_encoded_fmt_stream_map'][0].split(',')
        url_data = [parse_qs(uds) for uds in url_data_strs]
        url_data = filter(lambda ud: 'itag' in ud and 'url' in ud, url_data)
        url_map = dict((ud['itag'][0], ud['url'][0]) for ud in url_data)

        format_limit = None
        available_formats = _available_formats
        if format_limit is not None and format_limit in available_formats:
            format_list = available_formats[available_formats.index(format_limit):]
        else:
            format_list = available_formats
        existing_formats = [x for x in format_list if x in url_map]
        if len(existing_formats) == 0:
            yield Trouble(u'ERROR: no known formats available for video')
            return
        if req_format is None or req_format == 'best':
            video_url_list = [(existing_formats[0], url_map[existing_formats[0]])] # Best quality
        elif req_format == 'worst':
            video_url_list = [(existing_formats[len(existing_formats)-1], url_map[existing_formats[len(existing_formats)-1]])] # worst quality
        elif req_format in ('-1', 'all'):
            video_url_list = [(f, url_map[f]) for f in existing_formats] # All formats
        else:
            # Specific formats. We pick the first in a slash-delimeted sequence.
            # For example, if '1/2/3/4' is requested and '2' and '4' are available, we pick '2'.
            req_formats = req_format.split('/')
            video_url_list = None
            for rf in req_formats:
                if rf in url_map:
                    video_url_list = [(rf, url_map[rf])]
                    break
            if video_url_list is None:
                yield Trouble(u'ERROR: requested format not available')
                return
    else:
        yield Trouble(u'ERROR: no conn or url_encoded_fmt_stream_map information found in video info')
        return

    results = []
    for format_param, video_real_url in video_url_list:
        # Extension
        video_extension = _video_extensions.get(format_param, 'flv')

        results.append({
            'id':       video_id.decode('utf-8'),
            'url':      video_real_url.decode('utf-8'),
            'uploader': video_uploader.decode('utf-8'),
            'upload_date':  upload_date,
            'title':    video_title,
            'ext':      video_extension.decode('utf-8'),
            'format':   (format_param is None and u'NA' or format_param.decode('utf-8')),
            'thumbnail':    video_thumbnail.decode('utf-8'),
            'description':  video_description,
            'player_url':   player_url
        })
    yield Results(results)



def preferredencoding():
    """Get preferred encoding.

    Returns the best encoding scheme for the system, based on
    locale.getpreferredencoding() and some further tweaks.
    """
    def yield_preferredencoding():
        try:
            pref = locale.getpreferredencoding()
            u'TEST'.encode(pref)
        except:
            pref = 'UTF-8'
        while True:
            yield pref
    return yield_preferredencoding().next()


def htmlentity_transform(matchobj):
    """Transforms an HTML entity to a Unicode character.

    This function receives a match object and is intended to be used with
    the re.sub() function.
    """
    entity = matchobj.group(1)

    # Known non-numeric HTML entity
    if entity in htmlentitydefs.name2codepoint:
        return unichr(htmlentitydefs.name2codepoint[entity])

    # Unicode character
    mobj = re.match(ur'(?u)#(x?\d+)', entity)
    if mobj is not None:
        numstr = mobj.group(1)
        if numstr.startswith(u'x'):
            base = 16
            numstr = u'0%s' % numstr
        else:
            base = 10
        return unichr(long(numstr, base))

    # Unknown entity in name, return its literal representation
    return (u'&%s;' % entity)

HTMLParser.locatestarttagend = re.compile(r"""<[a-zA-Z][-.a-zA-Z0-9:_]*(?:\s+(?:(?<=['"\s])[^\s/>][^\s/=>]*(?:\s*=+\s*(?:'[^']*'|"[^"]*"|(?!['"])[^>\s]*))?\s*)*)?\s*""", re.VERBOSE) # backport bugfix
class IDParser(HTMLParser.HTMLParser):
    """Modified HTMLParser that isolates a tag with the specified id"""
    def __init__(self, id):
        self.id = id
        self.result = None
        self.started = False
        self.depth = {}
        self.html = None
        self.watch_startpos = False
        self.error_count = 0
        HTMLParser.HTMLParser.__init__(self)

    def error(self, message):
        print >> sys.stderr, self.getpos()
        if self.error_count > 10 or self.started:
            raise HTMLParser.HTMLParseError(message, self.getpos())
        self.rawdata = '\n'.join(self.html.split('\n')[self.getpos()[0]:]) # skip one line
        self.error_count += 1
        self.goahead(1)

    def loads(self, html):
        self.html = html
        self.feed(html)
        self.close()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.started:
            self.find_startpos(None)
        if 'id' in attrs and attrs['id'] == self.id:
            self.result = [tag]
            self.started = True
            self.watch_startpos = True
        if self.started:
            if not tag in self.depth: self.depth[tag] = 0
            self.depth[tag] += 1

    def handle_endtag(self, tag):
        if self.started:
            if tag in self.depth: self.depth[tag] -= 1
            if self.depth[self.result[0]] == 0:
                self.started = False
                self.result.append(self.getpos())

    def find_startpos(self, x):
        """Needed to put the start position of the result (self.result[1])
        after the opening tag with the requested id"""
        if self.watch_startpos:
            self.watch_startpos = False
            self.result.append(self.getpos())
    handle_entityref = handle_charref = handle_data = handle_comment = \
    handle_decl = handle_pi = unknown_decl = find_startpos

    def get_result(self):
        if self.result == None: return None
        if len(self.result) != 3: return None
        lines = self.html.split('\n')
        lines = lines[self.result[1][0]-1:self.result[2][0]]
        lines[0] = lines[0][self.result[1][1]:]
        if len(lines) == 1:
            lines[-1] = lines[-1][:self.result[2][1]-self.result[1][1]]
        lines[-1] = lines[-1][:self.result[2][1]]
        return '\n'.join(lines).strip()

def get_element_by_id(id, html):
    """Return the content of the tag with the specified id in the passed HTML document"""
    parser = IDParser(id)
    try:
        parser.loads(html)
    except HTMLParser.HTMLParseError:
        pass
    return parser.get_result()


def clean_html(html):
    """Clean an HTML snippet into a readable string"""
    # Newline vs <br />
    html = html.replace('\n', ' ')
    html = re.sub('\s*<\s*br\s*/?\s*>\s*', '\n', html)
    # Strip html tags
    html = re.sub('<.*?>', '', html)
    # Replace html entities
    html = unescapeHTML(html)
    return html


def sanitize_open(filename, open_mode):
    """Try to open the given filename, and slightly tweak it if this fails.

    Attempts to open the given filename. If this fails, it tries to change
    the filename slightly, step by step, until it's either able to open it
    or it fails and raises a final exception, like the standard open()
    function.

    It returns the tuple (stream, definitive_file_name).
    """
    try:
        if filename == u'-':
            if sys.platform == 'win32':
                import msvcrt
                msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
            return (sys.stdout, filename)
        stream = open(encodeFilename(filename), open_mode)
        return (stream, filename)
    except (IOError, OSError), err:
        # In case of error, try to remove win32 forbidden chars
        filename = re.sub(ur'[/<>:"\|\?\*]', u'#', filename)

        # An exception here should be caught in the caller
        stream = open(encodeFilename(filename), open_mode)
        return (stream, filename)


def timeconvert(timestr):
    """Convert RFC 2822 defined time string into system timestamp"""
    timestamp = None
    timetuple = email.utils.parsedate_tz(timestr)
    if timetuple is not None:
        timestamp = email.utils.mktime_tz(timetuple)
    return timestamp

def sanitize_filename(s):
    """Sanitizes a string so it could be used as part of a filename."""
    def replace_insane(char):
        if char in u' .\\/|?*<>:"' or ord(char) < 32:
            return '_'
        return char
    return u''.join(map(replace_insane, s)).strip('_')

def orderedSet(iterable):
    """ Remove all duplicates from the input iterable """
    res = []
    for el in iterable:
        if el not in res:
            res.append(el)
    return res

def unescapeHTML(s):
    """
    @param s a string (of type unicode)
    """
    assert type(s) == type(u'')

    result = re.sub(ur'(?u)&(.+?);', htmlentity_transform, s)
    return result

def encodeFilename(s):
    """
    @param s The name of the file (of type unicode)
    """

    assert type(s) == type(u'')

    if sys.platform == 'win32' and sys.getwindowsversion().major >= 5:
        # Pass u'' directly to use Unicode APIs on Windows 2000 and up
        # (Detecting Windows NT 4 is tricky because 'major >= 4' would
        # match Windows 9x series as well. Besides, NT 4 is obsolete.)
        return s
    else:
        return s.encode(sys.getfilesystemencoding(), 'ignore')

class DownloadError(Exception):
    """Download Error exception.

    This exception may be thrown by FileDownloader objects if they are not
    configured to continue on errors. They will contain the appropriate
    error message.
    """
    pass


class SameFileError(Exception):
    """Same File exception.

    This exception will be thrown by FileDownloader objects if they detect
    multiple files would have to be downloaded to the same file on disk.
    """
    pass


class PostProcessingError(Exception):
    """Post Processing exception.

    This exception may be raised by PostProcessor's .run() method to
    indicate an error in the postprocessing task.
    """
    pass

class MaxDownloadsReached(Exception):
    """ --max-downloads limit has been reached. """
    pass


class UnavailableVideoError(Exception):
    """Unavailable Format exception.

    This exception will be thrown when a video is requested
    in a format that is not available for that video.
    """
    pass


class ContentTooShortError(Exception):
    """Content Too Short exception.

    This exception may be raised by FileDownloader objects when a file they
    download is too small for what the server announced first, indicating
    the connection was probably interrupted.
    """
    # Both in bytes
    downloaded = None
    expected = None

    def __init__(self, downloaded, expected):
        self.downloaded = downloaded
        self.expected = expected


class Results(Exception):
    pass

class Trouble(Exception):
    """Trouble helper exception

    This is an exception to be handled with
    FileDownloader.trouble
    """
    pass

class YoutubeDLHandler(urllib2.HTTPHandler):
    """Handler for HTTP requests and responses.

    This class, when installed with an OpenerDirector, automatically adds
    the standard headers to every HTTP request and handles gzipped and
    deflated responses from web servers. If compression is to be avoided in
    a particular request, the original request in the program code only has
    to include the HTTP header "Youtubedl-No-Compression", which will be
    removed before making the real request.

    Part of this code was copied from:

    http://techknack.net/python-urllib2-handlers/

    Andrew Rowls, the author of that code, agreed to release it to the
    public domain.
    """

    @staticmethod
    def deflate(data):
        try:
            return zlib.decompress(data, -zlib.MAX_WBITS)
        except zlib.error:
            return zlib.decompress(data)

    @staticmethod
    def addinfourl_wrapper(stream, headers, url, code):
        if hasattr(urllib2.addinfourl, 'getcode'):
            return urllib2.addinfourl(stream, headers, url, code)
        ret = urllib2.addinfourl(stream, headers, url)
        ret.code = code
        return ret

    def http_request(self, req):
        for h in std_headers:
            if h in req.headers:
                del req.headers[h]
            req.add_header(h, std_headers[h])
        if 'Youtubedl-no-compression' in req.headers:
            if 'Accept-encoding' in req.headers:
                del req.headers['Accept-encoding']
            del req.headers['Youtubedl-no-compression']
        return req

    def http_response(self, req, resp):
        old_resp = resp
        # gzip
        if resp.headers.get('Content-encoding', '') == 'gzip':
            gz = gzip.GzipFile(fileobj=StringIO.StringIO(resp.read()), mode='r')
            resp = self.addinfourl_wrapper(gz, old_resp.headers, old_resp.url, old_resp.code)
            resp.msg = old_resp.msg
        # deflate
        if resp.headers.get('Content-encoding', '') == 'deflate':
            gz = StringIO.StringIO(self.deflate(resp.read()))
            resp = self.addinfourl_wrapper(gz, old_resp.headers, old_resp.url, old_resp.code)
            resp.msg = old_resp.msg
        return resp
