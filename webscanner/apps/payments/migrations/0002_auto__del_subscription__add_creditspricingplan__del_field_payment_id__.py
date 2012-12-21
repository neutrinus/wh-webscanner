# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'Subscription'
        db.delete_table('payments_subscription')

        # Adding model 'CreditsPricingPlan'
        db.create_table('payments_creditspricingplan', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('price', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=2)),
            ('credits', self.gf('django.db.models.fields.IntegerField')()),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('payments', ['CreditsPricingPlan'])

        # Deleting field 'Payment.id'
        db.delete_column('payments_payment', 'id')

        # Deleting field 'Payment.subscription'
        db.delete_column('payments_payment', 'subscription_id')

        # Adding field 'Payment.code'
        db.add_column('payments_payment', 'code',
                      self.gf('django.db.models.fields.CharField')(default='0c076ae2cbf8422663da', max_length=512, primary_key=True),
                      keep_default=False)

        # Adding field 'Payment.user'
        db.add_column('payments_payment', 'user',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['auth.User']),
                      keep_default=False)

        # Adding field 'Payment.coupon'
        db.add_column('payments_payment', 'coupon',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['payments.Coupon'], null=True, blank=True),
                      keep_default=False)

        # Adding field 'Payment.credits'
        db.add_column('payments_payment', 'credits',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=1),
                      keep_default=False)

        # Adding field 'Payment.is_paid'
        db.add_column('payments_payment', 'is_paid',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Payment.date_paid'
        db.add_column('payments_payment', 'date_paid',
                      self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True),
                      keep_default=False)


        # Changing field 'Payment.date_created'
        db.alter_column('payments_payment', 'date_created', self.gf('django.db.models.fields.DateTimeField')())

    def backwards(self, orm):
        # Adding model 'Subscription'
        db.create_table('payments_subscription', (
            ('code', self.gf('django.db.models.fields.CharField')(default='88c4a6b214bc7e09c9d0', max_length=512, unique=True, primary_key=True)),
            ('date_eot', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True)),
            ('date_canceled', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True)),
            ('coupon', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['payments.Coupon'], null=True, blank=True)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('is_subscribed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('date_subscribed', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True)),
            ('price', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=2)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal('payments', ['Subscription'])

        # Deleting model 'CreditsPricingPlan'
        db.delete_table('payments_creditspricingplan')


        # User chose to not deal with backwards NULL issues for 'Payment.id'
        raise RuntimeError("Cannot reverse this migration. 'Payment.id' and its values cannot be restored.")

        # User chose to not deal with backwards NULL issues for 'Payment.subscription'
        raise RuntimeError("Cannot reverse this migration. 'Payment.subscription' and its values cannot be restored.")
        # Deleting field 'Payment.code'
        db.delete_column('payments_payment', 'code')

        # Deleting field 'Payment.user'
        db.delete_column('payments_payment', 'user_id')

        # Deleting field 'Payment.coupon'
        db.delete_column('payments_payment', 'coupon_id')

        # Deleting field 'Payment.credits'
        db.delete_column('payments_payment', 'credits')

        # Deleting field 'Payment.is_paid'
        db.delete_column('payments_payment', 'is_paid')

        # Deleting field 'Payment.date_paid'
        db.delete_column('payments_payment', 'date_paid')


        # Changing field 'Payment.date_created'
        db.alter_column('payments_payment', 'date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'payments.coupon': {
            'Meta': {'object_name': 'Coupon'},
            'code': ('django.db.models.fields.CharField', [], {'default': "'f7f054ee6e541662d53e'", 'unique': 'True', 'max_length': '256'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'percent': ('django.db.models.fields.IntegerField', [], {}),
            'used': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'used_date': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'})
        },
        'payments.creditspricingplan': {
            'Meta': {'object_name': 'CreditsPricingPlan'},
            'credits': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'price': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'})
        },
        'payments.payment': {
            'Meta': {'object_name': 'Payment'},
            'code': ('django.db.models.fields.CharField', [], {'default': "'c49793af7c12e4a2fad7'", 'max_length': '512', 'primary_key': 'True'}),
            'coupon': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['payments.Coupon']", 'null': 'True', 'blank': 'True'}),
            'credits': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
            'date_paid': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'is_paid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'price': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['payments']