import re
import brotli
# import zlib
import gzip

from .ad_deleter import AdDeleter


class HTTPRequest:
    START_RE = re.compile(rb'(CONNECT|GET|HEAD|PUT|POST|DELETE|TRACE|OPTIONS) (.+) (.+)')
    HOST_RE = re.compile(rb'Host: ([^:\r\n]+):?(\d+)?')

    def __init__(self, request):
        self.request = request
        self.method = None
        self.URL = None
        self.HTTP_v = None
        self.host = None
        self.host_port = None
        self._parse(request)

    def _parse(self, request):
        start_match = HTTPRequest.START_RE.search(request)
        if not start_match:
            print(request)
        self.method = start_match.group(1)
        self.URL = start_match.group(2)
        self.HTTP_v = start_match.group(3).strip(b'\r')

        host_match = HTTPRequest.HOST_RE.search(request)
        self.host = host_match.group(1)
        self.host_port = host_match.group(2)


class HTTPResponse:
    HTML_CONT_TYP_RE = re.compile(rb'Content-Type: text/html')
    HTML_CHARSET_RE = re.compile(rb'Content-Type: text/html; charset=(.+)?')
    HTML_ENC_RE = re.compile(b'Content-Encoding: (.+)')

    def __init__(self, response):
        self.response = response
        self.is_html = self._is_html()
        self.charset = self._get_charset()
        self.content_encoding = self._get_content_encoding()

    def get_response(self):
        if not self.is_html:
            return self.response
        if self.content_encoding != 'gzip':
            return self.response
        headers, content = self._extract_content()
        decoded_content = gzip.decompress(content).decode(self.charset)
        altered_content = AdDeleter(decoded_content).get_content_without_ads()
        return headers + b'\r\n\r\n' + gzip.compress(altered_content.encode(self.charset))

    def _extract_content(self):
        sep = b'\r\n\r\n'
        headers, content = self.response.split(sep, maxsplit=1)
        return headers, content.strip(b'\r\n')

    def _is_html(self):
        return HTTPResponse.HTML_CONT_TYP_RE.search(self.response) is not None

    def _get_charset(self):
        match = HTTPResponse.HTML_CHARSET_RE.search(self.response)
        if not match:
            return 'utf-8'
        return match.group(1).strip(b'\r\n').decode()

    def _get_content_encoding(self):
        match = HTTPResponse.HTML_ENC_RE.search(self.response)
        if not match:
            return None
        return match.group(1).strip(b'\r\n').decode()
