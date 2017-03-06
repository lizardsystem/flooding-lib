import os.path
import StringIO
import tempfile
from unittest import TestCase
from zipfile import ZipFile

from nens.sobek import HISFile

from flooding_lib.tasks.kadeschade_module_waternet import KadeSchadeBerekening


class KadeSchadeMod(KadeSchadeBerekening):
    def get_settings(self):
        test_dir = os.path.join(os.path.dirname(__file__), 'data')
        temp_dir = tempfile.gettempdir()

        self.source_dir = os.path.join(test_dir, 'full')
        self.result_dir = test_dir
        self.presentation_dir = os.path.join(temp_dir, 'presentation')


class TestModel:
    embankment_damage_shape = 'oevers.shp'


class TestKadeSchadeWaternet(TestCase):

    def test_read_settings(self):

        kds = KadeSchadeMod(scenario_id=1)
        test_dir = os.path.join(os.path.dirname(__file__), 'data', 'full')

        # 1. location of settings
        embankment_source_shape, building_source_shape, ark_source_shape, \
            damage_set_csv, damage_range_set_csv, csv_bdm_type = kds.get_source_filenames(TestModel())

        self.assertEqual(os.path.dirname(embankment_source_shape), test_dir)

        # 2. reading settings from csv files
        damage, start_damage, full_damage, bdm_weg_criterium, \
            bdm_invloedszone_bebouwing, bdm_invloedszone_oude_bebouwing = \
                kds.get_general_damage_settings(damage_set_csv, damage_range_set_csv, csv_bdm_type)

        self.assertEqual(damage['schade_meter_oever_zonder_weg'], 1000)
        self.assertEqual(start_damage['test'], 1.0)
        self.assertEqual(full_damage['test'], 2.0)

        # 3. read settings from shapefile

        embankment_data, building_data, ark_data = kds.read_settings_from_shapefiles(
                embankment_source_shape, building_source_shape, ark_source_shape)

        self.assertEqual(len(embankment_data), 3666)
        self.assertEqual(len(building_data), 17824)
        self.assertEqual(len(ark_data), 2897)

    def test_read_result(self):

        kds = KadeSchadeMod(scenario_id=1)

        his_zip_name = os.path.join(kds.result_dir,
                                    'channelwaterlevel.zip')

        input_file = ZipFile(his_zip_name, "r")
        for filename in input_file.namelist():
            if filename.lower() == 'calcpnt.his':
                kds.his = HISFile(StringIO.StringIO(input_file.read(filename)))
                break

        self.assertAlmostEquals(kds.get_daling('BoezemA16_1'), 0.385, delta=0.01)
        self.assertAlmostEqual(kds.get_daling('BoezemA126_3'), 0.02, delta=0.01)

    def test_calc_damage(self):

        kds = KadeSchadeMod(scenario_id=1)
        kds.source_dir = os.path.join(kds.result_dir, 'small')

        embankment_source_shape, building_source_shape, ark_source_shape, \
            damage_set_csv, damage_range_set_csv, csv_bdm_type = kds.get_source_filenames(TestModel())

        damage, start_damage, full_damage, bdm_weg_criterium, \
            bdm_invloedszone_bebouwing, bdm_invloedszone_oude_bebouwing = \
            kds.get_general_damage_settings(damage_set_csv, damage_range_set_csv, csv_bdm_type)

        embankment_data, building_data, ark_data, = kds.read_settings_from_shapefiles(
                embankment_source_shape, building_source_shape, ark_source_shape)

        his_zip_name = os.path.join(kds.result_dir, 'channelwaterlevel.zip')

        input_file = ZipFile(his_zip_name, "r")
        for filename in input_file.namelist():
            if filename.lower() == 'calcpnt.his':
                kds.his = HISFile(StringIO.StringIO(input_file.read(filename)))
                break

        embankment_data, building_data, ark_data, \
            summary = kds.calc_damage(embankment_data,
                                      building_data,
                                      ark_data,
                                      damage,
                                      start_damage,
                                      full_damage,
                                      bdm_weg_criterium,
                                      bdm_invloedszone_bebouwing,
                                      bdm_invloedszone_oude_bebouwing)

        self.assertEqual(len(embankment_data), 5)
        self.assertEqual(len(building_data), 3)
        self.assertEqual(len(ark_data), 5)

        embankment_dict = {int(oever['id_oever']): oever for oever in embankment_data}

        self.assertAlmostEqual(embankment_dict[1]['daling'], 0.38, delta=0.01)
        self.assertAlmostEqual(embankment_dict[1]['perc_bezw'], 100.0)
        self.assertAlmostEqual(embankment_dict[1]['sch_kade'], 50 * 2000)
        self.assertAlmostEqual(embankment_dict[1]['sch_bebouw'], 200)
        self.assertAlmostEqual(embankment_dict[1]['sch_woonb'], 50000)
        self.assertAlmostEqual(embankment_dict[1]['sch_totaal'], 150200)
        self.assertAlmostEqual(embankment_dict[1]['sch_per_m'], 3004.0)

        self.assertAlmostEqual(embankment_dict[4]['daling'], 0.38, delta=0.01)
        self.assertAlmostEqual(embankment_dict[4]['perc_bezw'], 0)
        self.assertAlmostEqual(embankment_dict[4]['sch_kade'], 0)
        self.assertAlmostEqual(embankment_dict[4]['sch_bebouw'], 0)
        self.assertAlmostEqual(embankment_dict[4]['sch_woonb'], 50000)
        self.assertAlmostEqual(embankment_dict[4]['sch_totaal'],50000)
        self.assertAlmostEqual(embankment_dict[4]['sch_per_m'], 250)

        self.assertAlmostEqual(embankment_dict[5]['daling'], 0.38, delta=0.01)
        self.assertAlmostEqual(embankment_dict[5]['perc_bezw'], 50, delta=1)
        self.assertAlmostEqual(embankment_dict[5]['sch_kade'], int(100 * 1000 * 0.5), delta=500)
        self.assertAlmostEqual(embankment_dict[5]['sch_bebouw'], 50)
        self.assertAlmostEqual(embankment_dict[5]['sch_woonb'], 50000)
        self.assertAlmostEqual(embankment_dict[5]['sch_totaal'], 100050, delta=500)
        self.assertAlmostEqual(embankment_dict[5]['sch_per_m'], 1000, delta=5)

        #dest_shape_embankment, dest_shape_building, dest_shape_arks = kds.get_dest_filenames()
        #
        # embankment_output_layer, building_output_layer, ark_output_layer \
        #     = kds.write_results(dest_shape_embankment, embankment_data,
        #                         dest_shape_building, building_data,
        #                         dest_shape_arks, ark_data)

        # self.assertEqual(embankment_output_layer.GetFeatureCount(), len(embankment_data))
        # self.assertEqual(building_output_layer.GetFeatureCount(), len(building_data))
        # self.assertEqual(ark_output_layer.GetFeatureCount(), len(building_data))
