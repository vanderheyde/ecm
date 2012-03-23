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

__date__ = '2011 6 9'
__author__ = 'diabeteman'

from django.contrib import admin

from ecm.plugins.industry.models import (InventionPolicy,
                                         Job,
                                         Order,
                                         OrderLog,
                                         OrderRow,
                                         OwnedBlueprint,
                                         PriceHistory,
                                         SupplySource,
                                         Supply,
                                         CatalogEntry)

#------------------------------------------------------------------------------
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'originator',
        'manufacturer',
        'delivery_boy',
        'client',
        'delivery_location',
        'delivery_date',
        'state',
        'cost',
        'discount',
        'quote',
    ]
    search_fields = ['originator__username', 'client', 'manufacturer__username',
                     'delivery_boy__username', 'delivery_location']

#------------------------------------------------------------------------------
class OrderLogAdmin(admin.ModelAdmin):
    list_display = ['order', 'state', 'date', 'user', 'text' ]
    search_fields = ['user__username', 'text']

#------------------------------------------------------------------------------
class OrderRowAdmin(admin.ModelAdmin):
    list_display = ['catalog_entry', 'quantity', 'cost', 'order', ]
    search_fields = ['catalog_entry__typeName']

#------------------------------------------------------------------------------
class JobAdmin(admin.ModelAdmin):
    list_display = [
        'order',
        'row',
        'parent_job',
        'state',
        'owner',
        'item_id',
        'runs',
        'blueprint',
        'activity',
        'duration',
        'start_date',
        'end_date',
    ]
#------------------------------------------------------------------------------
class SupplySourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'location_id']

#------------------------------------------------------------------------------
class SupplyAdmin(admin.ModelAdmin):
    list_display = ['item_admin_display', 'price', 'auto_update', 'supply_source']

#------------------------------------------------------------------------------
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ['item_admin_display', 'price', 'date']

#------------------------------------------------------------------------------
class CatalogEntryAdmin(admin.ModelAdmin):
    list_display = [
        'typeName',
        'typeID',
        'production_cost',
        'public_price',
        'last_update',
        'fixed_price',
        'is_available',
    ]

#------------------------------------------------------------------------------
class OwnedBlueprintAdmin(admin.ModelAdmin):
    list_display = [
        'item_name_admin_display',
        'typeID',
        'me',
        'pe',
        'copy',
        'runs',
    ]
#------------------------------------------------------------------------------
class InventionPolicyAdmin(admin.ModelAdmin):
    list_display = [
        'item_group',
        'item_group_id',
        'invention_chance_admin_display',
        'target_me',
    ]

admin.site.register(Order, OrderAdmin)
admin.site.register(OrderLog, OrderLogAdmin)
admin.site.register(OrderRow, OrderRowAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(SupplySource, SupplySourceAdmin)
admin.site.register(Supply, SupplyAdmin)
admin.site.register(PriceHistory, PriceHistoryAdmin)
admin.site.register(CatalogEntry, CatalogEntryAdmin)
admin.site.register(OwnedBlueprint, OwnedBlueprintAdmin)
admin.site.register(InventionPolicy, InventionPolicyAdmin)
