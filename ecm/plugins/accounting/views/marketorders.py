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

__date__ = '2012 04 06'
__author__ = 'tash'


try:
    import json
except ImportError:
    # fallback for python 2.5
    import django.utils.simplejson as json

from django.db.models import Q
from django.http import HttpResponseBadRequest, HttpResponse
from django.shortcuts import render_to_response
from django.template.context import RequestContext as Ctx
from ecm.apps.eve.models import CelestialObject, Type
from ecm.apps.hr.models import Member
from ecm.plugins.accounting.models import MarketOrder, OrderState
from ecm.utils.format import print_float
from ecm.views import getScanDate, extract_datatable_params
from ecm.views.decorators import check_user_access
import logging



LOG = logging.getLogger(__name__)

#------------------------------------------------------------------------------
_range_map = {-1: 'Station',
             32767: 'Region'}

@check_user_access()
def marketorders(request):
    stateID = int(request.GET.get('stateID', -1))
    typeID = request.GET.get('typeID', 0)

    states = [{ 'stateID' :-1, 'name' : 'All', 'selected' : stateID == -1 }]
    for s in OrderState.objects.all().order_by('stateID'):
        states.append({
                'stateID' : s.stateID,
                'name' : s.description,
                'selected' : s.stateID == stateID})

    types = [{ 'typeID' : 0, 'name' : 'All', 'selected' : typeID == 0}]
    types.append({
    'typeID' : 1,
    'name'   : "Buy Order",
    'selected' : typeID == 1})
    types.append({
    'typeID' : 2,
    'name'   : "Sell Order",
    'selected' : typeID == 2})
    data = { 'states' : states,
             'types' : types,
             'scan_date' : getScanDate(MarketOrder)}
    return render_to_response('marketorders.html', data, Ctx(request))

@check_user_access()
def marketorders_data(request):
    try:
        params = extract_datatable_params(request)
        REQ = request.GET if request.method == 'GET' else request.POST
        params.stateID = int(REQ.get('stateID', -1))
        params.typeID = int(REQ.get('typeID', 0))
    except:
        return HttpResponseBadRequest()

    query = MarketOrder.objects.select_related(depth=1).all() # .order_by('-dateIssued')

    if params.search or params.stateID != -1 or params.typeID:
        # Total number of entries
        total_entries = query.count()
        search_args = Q()

        if params.search:
            search_args |= Q(title__icontains=params.search)
        if params.stateID > -1:
            state = OrderState.objects.get(stateID__exact=params.stateID)
            if state:
                search_args &= Q(orderState=state)
        if params.typeID == 1:
            search_args &= Q(bid=True)
        elif params.typeID == 2:
            search_args &= Q(bid=False)

        query = query.filter(search_args)
        filtered_entries = query.count()
    else:
        total_entries = filtered_entries = query.count()

    query = query[params.first_id:params.last_id]
    entries = []
    for entry in query:
        # Get the owner of the order
        try: owner = Member.objects.get(characterID=entry.charID).permalink
        except Member.DoesNotExist: owner = entry.charID
        entries.append([
            _map_type(entry.bid),
            #entry.charID,
            owner,
            Type.objects.get(typeID=entry.typeID).typeName,
            print_float(entry.price),
            entry.duration,
            CelestialObject.objects.get(itemID=entry.stationID).itemName,
            entry.volEntered,
            entry.volRemaining,
            entry.minVolume,
            entry.orderState.description,
            _map_range(entry.range) 
        ])
    json_data = {
        "sEcho" : params.sEcho,
        "iTotalRecords" : total_entries,
        "iTotalDisplayRecords" : filtered_entries,
        "aaData" : entries,
    }
    return HttpResponse(json.dumps(json_data))
def _map_type(bid):
    result = ""
    if bid:
        result = "Buy Order"
    else:
        result = "Sell Order"
    return result

def _map_range(order_range):
    return _range_map.get(int(order_range), '%d Jumps' % order_range)
