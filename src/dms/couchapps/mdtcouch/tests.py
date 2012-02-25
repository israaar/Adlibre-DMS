"""
Module: Metadata Template UI Views
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

import json
from django.test import TestCase
from django.core.urlresolvers import reverse

# auth user
username = 'admin'
password = 'admin'

api = 'http://127.0.0.1:8000/api/mdt/'
template = {
    "docrule_id": "10000",
    "description": "<-- description of this metadata template -->",
    "fields": {
       "1": {
           "type": "integer",
           "field_name": "Employee ID",
           "description": "Unique (Staff) ID of the person associated with the document"
       },
       "2": {
           "type": "string",
           "length": 60,
           "field_name": "Employee Name",
           "description": "Name of the person associated with the document"
       },
    },
    "parallel": {
       "1": [ "1", "2"],
    }
}

class MetadataCouchDB(TestCase):
    def setUp(self):
        # We-re using only logged in client in this test
        self.client.login(username=username, password=password)

    def test_mdt_adding(self):
        """
        Posts Example MDT's to CouchDB through API
        Does test sending Metadata Template through API
        """
        mdt = json.dumps(template)
        url = reverse('api_mdt')
        response = self.client.post(url, {"mdt": mdt})
        self.assertEqual(response.status_code, 200)

    def test_mdt_adding_improper(self):
        """
        Posts WRONG MDT's to CouchDB through API
        Tests validation of added MDT
        """
        url = reverse('api_mdt')
        response = self.client.post(url, {"mdt": "some_string_for_testing"})
        self.assertEqual(response.status_code, 400)

    def test_mdt_adding_improper2(self):
        """
        Posts WRONG MDT's to CouchDB through API
        Tests validation of added MDT
        """
        url = reverse('api_mdt')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

    def test_mdt_adding_improper3(self):
        """
        Posts WRONG MDT's to CouchDB through API
        Tests validation of added MDT
        """
        url = reverse('api_mdt')
        template_wrong = template
        del template_wrong["docrule_id"]
        mdt = json.dumps(template_wrong)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

    def test_mdt_adding_improper4(self):
        """
        Posts WRONG MDT's to CouchDB through API
        Tests validation of added MDT
        """
        url = reverse('api_mdt')
        template_wrong = template
        del template_wrong["description"]
        mdt = json.dumps(template_wrong)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

    def test_mdt_adding_improper5(self):
        """
        Posts WRONG MDT's to CouchDB through API
        Tests validation of added MDT
        """
        url = reverse('api_mdt')
        template_wrong = template
        del template_wrong["fields"]
        mdt = json.dumps(template_wrong)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

    def test_mdt_adding_improper6(self):
        """
        Posts WRONG MDT's to CouchDB through API
        Tests validation of added MDT
        """
        url = reverse('api_mdt')
        template_wrong = template
        del template_wrong["parallel"]
        mdt = json.dumps(template_wrong)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

    def test_mdt_getting(self):
        """
        Fetches Example MDT's from CouchDB through API
        Tests: Proper test MDT received.
        """
        url = reverse('api_mdt')
        response = self.client.get(url, {"docrule_id": "10000"})
        self.assertContains(response, '"docrule_id": "10000"')
        self.assertContains(response, '"description": "Name of the person associated with the document"')
        self.assertEqual(response.status_code, 200)

    def test_mdt_getting_proper_format(self):
        """
        Testing Proper MDT format (hiding of CouchDB internal vars).
        """
        url = reverse('api_mdt')
        response = self.client.get(url, {"docrule_id": "10000"})
        self.assertContains(response, "mdt_id")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '"_id"')
        self.assertNotContains(response, '"_rev"')

    def test_mdt_getting_improper_call(self):
        """
        Tries to get not existing MDT from API
        """
        url = reverse('api_mdt')
        response = self.client.get(url, {"docrule_id": "10000000"})
        self.assertEqual(response.status_code, 404)

    def test_mdt_getting_improper_call2(self):
        """
        Tries to get something from MDT API without proper call
        """
        url = reverse('api_mdt')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_mdt_removing_wrong_id(self):
        """
        Testing wrond deletion calls
        """
        url = reverse('api_mdt')
        response = self.client.get(url, {"docrule_id": "10000000"})
        self.assertEqual(response.status_code, 404)

    def test_mdt_removing_improper_call(self):
        """
        Testing wrond deletion calls
        """
        url = reverse('api_mdt')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def _test_mdt_z_proper_removing(self):
        """
        Deleting all- test MDT's (with doccode 10000).

        NOTE: NAme of test should be in the end not to fail other tests...
        """
        url = reverse('api_mdt')
        response = self.client.get(url, {"docrule_id": "10000"})
        data = json.loads(str(response.content))
        for key, value in data.iteritems():
            mdt_id =  data[key]["mdt_id"]
            response = self.client.delete(url, {"mdt_id": mdt_id})
            self.assertEqual(response.status_code, 204)

class MetadataTemplateExternalUser(TestCase):

    def test_mdt_remove_not_logged_in(self):
        """
        Deleting all- test MDT's (with doccode 10000).

        NOTE: NAme of test should be in the end not to fail other tests...
        """
        url = reverse('api_mdt')
        response = self.client.get(url, {"docrule_id": "10000"})
        self.assertEqual(response.status_code, 401)

    def test_mdt_getting_not_logged_in(self):
        """
        Fetches Example MDT's from CouchDB through API
        Tests: Proper test MDT received.
        """
        url = reverse('api_mdt')
        response = self.client.get(url, {"docrule_id": "10000"})
        self.assertEqual(response.status_code, 401)

    def test_mdt_adding_not_logged_in(self):
        """
        Posts Example MDT's to CouchDB through API
        Does test sending Metadata Template through API
        """
        mdt = json.dumps(template)
        url = reverse('api_mdt')
        response = self.client.post(url, {"mdt": mdt})
        self.assertEqual(response.status_code, 401)