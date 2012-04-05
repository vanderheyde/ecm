# Copyright (c) 2010-2012 Robin Jarry
#
# This file is part of EVE Corporation Management.
#
# EVE Corporation Management is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# EVE Corporation Management is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# EVE Corporation Management. If not, see <http://www.gnu.org/licenses/>.

__date__ = '2012 04 01'
__author__ = 'tash'


try:
    import json
except ImportError:
    # fallback for python 2.5
    import django.utils.simplejson as json

from django.http import HttpResponseBadRequest, HttpResponse
from django.shortcuts import render_to_response
from django.template.context import RequestContext as Ctx
from django.db.models import Q

from ecm.core.utils import print_time_min, print_float
from ecm.apps.eve.models import Type
#from ecm.apps.eve import db
from ecm.apps.corp.models import Wallet, Corp
from ecm.apps.hr.models import Member
from ecm.views.decorators import check_user_access
from ecm.views import getScanDate, extract_datatable_params

from ecm.plugins.accounting.models import Contract 

#------------------------------------------------------------------------------
@check_user_access()
def contracts(request):

    # Get contract types
    data = {
        'scan_date' : getScanDate(Contract)        
    }
    return render_to_response('contracts.html', data, Ctx(request))

@check_user_access()
def contracts_data(request):
    try:
        params = extract_datatable_params(request)
        REQ = request.GET if request.method == 'GET' else request.POST
    except:
        return HttpResponseBadRequest()

    query = Contract.objects.select_related(depth=1).all() # .order_by('-dateIssued')
    
    if params.search:
        # Total number of entries
        total_entries = query.count()

        search_args = Q()

        if params.search:
            search_args |= Q(title__icontains=params.search)

        query = query.filter(search_args)
        # Total number of filtered entries #TODO 
        filtered_entries = query.count()
    else:
        total_entries = filtered_entries = query.count()

    query = query[params.first_id:params.last_id]
    entries = []

    for entry in query:
        entries.append([
            entry.type,
            entry.status,
            entry.title,
            print_time_min(entry.dateIssued),
            print_time_min(entry.dateExpired),
            print_time_min(entry.dateAccepted),
            print_time_min(entry.dateCompleted),
            print_float(entry.price),
            print_float(entry.reward),
            print_float(entry.collateral),
            print_float(entry.buyout),
            print_float(entry.volume),
        ])
    json_data = {
        "sEcho" : params.sEcho,
        "iTotalRecords" : total_entries,
        "iTotalDisplayRecords" : filtered_entries,
        "aaData" : entries
    }
    return HttpResponse(json.dumps(json_data))