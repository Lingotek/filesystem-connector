import socket
import sys

# from six.moves import BaseHTTPServer
# from six.moves import urllib
import BaseHTTPServer
import urlparse
import urllib

from info import CLIENT_ID

class ClientRedirectServer(BaseHTTPServer.HTTPServer):
    """ A server to handle OAuth 2.0 redirects back to localhost.
    Waits for a single request and parses the query parameters
    into query_params and then stops serving.
    """
    query_params = {}

class ClientRedirectHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """ A handler for OAuth 2.0 redirects back to localhost.
    Waits for a single request and parses the query parameters
    into the servers query_params and then stops serving.
    """

    def do_GET(self):
        """ Handle a GET request.
        Parses the query parameters and prints a message
        if the flow has completed. Note that we can't detect
        if an error occurred.
        """
        print 'self path before send response: {0}'.format(self.path)
        # todo path is currently '/'
        print self.headers
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        query = self.path.split('#', 1)[-1]
        print 'query: {0}'.format(query)
        query = dict(urlparse.parse_qsl(query))
        self.server.query_params = query
        self.wfile.write(
            b"<html><head><title>Authentication Status</title></head>")
        self.wfile.write(
            b"<body><p>Authentication has completed.</p>")
        self.wfile.write(b"</body></html>")

def run_oauth(host=None):
    r_host = 'localhost'  # host to redirect to
    r_port = 9001
    httpd = None
    try:
        httpd = ClientRedirectServer((r_host, r_port), ClientRedirectHandler)
    except socket.error:
        pass
    # todo some error checking about if webserver was able to start on 9001
    oauth_callback = 'http://{0}:{1}/'.format(r_host, r_port)
    client_id = CLIENT_ID
    response_type = 'token'
    payload = {'client_id': client_id, 'redirect_uri': oauth_callback, 'response_type': response_type}
    authorize_url = host + '/auth/authorize.html?' + urllib.urlencode(payload)
    import webbrowser
    webbrowser.open_new(authorize_url)
    print 'Your browser has been opened to visit: \n{0}\n'.format(authorize_url)

    token = None
    httpd.handle_request()
    print httpd.query_params
    if 'error' in httpd.query_params:
        sys.exit('Authentication request was rejected.')
    if 'access_token' in httpd.query_params:
        token = httpd.query_params['access_token']
        print token
    # store the token because apparently it doesn't expire..

run_oauth('https://cms.lingotek.com')
# run_oauth()
