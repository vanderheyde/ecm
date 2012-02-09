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

from __future__ import with_statement

__date__ = "2011 8 17"
__author__ = "diabeteman"

from django.db import models, connection
from django.contrib.auth.models import User

from ecm.core import utils
from ecm.core.eve import db
from ecm.core.utils import fix_mysql_quotes
from ecm.plugins.industry.models.catalog import CatalogEntry
from ecm.plugins.industry.models.inventory import Supply
from ecm.plugins.industry.models.job import Job

#------------------------------------------------------------------------------
class Order(models.Model):
    """
    An order submitted by a User or the application.
    each order must follow the same life cycle specified by the VALID_TRANSITIONS hash table.
    An order can contain multiple rows (one for each different item)
    """

    class Meta:
        ordering = ['id']
        get_latest_by = 'id'
        app_label = 'industry'

    # states
    DRAFT = 0
    PENDING = 1
    PROBLEMATIC = 2
    ACCEPTED = 3
    PLANNED = 4
    IN_PREPARATION = 5
    READY = 6
    DELIVERED = 7
    PAID = 8
    CANCELED = 9
    REJECTED = 10

    # states text
    STATES = {
        DRAFT:             'Draft',
        PENDING:           'Pending',
        PROBLEMATIC:       'Problematic',
        ACCEPTED:          'Accepted',
        PLANNED:           'Planned',
        IN_PREPARATION:    'In Preparation',
        READY:             'Ready',
        DELIVERED:         'Delivered',
        PAID:              'Paid',
        CANCELED:          'Canceled by Client',
        REJECTED:          'Rejected by Manufacturer',
    }

    state = models.PositiveIntegerField(default=DRAFT, choices=STATES.items())
    originator = models.ForeignKey(User, related_name='orders_created')
    manufacturer = models.ForeignKey(User, null=True, blank=True, related_name='orders_manufactured')
    delivery_boy = models.ForeignKey(User, null=True, blank=True, related_name='orders_delivered')
    client = models.CharField(max_length=255, null=True, blank=True)
    delivery_location = models.CharField(max_length=255, null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True)
    cost = models.FloatField(default=0.0)
    quote = models.FloatField(default=0.0)
    discount = models.FloatField(default=0.0)

    def last_modified(self):
        try:
            return self.logs.latest().date
        except OrderLog.DoesNotExist:
            return None

    def creation_date(self):
        try:
            return self.logs.all()[0].date
        except IndexError:
            return None


    #############################
    # TRANSISTIONS

    def add_comment(self, user, comment):
        self.logs.create(state=self.state, user=user, text=unicode(comment))

    def apply_transition(self, function, state, user, comment):
        """
        Modify the state of an order. Adding a comment in the order logs.

        Checks if the new state is allowed in the life cycle. If not, raises an IllegalStateError
        """
        self.check_can_pass_transition(function.__name__)
        self.state = state
        self.add_comment(user, comment)

    def modify(self, entries):
        """
        Modification of the order.
        An order can only be modified if its state is DRAFT or PENDING.

        entries must be a list of tuples such as :
        [(CatalogEntry_A, qty_A), (CatalogEntry_B, qty_B), (CatalogEntry_C, qty_C)]
        """
        if self.rows.all() or self.logs.all():
            comment = "Modified by originator."
        else:
            comment = "Created."
        self.apply_transition(Order.modify, Order.DRAFT, self.originator, comment)
        self.rows.all().delete()
        
        self.cost = 0.0
        self.quote = 0.0
        missingPrice = False
        for catalog_entry, quantity in entries:
            self.rows.create(catalog_entry=catalog_entry, quantity=quantity)
            if catalog_entry.production_cost is not None:
                if catalog_entry.fixed_price is not None:
                    self.quote += catalog_entry.fixed_price
                else:
                    self.quote += catalog_entry.production_cost * (1 + self.pricing.margin)
                self.cost += catalog_entry.production_cost
            else:
                missingPrice = True
        if missingPrice:
            self.cost = 0.0
            self.quote = 0.0
        self.save()

    def confirm(self):
        """
        Originator's confirmation of the order. Warns the manufacturing team.
        """
        self.apply_transition(Order.confirm, Order.PENDING, self.originator, "Confirmed by originator.")
        self.save()
        # TODO: handle the alerts to the manufacturing team

    def accept(self, manufacturer):
        """
        Acceptation by a manufacturer.
        The order cannot be modified by its originator after acceptation.

        During the "accept" transition, we check if the order can be fulfilled.
        If it can, its states changes to ACCEPTED. If not, the order changes to PROBLEMATIC.
        """
        try:
            self.check_feasibility()
            missingPrices = self.create_jobs()
            if missingPrices: # FIXME moche moche moche
                raise OrderCannotBeFulfilled('Missing prices for items %s' % list(missingPrices))
            self.apply_transition(Order.accept, Order.ACCEPTED, user=manufacturer, comment="Accepted")
            self.save()
            return True
        except OrderCannotBeFulfilled, err:
            self.apply_transition(Order.accept, Order.PROBLEMATIC, user=manufacturer, comment=str(err))
            self.save()
            return False

    def resolve(self, manufacturer, comment):
        """
        Resolution of a problematic order.

        This is a manual operation and entering a comment is mandatory to explain
        why the order was accepted despite the fact that is was PROBLEMATIC
        """
        self.create_jobs()
        self.apply_transition(Order.resolve, Order.ACCEPTED, manufacturer, comment)
        self.save()

    def plan(self, manufacturer, date):
        """
        Plan an order for a delivery date
        """
        self.apply_transition(Order.plan, Order.PLANNED, manufacturer,
                             'Order planned for date "%s"' % utils.print_date(date))
        self.delivery_date = date
        self.save()

    def reject(self, manufacturer, comment):
        """
        Rejection of an order by a manufacturer.

        This is a manual operation and entering a comment is mandatory to explain
        why the order was rejected.
        """
        self.apply_transition(Order.reject, Order.REJECTED, manufacturer, comment)
        self.save()
        # TODO: handle the alerts to the client

    def cancel(self, comment):
        """
        Cancellation of the order by its originator.
        """
        self.apply_transition(Order.cancel, Order.CANCELED, self.originator, comment)
        self.save()
        # TODO: handle the alerts to the manufacturing team

    def start_preparation(self, user=None):
        """
        Order preparation started (first job is started)
        """
        self.apply_transition(Order.start_preparation, Order.IN_PREPARATION,
                             user or self.manufacturer, "Preparation started.")
        self.save()

    def end_preparation(self, manufacturer=None, delivery_boy=None):
        """
        Order is ready (all jobs are ready)

        Delivery task is assigned to manufacturer by default, unless delivery_boy is not None.
        """
        self.apply_transition(Order.end_preparation, Order.READY,
                             manufacturer, "Order is ready.")
        self.delivery_boy = delivery_boy or manufacturer or self.manufacturer

        self.save()

    def deliver(self, user=None):
        """
        Order has been delivered.
        """
        self.apply_transition(Order.deliver, Order.DELIVERED,
                             user or self.delivery_boy,
                             "Order has been delivered to the client.")
        self.save()
        # TODO: handle the alerts to the client

    def pay(self, user=None):
        """
        Order has been paid.
        """
        self.apply_transition(Order.pay, Order.PAID,
                             user or self.delivery_boy, "Order has been delivered to the client.")
        self.save()

    # allowed transitions between states
    VALID_TRANSITIONS = {
        DRAFT : (modify, confirm, cancel),
        PENDING : (modify, accept, cancel, reject),
        PROBLEMATIC : (modify, resolve, cancel, reject),
        ACCEPTED : (plan, start_preparation, cancel),
        PLANNED : (start_preparation, cancel),
        IN_PREPARATION : (end_preparation, cancel),
        READY : (deliver, cancel),
        DELIVERED : (pay, cancel),
        PAID : (),
        CANCELED : (),
        REJECTED : (),
    }

    modify.text = 'Modify order'
    confirm.text = 'Confirm order'
    accept.text = 'Accept order'
    resolve.text = 'Resolve order'
    plan.text = 'Plan order'
    reject.text = 'Reject order'
    cancel.text = 'Cancel order'
    start_preparation.text = 'Start preparation'
    end_preparation.text = 'End preparation'
    deliver.text = 'Deliver order'
    pay.text = 'Pay order'

    modify.customerAccess = True
    confirm.customerAccess = True
    accept.customerAccess = False
    resolve.customerAccess = False
    plan.customerAccess = False
    reject.customerAccess = False
    cancel.customerAccess = True
    start_preparation.customerAccess = False
    end_preparation.customerAccess = False
    deliver.customerAccess = False
    pay.customerAccess = True


    def get_valid_transitions(self, customer=False):
        if customer:
            return [ tr for tr in Order.VALID_TRANSITIONS[self.state] if tr.customerAccess ]
        else:
            return Order.VALID_TRANSITIONS[self.state]

    def check_can_pass_transition(self, transitionName):
        validTransitionNames = [ t.__name__ for t in Order.VALID_TRANSITIONS[self.state] ]
        if transitionName not in validTransitionNames:
            raise IllegalTransition('Cannot apply transition "%s" from state "%s".' %
                                    (transitionName, Order.STATES[self.state]))

    ################################
    # UTILITY FUNCTIONS

    def check_feasibility(self):
        """
        Checks if the order can be fulfilled.

        1/ All the blueprints involved by the jobs generated by this order are owned by the corp
        2/ ...

        If cannot be fulfilled, raise OrderCannotBeFulfilled exception which contains
        the list of missing blueprints.
        """
        missing_blueprints = set()
        for row in self.rows.all():
            missing_blueprints.update(row.catalog_entry.missing_blueprints())
        
        if missing_blueprints:
            raise OrderCannotBeFulfilled(missing_blueprints=missing_blueprints)

    def create_jobs(self):
        """
        Create all jobs needed to complete this order.
        Calculating costs for all the order's rows.

        If dry_run is True, only the prices are written, and any job creation is rollbacked.
        """
        prices = {}
        for sp in Supply.objects.all():
            prices[sp.typeID] = sp.price
        missingPrices = set([])
        self.cost = 0.0
        self.quote = 0.0
        for row in self.rows.all():
            row.cost, missPrices = row.create_jobs(prices=prices)
            missingPrices.update(missPrices)
            self.cost += row.cost
            self.quote += row.quote
            row.save()
        self.save()
        return missingPrices
            


    def get_aggregated_jobs(self, activity=None):
        """
        Retrieve a list of all the jobs related to this order aggregated by itemID.

        The job activity can be filtered to display only SUPPLY jobs
        """
        where = [ '"order_id" = %s' ]
        if activity is not None:
            where.append('"activity" = %s')
        sql = 'SELECT "itemID", SUM("runs"), "activity" FROM "industry_job"'
        sql += ' WHERE ' + ' AND '.join(where)
        sql += ' GROUP BY "itemID", "activity" ORDER BY "activity", "itemID";'
        sql = fix_mysql_quotes(sql)

        cursor = connection.cursor() #@UndefinedVariable
        if activity is not None:
            cursor.execute(sql, [self.id, activity])
        else:
            cursor.execute(sql, [self.id])

        jobs = []
        for i, r, a in cursor:
            jobs.append(Job(itemID=i, runs=r, activity=a))
        cursor.close()

        return jobs

    def repr_as_tree(self):
        output = ''
        for r in self.rows.all():
            for j in r.jobs.filter(parentJob=None):
                output += j.repr_as_tree()
        return output

    def url(self):
        return '/industry/orders/%d/' % self.id

    def shop_url(self):
        return '/shop/orders/%d/' % self.id

    def permalink(self, shop=True):
        if shop:
            url = self.shop_url()
        else:
            url = self.url()
        return '<a href="%s" class="order">Order &#35;%d</a>' % (url, self.id)

    def originator_permalink(self):
        if self.originator is not None:
            url = '/hr/player/%d/' % self.originator.id
            return '<a href="%s" class="player">%s</a>' % (url, self.originator.username)
        else:
            return '(none)'

    def manufacturer_permalink(self):
        if self.manufacturer is not None:
            url = '/hr/player/%d/' % self.manufacturer.id
            return '<a href="%s" class="player">%s</a>' % (url, self.manufacturer.username)
        else:
            return '(none)'

    def delivery_boy_permalink(self):
        if self.delivery_boy is not None:
            url = '/hr/player/%d/' % self.delivery_boy.id
            return '<a href="%s" class="player">%s</a>' % (url, self.delivery_boy.username)
        else:
            return '(none)'

    def state_text(self):
        return Order.STATES[self.state]

    def __unicode__(self):
        return u'Order #%d from %s [%s]' % (self.id, str(self.originator), Order.STATES[self.state])

    def __repr__(self):
        return unicode(self) + '\n  ' + '\n  '.join(map(unicode, list(self.rows.all())))




