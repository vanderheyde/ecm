# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'OrderState'
        db.create_table('accounting_orderstate', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('stateID', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=10)),
        ))
        db.send_create_signal('accounting', ['OrderState'])

        # Adding model 'MarketOrder'
        db.create_table('accounting_marketorder', (
            ('orderID', self.gf('django.db.models.fields.PositiveIntegerField')(primary_key=True)),
            ('charID', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('stationID', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('volEntered', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('volRemaining', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('minVolume', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('orderState', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounting.OrderState'])),
            ('typeID', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('range', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('accountKey', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('duration', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('escrow', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('price', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('bid', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('issued', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal('accounting', ['MarketOrder'])


    def backwards(self, orm):
        
        # Deleting model 'OrderState'
        db.delete_table('accounting_orderstate')

        # Deleting model 'MarketOrder'
        db.delete_table('accounting_marketorder')


    models = {
        'accounting.contract': {
            'Meta': {'ordering': "['contractID']", 'object_name': 'Contract'},
            'acceptorID': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'assigneeID': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'availability': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'buyout': ('django.db.models.fields.FloatField', [], {}),
            'collateral': ('django.db.models.fields.FloatField', [], {}),
            'contractID': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'dateAccepted': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'dateCompleted': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'dateExpired': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'dateIssued': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'endStationID': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'forCorp': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'issuerCorpID': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'issuerID': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'numDays': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'price': ('django.db.models.fields.FloatField', [], {}),
            'reward': ('django.db.models.fields.FloatField', [], {}),
            'startStationID': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'volume': ('django.db.models.fields.FloatField', [], {})
        },
        'accounting.contractitem': {
            'Meta': {'ordering': "['recordID']", 'object_name': 'ContractItem'},
            'contract': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounting.Contract']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'included': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'quantity': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'rawQuantity': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'recordID': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'singleton': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'typeID': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'accounting.entrytype': {
            'Meta': {'object_name': 'EntryType'},
            'refTypeID': ('django.db.models.fields.PositiveIntegerField', [], {'primary_key': 'True'}),
            'refTypeName': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        'accounting.journalentry': {
            'Meta': {'object_name': 'JournalEntry'},
            'amount': ('django.db.models.fields.FloatField', [], {}),
            'argID1': ('django.db.models.fields.BigIntegerField', [], {}),
            'argName1': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'balance': ('django.db.models.fields.FloatField', [], {}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('ecm.lib.bigintpatch.BigAutoField', [], {'primary_key': 'True'}),
            'ownerID1': ('django.db.models.fields.BigIntegerField', [], {}),
            'ownerID2': ('django.db.models.fields.BigIntegerField', [], {}),
            'ownerName1': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'ownerName2': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'reason': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'refID': ('django.db.models.fields.BigIntegerField', [], {}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounting.EntryType']"}),
            'wallet': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['corp.Wallet']"})
        },
        'accounting.marketorder': {
            'Meta': {'ordering': "['orderID']", 'object_name': 'MarketOrder'},
            'accountKey': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'bid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'charID': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'duration': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'escrow': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'issued': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'minVolume': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'orderID': ('django.db.models.fields.PositiveIntegerField', [], {'primary_key': 'True'}),
            'orderState': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounting.OrderState']"}),
            'price': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'range': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'stationID': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'typeID': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'volEntered': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'volRemaining': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'accounting.orderstate': {
            'Meta': {'ordering': "['description']", 'object_name': 'OrderState'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'stateID': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'corp.wallet': {
            'Meta': {'ordering': "['walletID']", 'object_name': 'Wallet'},
            'accessLvl': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1000'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'walletID': ('django.db.models.fields.PositiveIntegerField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['accounting']
