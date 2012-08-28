# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."

        friesland = orm.Province(name='Provincie Friesland')
        groningen = orm.Province(name='Provincie Groningen')
        drenthe = orm.Province(name='Provincie Drenthe')
        noordholland = orm.Province(name='Provincie Noord-Holland')
        overijssel = orm.Province(name='Provincie Overijssel')
        gelderland = orm.Province(name='Provincie Gelderland')
        utrecht = orm.Province(name='Provincie Utrecht')
        zuidholland = orm.Province(name='Provincie Zuid-Holland')
        zeeland = orm.Province(name='Provincie Zeeland')
        noordbrabant = orm.Province(name='Provincie Noord-Brabant')
        limburg = orm.Province(name='Provincie Limburg')
        flevoland = orm.Province(name='Provincie Flevoland')
        rijk = orm.Province(name='Rijk')

        for p in (friesland, groningen, drenthe, noordholland, overijssel,
                  gelderland, utrecht, zuidholland, zeeland, noordbrabant,
                  limburg, flevoland, rijk):
            p.save()

        options = {
            1: ('Wetterskip Fryslan', friesland),
            2: ('Waterschap Noorderzijlvest', drenthe),
            3: ("Waterschap Hunze en Aa's", drenthe),
            4: ('Waterschap Reest en Wieden', overijssel),
            5: ('Waterschap Velt en Vecht', overijssel),
            6: ('Waterschap Zuiderzeeland', flevoland),
            7: ('Waterschap Regge en Dinkel', overijssel),
            8: ('Waterschap Groot Salland', overijssel),
            9: ('Waterschap Veluwe', gelderland),
            10: ('Waterschap Rijn en IJssel', gelderland),
            11: ('HHRS Hollands Noorderkwartier', noordholland),
            12: ('Waterschap Vallei en Eem', utrecht),
            13: ('Waternet', utrecht),  # == Amstel, Gooi en Vecht
            14: ('HHRS van Rijnland', zuidholland),
            15: ('HHRS van Delfland', zuidholland),
            16: ('HHRS van Schieland en de Krimpenerwaard', zuidholland),
            17: ('HHRS De Stichtse Rijnlanden', utrecht),
            18: ('Waterschap Rivierenland', gelderland),
            19: ('Waterschap Hollandse Delta', zuidholland),
            20: ('Waterschap Scheldestromen', zeeland),
            21: ('Waterschap Brabantse Delta', noordbrabant),
            22: ('Waterschap De Dommel', noordbrabant),
            23: ('Waterschap Aa en Maas', noordbrabant),
            24: ('Waterschap Peel en Maasvallei', limburg),
            25: ('Waterschap Roer en Overmaas', limburg),
            26: ('RWS Waterdienst', rijk),
            27: ('Provincie Friesland', friesland),
            28: ('Provincie Groningen', groningen),
            29: ('Provincie Drenthe', drenthe),
            30: ('Provincie Noord-Holland', noordholland),
            31: ('Provincie Overijssel', overijssel),
            32: ('Provincie Gelderland', gelderland),
            33: ('Provincie Utrecht', utrecht),
            34: ('Provincie Zuid-Holland', zuidholland),
            35: ('Provincie Zeeland', zeeland),
            36: ('Provincie Noord-Brabant', noordbrabant),
            37: ('Provincie Limburg', limburg),
            38: ('Provincie Flevoland', flevoland),
            }

        for key, (name, owner) in options.items():
            orm.Owner(id=key, name=name, province=owner).save()

    def backwards(self, orm):
        "Write your backwards methods here."


    models = {
        'sharedproject.owner': {
            'Meta': {'object_name': 'Owner'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'province': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sharedproject.Province']"})
        },
        'sharedproject.province': {
            'Meta': {'object_name': 'Province'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['sharedproject']