#------------------------------------------------------------------------------
class OrderLog(models.Model):

    class Meta:
        app_label = 'industry'
        get_latest_by = 'id'
        ordering = ['order', 'date']

    order = models.ForeignKey(Order, related_name='logs')
    state = models.PositiveSmallIntegerField(choices=Order.STATES.items())
    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, related_name='logs')
    text = models.TextField()

    def user_permalink(self):
        try:
            url = '/player/%d/' % self.user.id
            return '<a href="%s" class="player">%s</a>' % (url, self.user.username)
        except:
            return '(None)'

    def state_text(self):
        try:
            return Order.STATES[self.state]
        except KeyError:
            return str(self.state)

    def __unicode__(self):
        return u'%s: [%s] (%s) %s' % (self.date, self.state_text, self.user, self.text)


#------------------------------------------------------------------------------
class OrderRow(models.Model):

    class Meta:
        app_label = 'industry'
        ordering = ['order']

    order = models.ForeignKey(Order, related_name='rows')
    catalog_entry = models.ForeignKey(CatalogEntry, related_name='order_rows')
    quantity = models.PositiveIntegerField()
    cost = models.FloatField(default=0.0)


    def get_aggregated_jobs(self, activity=None):
        """
        Retrieve a list of all the jobs related to this OrderRow aggregated by itemID.

        The job activity can be filtered to display only SUPPLY jobs
        """
        where = [ '"row_id" = %s' ]
        if activity is not None:
            where.append('"activity" = %d' % activity)
        sql = 'SELECT "itemID", SUM("runs"), "activity" FROM "industry_job"'
        sql += ' WHERE ' + ' AND '.join(where)
        sql += ' GROUP BY "itemID", "activity" ORDER BY "activity", "itemID";'
        sql = fix_mysql_quotes(sql)

        cursor = connection.cursor() #@UndefinedVariable
        cursor.execute(sql, [self.id])

        jobs = []
        for i, r, a in cursor:
            jobs.append(Job(itemID=i, runs=r, activity=a))
        cursor.close()

        return jobs


    def create_jobs(self, prices=None):
        job = Job.create(self.catalog_entry_id, self.quantity, order=self.order, row=self)
        job.create_requirements()
        cost, missingPrices = self.calculate_cost(prices)
        return cost, missingPrices


    def calculate_cost(self, prices=None):
        if prices is None:
            prices = {}
            for sp in Supply.objects.all():
                prices[sp.typeID] = sp.price
        cost = 0.0
        missingPrices = set([])
        for job in self.get_aggregated_jobs(Job.SUPPLY):
            try:
                cost += prices[job.itemID] * round(job.runs)
            except KeyError:
                missingPrices.add(job.itemID)
        return cost, missingPrices


    def __unicode__(self):
        return '%s x%d : %f' % (self.catalog_entry.typeName, self.quantity, self.cost)



#------------------------------------------------------------------------------
class OrderCannotBeFulfilled(UserWarning):

    def __init__(self, missing_blueprints=None, missing_prices=None):
        self.missing_blueprints = missing_blueprints
        self.missing_prices = missing_prices

    def __str__(self):
        if self.missing_blueprints:
            if all([ type(p) == type(0) for p in self.missing_blueprints ]):
                self.missing_blueprints = [ db.resolveTypeName(p)[0] for p in self.missing_blueprints ]
            output = 'Missing Blueprints: '
            output += ', '.join(map(str, self.missing_blueprints))
        elif self.missing_prices:
            if all([ type(p) == type(0) for p in self.missing_prices ]):
                self.missing_prices = [ db.resolveTypeName(p)[0] for p in self.missing_prices ]
            output = 'Missing SupplyPrices: '
            output += ', '.join(map(str, self.missing_prices))
        return output

#------------------------------------------------------------------------------
class IllegalTransition(UserWarning): pass

