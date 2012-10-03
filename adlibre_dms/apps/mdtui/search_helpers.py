"""
Module: SEARCH TYPE VARIATIONS GENERAL SEARCH HELPERS

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

import logging

from operator import itemgetter

from forms_representator import SEARCH_STRING_REPR

from parallel_keys import ParallelKeysManager
from mdt_manager import MetaDataTemplateManager
from dmscouch.models import CouchDocument
from adlibre.date_converter import date_standardized
from core.search import DMSSearchManager

log = logging.getLogger('dms.mdtui.views')

DATE_RANGE_CONSTANTS = {
    'min': unicode(date_standardized('1960-01-01')),
    'max': unicode(date_standardized('2100-01-01')),
    }

def search_documents(cleaned_document_keys, docrule_ids):
    """Main DMS MUI search logic processing method"""
    documents = []
    manager = DMSSearchManager()

    # Submitted form with all fields empty
    if cleaned_document_keys:
        keys = [key for key in cleaned_document_keys.iterkeys()]
        dd_range_keys = manager.document_date_range_present_in_keys(keys)
        keys_cnt = cleaned_document_keys.__len__()
        # Selecting appropriate search method
        if dd_range_keys and keys_cnt == 2:
            documents = manager.document_date_range_only_search(cleaned_document_keys, docrule_ids)
        else:
            documents = manager.document_date_range_with_keys_search(cleaned_document_keys, docrule_ids)
    if documents:
        documents = search_results_by_date(documents)

    # Not passing CouchDB search results object to template system to avoid bugs, in case it contains no documents
    if not documents:
        documents = []
    return documents

def cleanup_document_keys(document_keys):
    """
    Cleaning up key/value pairs that have empty values from CouchDB search request
    """
    del_list = []
    for key, value in document_keys.iteritems():
        if not value:
            del_list.append(key)
    for key in del_list:
        del document_keys[key]
    return document_keys

def ranges_validator(cleaned_document_keys):
    """
    Validates search keys for ranges.
    Adds range measures to single date keys
    """
    keys_list = [key for key in cleaned_document_keys.iterkeys()]
    for key in keys_list:
        # Secondary key START date provided. Checking if end period exists
        if key.endswith(SEARCH_STRING_REPR['field_label_from']):
            pure_key = key.rstrip(SEARCH_STRING_REPR['field_label_from'])
            desired_key = pure_key + SEARCH_STRING_REPR['field_label_to']
            if not desired_key in keys_list:
                cleaned_document_keys[desired_key] = DATE_RANGE_CONSTANTS['max']
                # Secondary key END date provided. Checking if start period exists
        if key.endswith(SEARCH_STRING_REPR['field_label_to']):
            pure_key = key.rstrip(SEARCH_STRING_REPR['field_label_to'])
            desired_key = pure_key + SEARCH_STRING_REPR['field_label_from']
            if not desired_key in keys_list:
                cleaned_document_keys[desired_key] = DATE_RANGE_CONSTANTS['min']
                # Indexing date MIN/MAX provided
        if u'date' in keys_list:
            if not u'end_date' in keys_list:
                cleaned_document_keys[u'end_date'] = DATE_RANGE_CONSTANTS['max']
        if u'end_date' in keys_list:
            if not u'date' in keys_list:
                cleaned_document_keys[u'date'] = DATE_RANGE_CONSTANTS['min']
    return cleaned_document_keys

def recognise_dates_in_search(cleaned_document_keys):
    """Finding ranges in cleaned keys and converting them to tuple pairs"""
    proceed = False
    keys_list = [key for key in cleaned_document_keys.iterkeys()]
    # TODO: implement this
    # Converting document date range to tuple for consistency
    #    if 'date' in keys_list and 'end_date' in keys_list:
    #        print 'Refactor! date range in search conversion'

    # Validating date fields (except main date field) exist in search query
    # Simple iterator to optimise calls without dates
    for key in keys_list:
        if key.endswith(SEARCH_STRING_REPR['field_label_from'] or SEARCH_STRING_REPR['field_label_to']):
            # we have to do this conversion
            proceed = True
    if proceed:
        # Validating if date fields are really date ranges
        for key in keys_list:
            if key.endswith(SEARCH_STRING_REPR['field_label_from']):
                # We have start of the dates sequence. Searching for an end key
                pure_key = key.rstrip(SEARCH_STRING_REPR['field_label_from'])
                desired_key = pure_key + SEARCH_STRING_REPR['field_label_to']
                if desired_key in keys_list:
                    # We have a date range. Constructing dates range tuple
                    from_value = cleaned_document_keys[key]
                    to_value = cleaned_document_keys[desired_key]
                    del cleaned_document_keys[key]
                    del cleaned_document_keys[desired_key]
                    cleaned_document_keys[pure_key]=(from_value, to_value)
    return cleaned_document_keys

def search_results_by_date(documents):
    """Sorts search results into list by CouchDB document's 'created date'."""
    newlist = sorted(documents, key=itemgetter('metadata_created_date'))
    return newlist

def check_for_secondary_keys_pairs(input_keys_list, docrule_id):
    """Checks for parallel keys pairs if they already exist in Secondary Keys.

    Scenario:
    Existing Parallell key:
        JOHN 1234
    user enters
        MIKE 1234
    where MIKE already exists in combination with another numeric id we should still issue a warning.
    EG. The combination of key values is new! (even though no new keys have been created)
    """
    # Copying dictionary data and operating with them in function
    sec_keys_list = {}
    suspicious_keys_list = {}
    if input_keys_list:
        for key in input_keys_list.iterkeys():
            sec_keys_list[key] = input_keys_list[key]
        suspicious_keys_list = {}
    p_keys_manager = ParallelKeysManager()
    mdt_manager = MetaDataTemplateManager()
    keys_list = [key for key in sec_keys_list.iterkeys()]
    # Cleaning from not secondary keys
    for key in keys_list:
        if key == 'date' or key == 'description':
            del sec_keys_list[key]
    # Getting list of parallel keys for this docrule.
    mdts = mdt_manager.get_mdts_for_docrule(docrule_id)
    pkeys = p_keys_manager.get_parallel_keys_for_mdts(mdts)
    # Getting Pkeys lists.
    checked_keys = []
    for key in sec_keys_list.iterkeys():
        key_pkeys = p_keys_manager.get_parallel_keys_for_key(pkeys, key)
        pkeys_with_values = p_keys_manager.get_parallel_keys_for_pkeys(key_pkeys, sec_keys_list)
        # Checking if this parallel keys group already was checked.
        if not pkeys_with_values in checked_keys:
            checked_keys.append(pkeys_with_values)
            # Getting all keys for parallel key to check if it exists in any document metadata already.
            for pkey, pvalue in pkeys_with_values:
                documents = CouchDocument.view('dmscouch/search_autocomplete',
                                                key=[docrule_id, pkey, pvalue],
                                                reduce=False)
                # Appending non existing keys into list to be checked.
                if not documents:
                    suspicious_keys_list[pkey] = pvalue
    if suspicious_keys_list:
        log.debug('Found new unique key/values in secondary keys: ', suspicious_keys_list)
    else:
        log.debug('Found NO new unique key/values in secondary keys')
    return suspicious_keys_list

def get_mdts_by_names(names_list):
    """
    Proxy for clean implementation

    Planned to be refactored out upon implementing something like search manager
    or uniting main system core with search logic.
    """
    manager = MetaDataTemplateManager()
    mdts = manager.get_mdts_by_name(names_list)
    return mdts
