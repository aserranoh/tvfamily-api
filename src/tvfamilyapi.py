
'''tvfamilyapi.py - API with the tvfamily web service.

Copyright 2018 2019 Antonio Serrano Hernandez

tvfamily is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

tvfamily is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with tvfamily; see the file COPYING.  If not, see
<http://www.gnu.org/licenses/>.
'''

import io
import json
import os
import pycurl
import urllib.parse

__author__ = 'Antonio Serrano Hernandez'
__copyright__ = 'Copyright (C) 2018 2019 Antonio Serrano Hernandez'
__version__ = '0.1'
__license__ = 'GPL'
__maintainer__ = 'Antonio Serrano Hernandez'
__email__ = 'toni.serranoh@gmail.com'
__status__ = 'Development'
__homepage__ = 'https://github.com/aserranoh/tvfamily'


class ServiceError(Exception): pass

class Media(object):
    '''Represents a media to watch.'''

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __str__(self):
        try:
            return '{} {}x{:02}'.format(self.title, self.season, self.episode)
        except AttributeError:
            return self.title

class Title(object):
    '''Represents a title.'''

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        # Convert the seasons and episodes indexes to int
        try:
            seasons = self.seasons
            new_seasons = {}
            for sn, s in seasons.items():
                new_episodes = dict((int(en), e) for en, e in s.items())
                new_seasons[int(sn)] = new_episodes
            self.seasons = new_seasons
        except AttributeError: pass

class Server(object):
    '''Represents a tvfamily server.'''

    def __init__(self, address):
        self.address = address

    # Profile functions

    def get_profiles(self):
        '''Return the list of profiles.'''
        return self._api_function_get('getprofiles')['profiles']

    def get_profile_picture(self, name):
        '''Return an array of bytes that contains the profile picture
        (in png format).
        '''
        return self._api_function_get('getprofilepicture', name=name)

    def set_profile_picture(self, name, picture=None):
        '''Set a new picture for the given profile.'''
        self._api_function_post('setprofilepicture', picture, name=name)

    def create_profile(self, name, picture=None):
        '''Create a new profile with the given name.'''
        self._api_function_post('createprofile', picture, name=name)

    def delete_profile(self, name):
        '''Delete the profile with the given name.'''
        self._api_function_get('deleteprofile', name=name)

    # Categories functions

    def get_categories(self):
        '''Return the list of categories.'''
        return self._api_function_get('getcategories')['categories']

    # Medias functions

    def get_top(self, profile, category):
        '''Return the list of the top medias of a given category.'''
        response = self._api_function_get(
            'gettop', profile=profile, category=category)
        return [Media(**m) for m in response['top']]

    def get_media_status(self, title_id, season=None, episode=None):
        '''Retrieve the status of a media (downloaded, downloading, ...).'''
        if season is not None and episode is not None:
            kwargs = {'season': season, 'episode': episode}
        status = self._api_function_get('getmediastatus', **kwargs)['status']
        return MediaStatus(**status)

    # Title functions

    def get_title(self, title_id):
        '''Get title information.'''
        title = self._api_function_get('gettitle', id=title_id)['title']
        return Title(**title)

    # Generic API function

    def _api_function_get(self, function, **kwargs):
        '''Get some data from the server.'''
        buffer = io.BytesIO()
        c = pycurl.Curl()
        try:
            c.setopt(c.URL, '{}/api/{}?{}'.format(
                self.address, function, urllib.parse.urlencode(kwargs)))
            c.setopt(c.WRITEDATA, buffer)
            c.perform()
            c.close()
        except pycurl.error as e:
            raise ServiceError('connection error')
        body = buffer.getvalue()
        try:
            ret = json.loads(body.decode('utf-8'))
            if ret['code']:
                raise ServiceError(ret['error'])
        except ValueError:
            # No JSON data
            ret = body
        return ret

    def _api_function_post(self, function, file_=None, **kwargs):
        '''Send a file to the server.'''
        buffer = io.BytesIO()
        c = pycurl.Curl()
        try:
            c.setopt(c.URL, '{}/api/{}?{}'.format(
                self.address, function, urllib.parse.urlencode(kwargs)))
            if file_:
                file_ = (c.FORM_FILE, file_)
            else:
                file_ = (c.FORM_BUFFER, 'picture', c.FORM_BUFFERPTR, b'')
            c.setopt(c.HTTPPOST, [('file', file_)])
            c.setopt(c.WRITEDATA, buffer)
            c.perform()
            c.close()
        except pycurl.error as e:
            raise ServiceError('connection error')
        # Process the response
        body = buffer.getvalue()
        try:
            ret = json.loads(body.decode('utf-8'))
            if ret['code']:
                raise ServiceError(ret['error'])
        except ValueError:
            # No JSON data, protocol error
            raise ServiceError('protocol error, response is not JSON')

