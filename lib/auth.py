import socket
import sys
import os

# from six.moves import BaseHTTPServer
# from six.moves import urllib
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import urlparse
import urllib

class ClientRedirectServer(HTTPServer):
    """ A server to handle OAuth 2.0 redirects back to localhost.
    Waits for a single request and parses the query parameters
    into query_params and then stops serving.
    """
    query_params = {}

def MakeHandlerClass(root_path):
    class ClientRedirectHandler(BaseHTTPRequestHandler, object):
        """ A handler for OAuth 2.0 redirects back to localhost.
        Waits for two requests and parses the access token
        into the servers query_params and then stops serving.
        """
        def __init__(self, *args, **kwargs):
            self.root_path = root_path
            super(ClientRedirectHandler, self).__init__(*args, **kwargs)

        def do_GET(self):
            """ Handle a GET request.
                opens index.html and try to parse token
            """
            try:
                # f = open('static' + self.path)
                f = open(os.path.join(self.root_path, 'lib', 'static', self.path[1:]))
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
                return
            except IOError:
                self.send_error(404, 'File Not Found: {0}'.format(self.path))

        def do_POST(self):
            """ Handle a POST request.
                Should only ever be sending self urlencoded so
            """
            length = int(self.headers['content-length'])
            post_vars = urlparse.parse_qsl(self.rfile.read(length))
            self.server.query_params = dict(post_vars)
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.wfile.write(
                b"<html><head><title>Authentication Status</title></head>")
            self.wfile.write(
                b"<body><p>Authentication has completed.</p>")
            self.wfile.write(b"</body></html>")
    return ClientRedirectHandler


def run_oauth(host, root_path):
    r_host = 'localhost'  # host to redirect to
    r_ports = [9000, 9001, 9002]
    httpd = None
    server_started = False
    r_port = 0
    for port in r_ports:
        r_port = port
        try:
            ClientRedirectHandler = MakeHandlerClass(root_path)
            httpd = ClientRedirectServer((r_host, port), ClientRedirectHandler)
        except socket.error:
            pass
        else:
            server_started = True
            break
    if not server_started:
        sys.exit('Unable to start a local webserver listening on port 9000, 9001, or 9002. '
                 'Please unblock one of these ports for authorizing with Lingotek. '
                 'This local webserver will stop serving after two requests and free the port up again.')
    oauth_callback = 'http://{0}:{1}/index.html'.format(r_host, r_port)
    client_id = 'ab33b8b9-4c01-43bd-a209-b59f933e4fc4'
    response_type = 'token'
    payload = {'client_id': client_id, 'redirect_uri': oauth_callback, 'response_type': response_type}
    authorize_url = host + '/auth/authorize.html?' + urllib.urlencode(payload)
    import webbrowser
    webbrowser.open_new(authorize_url)
    print 'Your browser has been opened to visit: \n{0}\n'.format(authorize_url)

    httpd.handle_request()  # handle the GET redirect
    httpd.handle_request()  # handle the POST for token info

    if 'access_token' in httpd.query_params:
        print 'Found token, you may now close the browser.\n'
        token = httpd.query_params['access_token']
        # store the token because apparently it doesn't expire..
        return token
    sys.exit('Something went wrong with the authentication request, please try again.')

# run_oauth('https://cms.lingotek.com')
