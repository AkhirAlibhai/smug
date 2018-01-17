import re
import os

import yaml

''' Various helper functions used by the bot '''

def static_vars(**kwargs):
    ''' Decorator for assigning static variables to a function '''
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate

def markdownCodeBlock(text: str, language: str=''):
    ''' formats text as a markdown code block '''
    return f'```{language}\n' + text + '```'

rollPattern = re.compile('([\d]+[d]{1}[\d]+)(\s*[+]\s*[\d]+[d]{1}[\d]+)*')
rollSplitPattern = re.compile('\s*\+\s*')

basePath = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(basePath, 'config.yaml'), 'r') as configFile:
    config = yaml.load(configFile)
