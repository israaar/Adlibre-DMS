"""
Module: Metadata Template UI views helpers
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

from forms import DocumentIndexForm
from forms import DocumentSearchOptionsForm
from forms_representator import render_fields_from_docrules
from forms_representator import get_mdts_for_docrule

def initIndexesForm(request):
    """
    DocumentIndexForm/DocumentSearchForm initialization
    in case of GET returns an empty base form,
    in case of POST returns populated (from request) form instance.
    in both cases form is rendered with MDT index fields
    """
    details = None
    search = determine_search_req(request)
    try:
        # Trying to use cached MDT's and instantiating if none exist.
        details = request.session['mdts']
    except KeyError:
        # Getting MDT's from CouchDB
        try:
            try:
                details = get_mdts_for_docrule(request.session['docrule_id'])
            except KeyError:
                details = get_mdts_for_docrule(request.session['docrule'])
                search = True
            # Storing MDT's into improvised cashe
            request.session['mdts'] = details
        except KeyError:
            pass

    # Selecting proper form depending on request type
    if search:
        form = DocumentSearchOptionsForm()
    else:
        form = DocumentIndexForm()

    if details:
        if not details == 'error':
            # MDT's exist for ths docrule adding fields to form
            if search:
                fields = render_fields_from_docrules(details, request.POST or None, search=True)
            else:
                fields = render_fields_from_docrules(details, request.POST or None)
            if fields:
                form.setFields(fields)
    if request.POST:
        form.setData(request.POST)
        form.validation_ok()
    return form

def processDocumentIndexForm(request):
    """
    Handles document index form validation/population/data handling
    Works for search/indexing calls
    """
    form = initIndexesForm(request)
    secondary_indexes = {}
    search = determine_search_req(request)
    if form.validation_ok() or search:
        for key, field in form.fields.iteritems():
            # UPPERCASE Init if set attribute
            upper = False
            try:
                if field.is_uppercase:
                    upper = True
            except AttributeError:
                pass
            # FIXME: Nested exceptions.. bad
            try:
                # For dynamic form fields
                if not upper:
                    secondary_indexes[field.field_name] = form.data[unicode(key)]
                else:
                    secondary_indexes[field.field_name] = form.data[unicode(key)].upper()
            except (AttributeError, KeyError):
                try:
                    # For native form fields
                    if not upper:
                        secondary_indexes[key] = form.data[unicode(key)]
                    else:
                        secondary_indexes[key] = form.data[unicode(key)].upper()
                except KeyError:
                    pass

        if secondary_indexes:
            return secondary_indexes
        else:
            return None

def determine_search_req(request):
    """
    Helper to finds out if provided request is search or indexing (not search) one
    Returns Boolean search request
    Currently determining if search by the url
    Warning! (MUST BE CHANGED IF RENAMING SEARCH URL)
    """
    if 'search' in request.path:
        search = True
    else:
        search = False
    return search

def get_mdts_for_documents(documents):
    """
    Returns list of mdts for provided documents list
    """
    indexes = {}
    resp = None
    if documents:
        for document in documents:
            xes = document.mdt_indexes
            for ind in xes:
                indexes[ind] = ""
        resp = indexes.keys()
    return resp

def extract_secondary_keys_from_form(form):
    """
    Extracts secondary keys list from Indexes form.
    """
    keys_list = []
    for field_id, field in form.fields.iteritems():
        try:
            # if field is dynamic
            if field.field_name:
                if not field.__class__.__name__ == "DateField":
                    keys_list.append(field.field_name)
        except AttributeError:
            # standard field
            pass
    return keys_list

def cleanup_search_session(request):
    """
    Makes MDTUI forget abut searching keys entered before.
    """
    try:
        # search done. Cleaning up session for indexing to avoid collisions in functions
        request.session["document_search_dict"] = None
        request.session['docrule'] = None
        del request.session["document_search_dict"]
        del request.session['docrule']
    except KeyError:
        pass

def cleanup_indexing_session(request):
    """
    Makes MDTUI forget abut indexing keys entered before.
    """
    try:
        # Index done. Cleaning up session for future indexing to avoid collisions
        request.session["document_keys_dict"] = None
        request.session['docrule_id'] = None
        del request.session["document_keys_dict"]
        del request.session['docrule_id']
    except KeyError:
        pass

def cleanup_mdts(request):
    """
    Cleanup MDT's in improvised cache.
    """
    try:
        request.session['mdts'] = None
        del request.session['mdts']
    except KeyError:
        pass
