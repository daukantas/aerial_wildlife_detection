'''
    Main Bottle and routings for the UserHandling module.

    2019 Benjamin Kellenberger
'''

from bottle import request, response, static_file, abort, redirect
from .backend.middleware import UserMiddleware
from .backend.exceptions import *


class UserHandler():

    def __init__(self, config, app):
        self.config = config
        self.app = app
        self.staticDir = self.config.getProperty(self, 'staticfiles_dir')
        self.middleware = UserMiddleware(config)

        self._initBottle()


    def _parse_parameter(self, request, param):
        if not param in request:
            raise ValueMissingException(param)
        return request.get(param)


    def _initBottle(self):

        @self.app.route('/login', method='POST')
        def login():
            # check provided credentials
            try:
                username = self._parse_parameter(request.forms, 'username')
                password = self._parse_parameter(request.forms, 'password')

                # check if session token already provided; renew login if correct
                sessionToken = request.get_cookie('session_token')

                sessionToken, _, expires = self.middleware.login(username, password, sessionToken)
                
                response.set_cookie('username', username, expires=expires)
                response.set_cookie('session_token', sessionToken, expires=expires)

                return {
                    'expires': expires.strftime('%H:%M:%S')
                }

            except Exception as e:
                abort(403, str(e))
        

        @self.app.route('/loginCheck', method='POST')
        def loginCheck():
            try:
                username = request.get_cookie('username')
                if username is None:
                    username = self._parse_parameter(request.forms, 'username')

                sessionToken = request.get_cookie('session_token')

                _, _, expires = self.middleware.isLoggedIn(username, sessionToken)
                
                response.set_cookie('username', username, expires=expires)
                response.set_cookie('session_token', sessionToken, expires=expires)
                return {
                    'expires': expires.strftime('%H:%M:%S')
                }
                return response

            except Exception as e:
                abort(401, str(e))


        @self.app.route('/logout', method='GET')        
        @self.app.route('/logout', method='POST')
        def logout():
            try:
                username = request.get_cookie('username')
                sessionToken = request.get_cookie('session_token')
                self.middleware.logout(username, sessionToken)

                response.set_cookie('username', '', expires=0)
                response.set_cookie('session_token', '', expires=0)

                # send redirect
                response.status = 303
                response.set_header('Location', '/')
                return response

            except Exception as e:
                abort(403, str(e))


        @self.app.route('/createAccount', method='POST')
        def createAccount():
            #TODO: make secret token match
            try:
                username = self._parse_parameter(request.forms, 'username')
                password = self._parse_parameter(request.forms, 'password')
                email = self._parse_parameter(request.forms, 'email')

                sessionToken, _, expires = self.middleware.createAccount(
                    username, password, email
                )

                response.set_cookie('username', username, expires=expires)
                response.set_cookie('session_token', sessionToken, expires=expires)
                return {
                    'expires': expires.strftime('%H:%M:%S')
                }

            except Exception as e:
                abort(403, str(e))

        @self.app.route('/newAccount')
        def showNewAccountPage():
            return static_file('newAccount.html', root=self.staticDir)

        @self.app.route('/accountExists', method='POST')
        def checkAccountExists():
            try:
                username = self._parse_parameter(request.forms, 'username')
                if len(username) == 0:
                    raise Exception('invalid request.')
                return {
                    'response': str(self.middleware.accountExists(username))
                }
            except Exception as e:
                abort(401, str(e))

        @self.app.route('/checkAuthenticated', method='POST')
        def checkAuthenticated():
            try:
                if self.checkAuthenticated():
                    return True
                else:
                    raise Exception('not authenticated.')
            except Exception as e:
                    abort(401, str(e))
            return response


    def checkAuthenticated(self):
        try:
            username = request.get_cookie('username')
            sessionToken = request.get_cookie('session_token')
            return self.middleware.isLoggedIn(username, sessionToken)
        except Exception as e:
            return False


    def getLoginCheckFun(self):
        return self.checkAuthenticated