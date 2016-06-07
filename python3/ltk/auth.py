import socket
import sys

# from six.moves import BaseHTTPServer
# from six.moves import urllib
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
# import warnings
#
# with warnings.catch_warnings():
#     warnings.filterwarnings("ignore")
#     import webbrowser

class ClientRedirectServer(HTTPServer):
    """ A server to handle OAuth 2.0 redirects back to localhost.
    Waits for a single request and parses the query parameters
    into query_params and then stops serving.
    """
    query_params = {}

class ClientRedirectHandler(BaseHTTPRequestHandler, object):
    """ A handler for OAuth 2.0 redirects back to localhost.
    Waits for two requests and parses the access token
    into the servers query_params and then stops serving.
    """
    def do_GET(self):
        """ Handle a GET request.
            opens index.html and try to parse token
        """
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(
            b"<html><head><title>Authentication Status</title>")
        self.wfile.write(
            b'<script src="https://ajax.googleapis.com/ajax/libs/jquery/2.1.4/jquery.min.js"></script></head>')
        self.wfile.write(
            b"<link href='https://fonts.googleapis.com/css?family=Open+Sans' rel='stylesheet' type='text/css'>")
        self.wfile.write(
            b'<body style=\'font-size: 1.5em; padding: 50px;\'>')
        self.wfile.write(b'<p id="message" style="font-family: Open Sans, Arial; background-color: #eee; text-align: center; border: 1px solid #5cb85e; padding: 5px 20px 25px 20px;">Retrieving your access token...</p>')
        self.wfile.write(b'<script> \
            $(document).ready(function(){ \
                function getParamFromHash(url, param) { \
                    var re = new RegExp("#.*" + param + "=([^&]+)(&|$)"); \
                    var match = url.match(re); \
                    return(match ? match[1] : ""); \
                } \
                var self_url = window.location.href; \
                var token_info = self_url.split("#")[1]; \
                var params = { \
                    access_token: getParamFromHash(self_url, "access_token"), \
                    expires_in: getParamFromHash(self_url, "expires_in"), \
                    token_type: getParamFromHash(self_url, "token_type") \
                }; \
                console.log(params); \
                $.post("index.html", params).done(function(data) { \
                    $("#message").css("background-color","#dff0d9"); \
                    $("#message").html("<div><p style=\'font-weight: bold; color: darkgreen;\'>'
                         b'Your access token has been successfully stored!</p>'
                         b'<p style=\'color: #666; font-size: .8em\'>You may now close this browser window and return to the terminal.</p>'
                         b'<p style=\'color: #aaa; font-size: .5em\'>" + params["access_token"] + "</p></div>"); \
                }); \
            }); \
        </script>')
        self.wfile.write(b'</body></html>')

    def do_POST(self):
        """ Handle a POST request.
            Should only ever be sending self urlencoded so
        """
        length = int(self.headers['content-length'])
        post_vars = urllib.parse.parse_qsl(self.rfile.read(length))
        self.server.query_params = dict(post_vars)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html><head><title>Authentication Response Status</title></head><body>")
        self.wfile.write(b"<p>Authentication has completed.</p>")
        self.wfile.write(b"</body></html>")


def run_oauth(host):
    print ('running oauth')
    r_host = 'localhost'  # host to redirect to
    r_ports = [9000, 9001, 9002]
    httpd = None
    server_started = False
    r_port = 0
    for port in r_ports:
        r_port = port
        try:
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
    oauth_callback = 'http://{0}:{1}/'.format(r_host, r_port)
    client_id = 'ab33b8b9-4c01-43bd-a209-b59f933e4fc4'
    response_type = 'token'
    payload = {'client_id': client_id, 'redirect_uri': oauth_callback, 'response_type': response_type}
    authorize_url = host + '/auth/authorize.html?' + urllib.parse.urlencode(payload)
    import webbrowser
    webbrowser.open_new(authorize_url)
    print ('Your browser has been opened to visit: \n{0}\n'.format(authorize_url))
    print ('--------------------------------------')
    httpd.handle_request()  # handle the GET redirect
    httpd.handle_request()  # handle the POST for token info
    print ('--------------------------------------\n')
    if b'access_token' in httpd.query_params:
        print ('Access token has been successfully stored!')
        print ('(If you haven\'t already, you may close your browser.)\n')
        init_token = httpd.query_params[b'access_token']
        init_token = init_token.decode("utf-8")
        print('init token',init_token)

        token = init_token.split('&')[0]
        # store the token because apparently it doesn't expire..
        webbrowser.open_new('https://www.youtube.com/watch?v=CbsvVar2rFs')
        return token
    sys.exit('Something went wrong with the authentication request, please try again.')

# run_oauth('https://cms.lingotek.com')
