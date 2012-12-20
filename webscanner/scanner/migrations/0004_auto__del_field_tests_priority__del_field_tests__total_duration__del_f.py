# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'Tests.priority'
        db.delete_column('scanner_tests', 'priority')

        # Deleting field 'Tests._total_duration'
        db.delete_column('scanner_tests', '_total_duration')

        # Deleting field 'Tests._status'
        db.delete_column('scanner_tests', '_status')

        # Adding index on 'Tests', fields ['is_deleted']
        db.create_index('scanner_tests', ['is_deleted'])

        # Adding index on 'Tests', fields ['user_ip']
        db.create_index('scanner_tests', ['user_ip'])


    def backwards(self, orm):
        
        # Removing index on 'Tests', fields ['user_ip']
        db.delete_index('scanner_tests', ['user_ip'])

        # Removing index on 'Tests', fields ['is_deleted']
        db.delete_index('scanner_tests', ['is_deleted'])

        # Adding field 'Tests.priority'
        db.add_column('scanner_tests', 'priority', self.gf('django.db.models.fields.IntegerField')(default=10), keep_default=False)

        # Adding field 'Tests._total_duration'
        db.add_column('scanner_tests', '_total_duration', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'Tests._status'
        db.add_column('scanner_tests', '_status', self.gf('django.db.models.fields.CharField')(default='not_started', max_length=16), keep_default=False)


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
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 12, 20, 15, 26, 58, 236098)'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 12, 20, 15, 26, 58, 235889)'}),
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
        'scanner.badword': {
            'Meta': {'object_name': 'BadWord'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'word': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'})
        },
        'scanner.commandqueue': {
            'Meta': {'object_name': 'CommandQueue'},
            'finish_date': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': '1', 'blank': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'run_date': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': '1', 'blank': '1'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '-3', 'db_index': 'True'}),
            'test': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'commands'", 'to': "orm['scanner.Tests']"}),
            'testname': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'wait_for_download': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'})
        },
        'scanner.results': {
            'Meta': {'object_name': 'Results'},
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'importance': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'output_desc': ('django.db.models.fields.CharField', [], {'max_length': '10000'}),
            'output_full': ('django.db.models.fields.TextField', [], {}),
            'status': ('django.db.models.fields.IntegerField', [], {}),
            'test': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'result'", 'to': "orm['scanner.Tests']"})
        },
        'scanner.tests': {
            'Meta': {'object_name': 'Tests'},
            'check_mail': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'check_performance': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'check_security': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'check_seo': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'download_path': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '300', 'null': '1', 'blank': '1'}),
            'download_status': ('django.db.models.fields.IntegerField', [], {'default': '-3', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '600', 'null': '1', 'blank': '1'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': '1'}),
            'user_ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'null': 'True', 'db_index': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'unique': 'True', 'max_length': '36', 'blank': 'True'})
        }
    }

    complete_apps = ['scanner']
