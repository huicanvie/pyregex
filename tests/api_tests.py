import unittest
import webapp2
import urllib
from pyregex.webapp import application as app
import re
import json

def regex_params(regex, test_string, flags=0, match_type='match'):
    return dict(flags=flags, regex=regex, test_string=test_string, match_type=match_type)

def build_request(url, query_dict=None, *args, **kwargs):
    if query_dict:
        url = "%s?%s" % (url, urllib.urlencode(query_dict))
    return webapp2.Request.blank(url, *args, **kwargs)


class RegexHandlerTest(unittest.TestCase):
    def test_index(self):
        request = webapp2.Request.blank('/api/regex/')
        response = request.get_response(app)
        self.assertEqual(404, response.status_int)


    def test_regexTestFindall(self):
        params = regex_params(r'\w+', u'Hello, World!', 
            re.I | re.M, 'findall')
        request = build_request('/api/regex/test/', params)
        response = request.get_response(app)

        json_body = self.get_json_response(response)
        self.assertEqual('findall', json_body['result_type'])
        self.assertEqual(['Hello', 'World'], json_body['result'])


    def test_regexTestFindallNotAMatch(self):
        params = regex_params(r'\d+', u'Hello, World!', 
            re.I | re.M, 'findall')
        request = build_request('/api/regex/test/', params)
        response = request.get_response(app)

        json_body = self.get_json_response(response)
        self.assertEqual('findall', json_body['result_type'])
        self.assertEqual(None, json_body['result'])    


    def test_regexTestMatch(self):
        params = regex_params(
            r'\[(\d{4,}-\d{2,}-\d{2})\] Testing beginning on server (.+)$',
            u'[2013-07-23] Testing beginning on server example.com')

        expected = dict(
            group='[2013-07-23] Testing beginning on server example.com',
            groups=['2013-07-23', 'example.com'],
            group_dict={},
            end=52, start=0, pos=0,
            span=[0, 52],
            regs=[[0, 52], [1, 11], [41, 52]],
            last_group=None,
            last_index=2
        )

        request = build_request('/api/regex/test/', params)
        response = request.get_response(app)
        json_body = self.get_json_response(response)
        self.assertEqual('match', json_body['result_type'])
        self.assertEqual(expected, json_body['result'])

    def test_regexTestMatchNotAMatch(self):
        params = regex_params(
            r'\[(\d{4,}-\d{2,}-\d{2})\] Testing beginning on server (.+)$',
            u'Not Matching [2013-07-23] Testing beginning on server example.com')

        expected = None

        request = webapp2.Request.blank(
            '/api/regex/test/?%s' % urllib.urlencode(params))
        response = request.get_response(app)
        json_body = self.get_json_response(response)
        self.assertEqual('match', json_body['result_type'])
        self.assertEqual(expected, json_body['result'])


    def test_regexTestSearch(self):
        params = regex_params(
            r'^\[(\d{4,}-\d{2,}-\d{2})\] Testing beginning on server (.+)$',
            u'[2013-07-23] Testing beginning on server example.com',
            match_type='search')

        expected = dict(
            group='[2013-07-23] Testing beginning on server example.com',
            groups=['2013-07-23', 'example.com'],
            group_dict={},
            end=52, start=0, pos=0,
            span=[0, 52],
            regs=[[0, 52], [1, 11], [41, 52]],
            last_group=None,
            last_index=2
        )

        request = build_request('/api/regex/test/', params)
        response = request.get_response(app)
        json_body = self.get_json_response(response)
        self.assertEqual('search', json_body['result_type'])
        self.assertEqual(expected, json_body['result'])


    def test_regexTestInvalidRegex(self):
        params = regex_params('[Not balanced', '[Not balanced')

        request = build_request('/api/regex/test/', params)
        response = request.get_response(app)
        json_body = self.get_json_response(response, 400)
        self.assertEqual('error', json_body['result_type'])
        self.assertEqual('Invalid regular expression: %s' % params['regex'], json_body['message'])


    def test_regexTestUnknown(self):
        params = regex_params(r'\w+', 'Hello, World!',
                            re.I | re.M, 'not_really_sure_about_it')

        request = build_request('/api/regex/test/', params)
        response = request.get_response(app)

        json_body = self.get_json_response(response, 400)
        self.assertEqual('error', json_body['result_type'])
        expected = r'Invalid value for match_type: "not_really_sure_about_it"\. Acceptable values are .+$'
        self.assertRegexpMatches(json_body['message'], expected)

    def test_regexTestMultilineFindallNoFlags(self):
        params = regex_params(r"\w+\n\d+", "Hi 2013", match_type="findall")

        request = build_request('/api/regex/test/', params)
        response = request.get_response(app)
        json_body = self.get_json_response(response)
        self.assertEqual('findall', json_body['result_type'])
        self.assertIsNone(json_body['result'])

    def test_regexTestMultilineFindallWithFlags(self):
        regex = '\\w+\n\\.\n\\d+'
        params = regex_params(regex, "Hi\n.\n2013", match_type="findall", flags=re.X)

        request = build_request('/api/regex/test/', params)
        response = request.get_response(app)
        json_body = self.get_json_response(response)
        self.assertEqual('findall', json_body['result_type'])
        self.assertIsNone(json_body['result'])

        params.update(test_string="Hi.2013")
        request = build_request('/api/regex/test/', params)
        response = request.get_response(app)
        json_body = self.get_json_response(response)
        self.assertEqual('findall', json_body['result_type'])
        self.assertEqual(['Hi.2013'], json_body['result'])



    def get_json_response(self, response, *acceptable_statuses):
        if not acceptable_statuses:
            acceptable_statuses = [200]

        self.assertIn(response.status_int, acceptable_statuses)
        self.assertEqual('application/json', response.content_type)
        return json.loads(response.body)

