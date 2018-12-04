
'''tvfamilyapi.py - API with the tvfamily web service.

Copyright 2018 Antonio Serrano Hernandez

This file is part of tvfamily.

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

import os
import requests

__author__ = 'Antonio Serrano Hernandez'
__copyright__ = 'Copyright (C) 2018 Antonio Serrano Hernandez'
__version__ = '0.1'
__license__ = 'GPL'
__maintainer__ = 'Antonio Serrano Hernandez'
__email__ = 'toni.serranoh@gmail.com'
__status__ = 'Development'
__homepage__ = 'https://github.com/aserranoh/tvfamily'


class ServiceError(Exception):
    pass

class Media(object):
    '''Represents a media to watch.'''

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def fromdict(cls, d):
        '''Build a media from a dictionary.'''
        return cls(**d)

    def __str__(self):
        '''Return a string representation of this media.'''
        try:
            return '{} {}x{:02}'.format(self.title, self.season, self.episode)
        except AttributeError:
            return self.title

class Server(object):
    '''Represents a tvfamily server.'''

    def __init__(self, address):
        self.address = address

    # Profile functions

    def get_profiles(self):
        '''Return the list of profiles.'''
        return self._api_function('getprofiles')['profiles']

    def get_profile_picture(self, name):
        '''Return an array of bytes that contains the profile picture
        (in png format).
        '''
        return self._api_function('getprofilepicture', name=name)

    def set_profile_picture(self, name, path=''):
        '''Set a new picture for the given profile.'''
        url = '{}/api/setprofilepicture'.format(self.address)
        params = {'name': name}
        try:
            if path:
                with open(path, 'rb') as data:
                    r = requests.post(url, params=params, files={'file': data})
            else:
                r = requests.post(url, params=params, files={'file': b''})
        except requests.exceptions.ConnectionError:
            raise ServiceError('connection error')
        # Process the response
        try:
            ret = r.json()
            if ret['code']:
                raise ServiceError(ret['error'])
        except ValueError:
            # No JSON data, protocol error
            raise ServiceError('protocol error, response is not JSON')

    def create_profile(self, name):
        '''Create a new profile with the given name.'''
        self._api_function('createprofile', name=name)

    def delete_profile(self, name):
        '''Delete the profile with the given name.'''
        self._api_function('deleteprofile', name=name)

    # Categories functions

    def get_categories(self):
        return self._api_function('getcategories')['categories']

    # Medias functions

    def get_top(self, category):
        '''List the top medias of a given category.'''
        d, r = self._api_function('gettop', category=category)
        return [Media.fromdict(m) for m in d['top']]

    # Generic API function

    def _api_function(self, function, **kwargs):
        url = '{}/api/{}'.format(self.address, function)
        try:
            r = requests.get(url, params=kwargs)
        except requests.exceptions.ConnectionError:
            raise ServiceError('connection error')
        try:
            ret = r.json()
            if ret['code']:
                raise ServiceError(ret['error'])
        except ValueError:
            # No JSON data
            ret = r.content
        return ret

