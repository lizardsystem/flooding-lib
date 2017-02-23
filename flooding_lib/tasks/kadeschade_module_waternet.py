# -*- coding: utf-8 -*-
import logging
import os
import datetime
import csv
from zipfile import ZipFile
import StringIO

from django import db
from osgeo import ogr, osr

from nens.sobek import HISFile

__revision__ = "$Rev: 1 $"[6:-2]

log = logging.getLogger('nens.lizard.kadebreuk.embankment_damage_waternet')


def set_broker_logging_handler(broker_handler=None):
    """
    """
    if broker_handler is not None:
        log.addHandler(broker_handler)
    else:
        log.warning("Broker logging handler does not set.")


class KadeSchadeBerekening:

    def __init__(self, scenario_id):

        self.scenario_id = scenario_id

        self.source_dir = None
        self.result_dir = None
        self.presentation_dir = None

        self.get_settings()

        self.his = None

    def get_settings(self):

        from flooding_base.models import Setting

        log.debug('read django and lizard settings')
        self.source_dir = Setting.objects.get(key='source_dir').value
        self.result_dir = Setting.objects.get(key='destination_dir').value
        self.presentation_dir = Setting.objects.get(key='presentation_dir').value

    def get_source_filenames(self, model):
        # source filenames
        shape_embankment = os.path.join(self.source_dir, model.embankment_damage_shape)

        source_path = os.path.dirname(shape_embankment)
        shape_buildings = os.path.join(source_path, 'bebouwing.shp')
        shape_arks = os.path.join(source_path, 'woonboten.shp')
        csv_damage = os.path.join(source_path, 'damage.csv')
        csv_damage_range = os.path.join(source_path, 'damage_range.csv')
        csv_bdm_type = os.path.join(source_path, 'bdm_type.csv')

        return shape_embankment, shape_buildings, shape_arks, csv_damage, csv_damage_range , csv_bdm_type

    def get_dest_filenames(self):

        log.debug('read scenario and file settings')
        # destination filenames
        dest_shape_embankment = os.path.join('flooding', 'scenario', str(self.scenario_id), 'oevers.shp')
        dest_shape_building = os.path.join(os.path.dirname(dest_shape_embankment), 'bebouwing.shp')
        dest_shape_arks = os.path.join(os.path.dirname(dest_shape_embankment), 'woonboten.shp')

        return dest_shape_embankment, dest_shape_building, dest_shape_arks

    def get_general_damage_settings(self, csv_damage, csv_damage_range, csv_bdm_invloedszones):

        # damage = {'onvhard': 500,  # for each m
        #           'verhard': 1000,  # for each m
        #           'huizen': 3000,  # for each m2
        #           'woonboot': 50000}  # each
        #
        # start_damage = {'zonder verdediging': 0.5,
        #                 'met beschoeiing': 0.5,
        #                 'stalen damwand': 0.5,
        #                 'stortsteen': 0.5,
        #                 'woonboot': 1.0,
        #                 'kleidijk': 3.0,
        #                 'veendijk': 2.5,
        #                 'zanddijk': 2.0,
        #                 'Klei': 3.0,
        #                 'Veen': 2.5,
        #                 'Zand': 2.0,
        #                 None: 0.5}
        #
        # full_damage = {'zonder verdediging': 1.0,
        #                'met beschoeiing': 1.0,
        #                'stalen damwand': 1.0,
        #                'stortsteen': 2.0,
        #                'woonboot': 1.0,
        #                'kleidijk': 3.0,
        #                'veendijk': 2.5,
        #                'zanddijk': 2.0,
        #                'Klei': 3.0,
        #                'Veen': 2.5,
        #                'Zand': 2.0,
        #                None: 1.0}

        log.debug('read damage settings {0}'.format(csv_damage))
        csvfile = open(csv_damage, 'rb')
        # check dialect. Dutch excel versions use ';' as delimiter
        dialect = csv.Sniffer().sniff(csvfile.read(1024), delimiters=";,")
        csvfile.seek(0)
        reader = csv.DictReader(csvfile, dialect=dialect)
        damage = {line['instelling']: int(line['waarde']) for line in reader}

        csvfile = open(csv_damage_range, 'rb')
        # check dialect. Dutch excel versions use ';' as delimiter
        dialect = csv.Sniffer().sniff(csvfile.read(1024), delimiters=";,")
        csvfile.seek(0)
        reader = csv.DictReader(csvfile, dialect=dialect)
        start_damage = {line['type']: float(line['start_daling_bezwijken']) for line in reader}

        csvfile.seek(0)
        reader = csv.DictReader(csvfile, dialect=dialect)
        full_damage = {line['type']: float(line['daling_volledig_bezweken']) for line in reader}

        csvfile = open(csv_bdm_invloedszones, 'rb')
        # check dialect. Dutch excel versions use ';' as delimiter
        dialect = csv.Sniffer().sniff(csvfile.read(1024), delimiters=";,")
        csvfile.seek(0)
        reader = csv.DictReader(csvfile, dialect=dialect)
        bdm_weg_criterium = {line['type']: float(line['weg_criterium']) for line in reader}

        csvfile.seek(0)
        reader = csv.DictReader(csvfile, dialect=dialect)
        bdm_invloedszone_bebouwing = {line['type']: float(line['invloedszone_bebouwing']) for line in reader}

        csvfile.seek(0)
        reader = csv.DictReader(csvfile, dialect=dialect)
        bdm_invloedszone_oude_bebouwing = {line['type']: float(line['invloedszone_oude_bebouwing']) for line in reader}

        return damage, start_damage, full_damage, bdm_weg_criterium, \
            bdm_invloedszone_bebouwing, bdm_invloedszone_oude_bebouwing

    def read_shapefile(self, shapefile_name, fields):

        log.debug('open shapefile  {0}'.format(shapefile_name))

        drv = ogr.GetDriverByName('ESRI Shapefile')
        source = drv.Open(str(shapefile_name))
        source_layer = source.GetLayer()

        indexes = {}

        if source_layer.GetFeatureCount() > 0:
            feature = source_layer.next()
            for key, field in fields.items():
                indexes[key] = feature.GetFieldIndex(field)
            source_layer.ResetReading()

        features = []

        for feature in source_layer:
            feat = {}
            feat['geom'] = feature.geometry().Clone()
            feat['fid'] = feature.GetFID()

            for key in fields.keys():
                feat[key] = feature.GetField(indexes[key])

            features.append(feat)

        return features, source_layer

    def write_to_shapefile(self, shapefile_name, data, fields, geom_type=ogr.wkbMultiPoint):


        log.debug('create shapefile {0}'.format(shapefile_name))

        drv = ogr.GetDriverByName('ESRI Shapefile')

        log.debug('check directory and create if needed')
        output_dir = os.path.dirname(shapefile_name)
        if not os.path.isdir(output_dir):
            log.debug('create output dir' + output_dir)
            os.makedirs(output_dir)
        elif os.path.isfile(shapefile_name):
            log.debug('shapefile already exist, delete shapefile.')
            os.remove(shapefile_name)
            os.remove(shapefile_name.replace('.shp', '.shx'))
            os.remove(shapefile_name.replace('.shp', '.dbf'))
            os.remove(shapefile_name.replace('.shp', '.prj'))

        log.debug('create shapefile')
        dest = drv.CreateDataSource(str(shapefile_name))
        dest_srs = osr.SpatialReference()
        dest_srs.ImportFromEPSG(28992)
        dest_layer = dest.CreateLayer(
            dest.GetName(), geom_type=geom_type, srs=dest_srs)

        for key, field_name, data_type in fields:
            dest_layer.CreateField(ogr.FieldDefn(field_name, data_type))

        for row in data:
            new_feat = ogr.Feature(dest_layer.GetLayerDefn())
            new_feat.SetFID(row['fid'])
            g = row['geom'].ExportToWkt()

            new_feat.SetGeometry(ogr.CreateGeometryFromWkt(g))
            for key, field_name, data_type in fields:
                new_feat.SetField(field_name, row[key])

            dest_layer.CreateFeature(new_feat)

        dest_layer.SyncToDisk()

        return dest_layer

    def get_daling(self, calc_id):

        try:
            daling = float(self.his.get_timeseries('c_' + calc_id, 'Waterlevel', None, None, list)[0][1] - \
                        min([value for date, value in
                        self.his.get_timeseries('c_' + calc_id, 'Waterlevel', None, None, list)]))
        except KeyError:
            log.info('no value for %s' % calc_id)
            daling = 0.

        return daling

    def get_perc_bezw(self, daling, start_damage, full_damage):
        if daling <= start_damage:
            return 0.0
        elif daling >= full_damage:
            return 100.0
        else:
            return 100 * (daling - start_damage) / (full_damage - start_damage)

    def read_settings_from_shapefiles(self, embankment_source_shape, building_source_shape, ark_source_shape):

        embankment_data, embankment_layer = self.read_shapefile(embankment_source_shape, {
            'id_oever': 'id_oever',  # int
            'id_calc': 'id_calc',  # str
            'len_type': 'len_type',  # float
            'len_totaal': 'len_totaal',  # float
            'weg_3meter': 'weg_3m_int',  # bool
            'weg_7meter': 'weg_7m_int',  # bool
            'type_besch': 'kade_type',  # str
            'bdm_type': 'bdm_type',  # str
            # 'bdm_type2': 'bdm_type2', #str
        })

        building_data, building_layer = self.read_shapefile(building_source_shape, {
            'id_pand': 'id_pand',  # int
            'id_oever': 'id_oever',  # int
            'id_calc': 'id_calc',  # str
            'afst_oever': 'afst_oever',
            'bouwjaar': 'bouwjaar',
            'max_schade': 'max_schade',
        })

        ark_data, ark_layer = self.read_shapefile(ark_source_shape, {
            'id_woonb': 'id_woonb',
            'id_calc': 'id_calc',
            'id_oever': 'id_oever',
        })

        return embankment_data, building_data, ark_data

    def calc_damage(self,
                    oever_data,
                    building_data,
                    ark_data,
                    damage,
                    start_damage,
                    full_damage,
                    bdm_type_weg_invloed,
                    bdm_type_build_zone,
                    bdm_type_build_zone_old):

        summary = {
            'sch_totaal': 0.0,
            'sch_bebouw': 0.0,
            'sch_woonb': 0.0,
            'sch_kade': 0.0
        }

        oever_result = []
        building_result = []
        ark_result = []

        old_criteria = damage['oud_gebouw_criterium']

        for oever in oever_data:

            # uitlezen peildaling uit hisfile
            oever['daling'] = self.get_daling(oever['id_calc'])

            # uitvoeren berekeningen
            oever['perc_bezw'] = self.get_perc_bezw(
                oever['daling'], start_damage[oever['type_besch']], full_damage[oever['type_besch']])

            # todo
            if ((bdm_type_weg_invloed.get(oever['bdm_type'], 3) == 3 and oever['weg_3meter'] == 1) or
                (bdm_type_weg_invloed.get(oever['bdm_type'], 3) != 3 and oever['weg_7meter'] == 1)):

                max_schade = damage['schade_meter_oever_met_weg'] * oever['len_type']
            else:
                max_schade = damage['schade_meter_oever_zonder_weg'] * oever['len_type']

            oever['sch_kade'] = int(oever['perc_bezw'] * max_schade / 100)
            
            oever['sch_bebouw'] = 0
            oever['sch_woonb'] = 0
            
        oever_dict = {oever['id_oever']: oever for oever in oever_data}


        for building in building_data:
            
            oever = oever_dict[building['id_oever']]
            
            if building['bouwjaar'] <= old_criteria:
                invloedszone = bdm_type_build_zone_old[oever['bdm_type']]
            else:
                invloedszone = bdm_type_build_zone[oever['bdm_type']]
            
            if oever['perc_bezw'] > 0.0001 and building['afst_oever'] < invloedszone:
                if building['max_schade'] is None:
                    building['max_schade'] = 0

                building['sch_bebouw'] = int(oever['perc_bezw'] * building['max_schade'] / 100)
                oever['sch_bebouw'] += building['sch_bebouw']
                building_result.append(building)
                
        for ark in ark_data:
            
            oever = oever_dict[ark['id_oever']]

            ark['perc_bezw'] = self.get_perc_bezw(
                oever['daling'], start_damage['woonboot'], full_damage['woonboot'])
            
            if ark['perc_bezw'] > 0.0001:
                ark['sch_woonb'] = int(ark['perc_bezw'] * damage['woonboot'] / 100)
                ark_result.append(ark)
            
                oever['sch_woonb'] += ark['sch_woonb']
                

        for oever in oever_data:

            oever['sch_totaal'] = oever['sch_kade'] + oever['sch_bebouw'] + oever['sch_woonb']

            if oever['sch_totaal'] > 1.0:
                oever['sch_per_m'] = int(oever['sch_totaal'] / oever['len_type'])
                oever_result.append(oever)

                summary['sch_totaal'] += oever['sch_totaal']
                summary['sch_kade'] += oever['sch_kade']
                summary['sch_bebouw'] += oever['sch_bebouw']
                summary['sch_woonb'] += oever['sch_woonb']

        return oever_result, building_result, ark_result, summary

    def write_results(self,
                      dest_shape_embankment, embankment_data,
                      dest_shape_building, building_data,
                      dest_shape_arks, ark_data):

        embankment_output_layer = self.write_to_shapefile(
            os.path.join(self.presentation_dir, dest_shape_embankment),
            embankment_data, [
                ('id_oever', 'id_oever', ogr.OFTString),
                ('id_calc', 'id_calc', ogr.OFTString),
                ('len_type', 'len_type', ogr.OFTInteger),
                ('len_totaal', 'len_totaal', ogr.OFTInteger),
                ('weg_3meter', 'weg_3m_int', ogr.OFTInteger),
                ('weg_7meter', 'weg_7m_int', ogr.OFTInteger),
                ('type_besch', 'kade_type', ogr.OFTString),
                ('bdm_type', 'bdm_type', ogr.OFTString),
                # ('bodem_type2', 'bdm_type2', ogr.OFTString),
                ('daling', 'daling', ogr.OFTReal),
                ('perc_bezw', 'perc_bezw', ogr.OFTInteger),
                ('sch_kade', 'sch_kade', ogr.OFTInteger),
                ('sch_bebouw', 'sch_bebow', ogr.OFTInteger),
                ('sch_woonb', 'sch_woonb', ogr.OFTInteger),
                ('sch_totaal', 'sch_totaal', ogr.OFTInteger),
                ('sch_per_m', 'sch_per_m', ogr.OFTReal),],
            ogr.wkbMultiLineString
        )

        building_output_layer = self.write_to_shapefile(
            os.path.join(self.presentation_dir, dest_shape_building),
            building_data, [
                ('id_pand', 'id_pand', ogr.OFTInteger),
                ('afst_oever', 'afst_oever', ogr.OFTReal),
                ('id_oever', 'id_oever', ogr.OFTInteger),
                ('id_calc', 'id_calc', ogr.OFTString),
                ('bouwjaar', 'bouwjaar', ogr.OFTInteger),
                ('max_schade', 'max_schade', ogr.OFTInteger),

                ('sch_bebouw', 'sch_bebow', ogr.OFTInteger)],
            ogr.wkbMultiPolygon
        )

        ark_output_layer = self.write_to_shapefile(
            os.path.join(self.presentation_dir, dest_shape_arks),
            ark_data, [
                ('id_woonb', 'id_woonb', ogr.OFTInteger),
                ('id_calc', 'id_calc', ogr.OFTString),
                ('id_oever', 'id_oever', ogr.OFTInteger),

                ('sch_woonb', 'sch_woonb', ogr.OFTInteger)],
            ogr.wkbMultiPoint
        )

        return embankment_output_layer, building_output_layer, ark_output_layer

    def run(self):

        from flooding_lib.models import Scenario, Result, ResultType, \
            SobekModel, Scenario_PresentationLayer

        from flooding_presentation.models import SourceLinkType, SourceLink, \
            PresentationSource, PresentationType, PresentationLayer, \
            PresentationShape

        scenario = Scenario.objects.get(pk=self.scenario_id)

        pt_embankment = PresentationType.objects.get(code='damage_embankments')
        pt_building = PresentationType.objects.get(code='damage_buildings')
        pt_ark = PresentationType.objects.get(code='damage_arks')

        try:
            # damage settings
            extwater_models = SobekModel.objects.filter(scenariobreach__scenario=scenario,
                                                        embankment_damage_shape__isnull=False)
            if extwater_models.count() == 0:
                log.info('no externalwatermodel or embankment_damage_shape for this scenario. Scenario skipped')
                return True, 'skipped 1 '
            else:
                model = extwater_models[0]

            result_waterlevel = Result.objects.filter(scenario=scenario, resulttype=13)

            if result_waterlevel.count() > 0:
                his_zip_name = os.path.join(self.result_dir, result_waterlevel[0].resultloc)
            else:
                log.warning('Not enough results for calculation of embankment damage. Scenario skipped')
                return True, 'skipped 2 '

        except Result.DoesNotExist:
            log.warning('Not enough results for calculation of embankment damage. Scenario skipped')
            return True, 'skipped 3 '

        # get filenames
        dest_shape_embankment, dest_shape_building, dest_shape_arks = self.get_dest_filenames()

        embankment_source_shape, building_source_shape, ark_source_shape, \
            damage_set_csv, damage_range_set_csv, csv_bdm_type = self.get_source_filenames(model)

        # read settings
        damage, start_damage, full_damage, bdm_weg_criterium, \
        bdm_invloedszone_bebouwing, bdm_invloedszone_oude_bebouwing = \
            self.get_general_damage_settings(damage_set_csv, damage_range_set_csv, csv_bdm_type)

        embankment_data, building_data, ark_data = self.read_settings_from_shapefiles(
                embankment_source_shape, building_source_shape, ark_source_shape)

        # openen hisfile
        log.debug('read hisfile')

        input_file = ZipFile(his_zip_name, "r")
        for filename in input_file.namelist():
            if filename.lower() == 'calcpnt.his':
                self.his = HISFile(StringIO.StringIO(input_file.read(filename)))
                break

        input_file.close()

        embankment_data, building_data, ark_data, \
            summary = self.calc_damage(embankment_data,
                                      building_data,
                                      ark_data,
                                      damage,
                                      start_damage,
                                      full_damage,
                                      bdm_weg_criterium,
                                      bdm_invloedszone_bebouwing,
                                      bdm_invloedszone_oude_bebouwing)

        # write results to shapefile
        embankment_output_layer, building_output_layer, ark_output_layer \
            = self.write_results(dest_shape_embankment, embankment_data,
                                 dest_shape_building, building_data,
                                 dest_shape_arks, ark_data)

        # embankment
        for presentationtype, value, name, dest_shape in [
            (pt_embankment, summary['sch_oever'], 'fl_emb_dam_', dest_shape_embankment),
            (pt_building, summary['sch_bebouw'], 'fl_emb_build_dam_', dest_shape_building),
            (pt_ark, summary['sch_woonb'], 'fl_emb_ark_dam_', dest_shape_arks)
            ]:

            # arks
            pl, pl_new = PresentationLayer.objects.get_or_create(
                presentationtype=presentationtype,
                scenario_presentationlayer__scenario=scenario,
                defaults={"value": value})
            if pl_new:
                Scenario_PresentationLayer.objects.create(scenario=scenario,
                                                          presentationlayer=pl)
            else:
                pl.value = value
                pl.save()

            link_type, _ = SourceLinkType.objects.get_or_create(
                name=name)
            source_link, new = SourceLink.objects.get_or_create(
                link_id=str(scenario.id), sourcelinktype=link_type,
                type=name + str(scenario.id))
            source, new = source_link.presentationsource.get_or_create(
                type=PresentationSource.SOURCE_TYPE_SHAPEFILE)

            relpath = os.path.realpath(dest_shape, self.presentation_dir)
            source.file_location = relpath
            source.t_original = datetime.datetime.fromtimestamp(
                os.stat(str(his_zip_name))[8])
            source.t_source = datetime.datetime.now()
            source.save()

            ps, ps_new = PresentationShape.objects.get_or_create(presentationlayer=pl)
            ps.geo_source = source
            ps.save()

        log.debug("Finish task.")
        log.debug("close db connection to avoid an idle process.")
        db.close_old_connections()
        return True, "ok "


def calc_damage(scenario_id):

    calc = KadeSchadeBerekening(scenario_id)
    return calc.run()
