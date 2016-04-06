# -*- coding: utf-8 -*-
import logging
import itertools

import mapnik


log = logging.getLogger('nens.mapnik_legend')


def search_value_lt(value, value_list):
    """
    searches first value that: value <= value_in of
    value_list. returns value_out. if nothing found, return
    value_out of last item

    value_list is an list of tuples (value_in, value_out)

      >>> search_value_lt(5, [(None, (0,)), (5, (1,)), (6, (2,))])
      (1,)

    """
    try:
        dummy, result_out = itertools.ifilter(
            lambda(x, v): value <= x, value_list).next()
    except StopIteration:
        dummy, result_out = value_list[-1]

    return result_out


class MapnikPointLegend:
    """
    Calculates mapnik (point) rules using ShapeDataLegend. Maps input
    values to these rules.

    Sample usage:
    input_dict = {'row1': 1, 'row2': 2}

    shapedatalegend = get_object_or_404(ShapeDataLegend,
    pk=request.GET['object_id'])

    if shapedatalegend.type == ShapeDataLegend.TYPE_POINT:
      sm = SymbolManager(SYMBOLS_DIR)
      mpl = MapnikPointLegend(shapedatalegend, sm)
      mapnik_style = mpl.get_style() #get mapnik style with a set of rules.
      rule_name = mpl.get_rule_name(input_dict) #get rule name by
                                                #looking at input
      title, blocks = mpl.get_legend_data() #get info to draw legend
    """

    def convert_mapping_to_tuple(self, objects):
        """
        input: queryset that contains the objects
        output: sorted tuple list (value_in, value_out)

        objects must have field value_in and function get_value_out()
        """

        dict = {}
        for o in objects:
            dict[o.value_in] = o.get_value_out()
            #strings are never None... instead there is a ''
            if o.value_in == '':
                dict[None] = o.get_value_out()
        tuplelist = dict.items()
        tuplelist.sort()  # sorts on first field
        return tuplelist, dict

    def get_output_properties(self, valuedict):
        """given a valuedict, produce a dictionary with all the
        properties that should be displayed

        output dict keys: symbol, color, size, rotate, shadow_height
        """
        result = {}

        symbol_value = valuedict[self.fn['symbol']]
        color_value = valuedict[self.fn['color']]
        size_value = valuedict[self.fn['size']]
        rotation_value = valuedict[self.fn['rotation']]
        shadowheight_value = valuedict[self.fn['shadowheight']]

        result['symbol'] = search_value_lt(symbol_value, self.values['symbol'])
        result['color'] = search_value_lt(color_value, self.values['color'])
        result['size'] = search_value_lt(size_value, self.values['size'])
        result['rotate'] = search_value_lt(
            rotation_value, self.values['rotation'])
        result['shadow_height'] = search_value_lt(
            shadowheight_value, self.values['shadowheight'])

        return result

    def get_rule_name(self, valuedict):
        """
        calculated the mapnik rule name, for a given set of data. the
        legend MUST be correctly configured, or an exception may be
        raised

        name is composed as follows: <sdl_id>_<symbol
        (name)>_<abs_color (rrggbbaa)>_<size (xx)x(yy)>_<rotation
        (degrees)>_<shadowheight (pixels)>

        example input: {'type': 'GEMAAL', 'value': 5.0}
        example output: "1_plus_ffffffff_32x32_0_0"

        must be fast.
        interpolation not supported yet

        note: 0x0 means keep original size.
        """

        output_values = self.get_output_properties(valuedict)

        symbol_out_str = '%s' % (output_values['symbol'])
        color_out_str = '%02X%02X%02X%02X' % (
            tuple([256 * i for i in output_values['color']]))
        size_out_str = '%dx%d' % (output_values['size'])
        rotation_out_str = '%d' % (output_values['rotate'])
        shadowheight_out_str = '%d' % (output_values['shadow_height'])

        result = '%d_%s_%s_%s_%s_%s' % (
            self.sdl.pk, symbol_out_str, color_out_str, size_out_str,
            rotation_out_str, shadowheight_out_str)
        return str(result)

    def get_legend_data(self):
        """Returns all info needed to draw the legend in a list. Ugly function.

        title, [{'title': <title>, 'content': [row1, row2, ...]},
        {'title': <title>, 'content': [row1, row2, ...]}, ...]

        titles are strings,


        the symbol properties can be used with visualization.get_symbol
        """
        def generate_block_row(value_in, output_dict_template,
                               output_dict_key, label):

            valuedict = output_dict_template.copy()
            valuedict[output_dict_key] = value_in
            row = {
                'symbol_properties':
                self.get_output_properties(valuedict), 'text': label}

            return row

        valuedict_empty = {self.fn['size']: None,
                           self.fn['symbol']: None,
                           self.fn['rotation']: None,
                           self.fn['shadowheight']: None,
                           self.fn['color']: None,
                           }
        result = []

        dependend_parameter = {}
        dependend_parameter[self.sdl.color_field] = []
        dependend_parameter[self.sdl.size_field] = []
        dependend_parameter[self.sdl.symbol_field] = []
        dependend_parameter[self.sdl.rotation_field] = []
        dependend_parameter[self.sdl.shadowheight_field] = []

        dependend_parameter[self.sdl.color_field].extend(
            [a for a, b in self.values['color']])
        dependend_parameter[self.sdl.size_field].extend(
            [a for a, b in self.values['size']])
        dependend_parameter[self.sdl.symbol_field].extend(
            [a for a, b in self.values['symbol']])
        dependend_parameter[self.sdl.rotation_field].extend(
            [a for a, b in self.values['rotation']])
        dependend_parameter[self.sdl.shadowheight_field].extend(
            [a for a, b in self.values['shadowheight']])

        for key, parameter in dependend_parameter.items():
            unique = []
            last = [None]
            parameter.sort()
            for n in parameter:
                if not last == n:
                    if n is None:
                        unique.append(generate_block_row(
                                None, valuedict_empty, key.name_in_source,
                                'geen waarde'))
                    elif last in [[None], None]:
                        unique.append(generate_block_row(
                                n, valuedict_empty, key.name_in_source,
                                '<= ' + str(n)))
                    elif n > 1e+99:
                        unique.append(generate_block_row(
                                n, valuedict_empty, key.name_in_source,
                                '>' + str(last)))
                    else:
                        unique.append(generate_block_row(
                                n, valuedict_empty, key.name_in_source,
                                str(last) + ' tot ' + str(n)))
                    last = n

            block = {'title': key.friendlyname,
                       'content': unique}
            result.append(block)

        return self.sdl.name, result

    def make_rules_for_input_combinations(
        self, possible_values, value_dict={}):
        """
        Recursive function to loop all possible input
        combinations. For each input combination, calculate rule name
        and rule.

        possible_values: dict of fieldname as key and a dict of {value: None}
        value_dict: dict of all current values (starts empty)

        Return a dictionary with all rulename as key and rule as value.
        """
        if possible_values:
            #not all possible values are put into value_dicts
            fieldname, fieldvalues = possible_values.items()[0]
            del possible_values[fieldname]

            rules = {}
            for fieldvalue in fieldvalues.keys():
                new_rules = self.make_rules_for_input_combinations(
                    possible_values, {fieldname: fieldvalue})
                rules.update(new_rules)
            return rules
        else:
            #possible values are empty, all values are listed in value_dict
            rule_name = self.get_rule_name(value_dict)
            symbol_kwargs = self.get_output_properties(value_dict)
            symbol_out = symbol_kwargs['symbol'][0] + '.png'
            size_out_x, size_out_y = symbol_kwargs['size']

            filename_abs = str(self.sm.get_symbol_transformed(
                    symbol_out, **symbol_kwargs))
            mapnik_rule = mapnik.Rule()
            log.debug("SYMBOL transformaed %s", filename_abs)
            ps = mapnik.PointSymbolizer(
                filename_abs, size_out_x, size_out_y)
            mapnik_rule.symbols.append(ps)
            mapnik_rule.filter = mapnik.Filter(
                str("[NAME] = '%s'" % (rule_name)))

            return {rule_name: mapnik_rule}

    def get_style(self, **kwargs):
        """
        calculates all mapnik rules and put them in a mapnik
        style. return style.

        as an effect of this function all possible symbols for the
        legend are generated

        kwargs: min, max (if % are used)
        """

        #make an overview of all possible input values, per field
        possible_values = {}
        for fieldname in self.fn.values():
            possible_values[fieldname] = {}
        for key, value in self.values.items():
            for value_in, value_out in value:
                possible_values[self.fn[key]][value_in] = None

        result_style = mapnik.Style()
        for r in self.make_rules_for_input_combinations(
            possible_values.copy()).values():
            result_style.rules.append(r)

        return result_style

    def get_presentationtype_fields(self):
        """
        make an overview of all possible input values, per field.
        returns a dictionary with key=field.id and value=field
        """

        fields = [self.sdl.color_field, self.sdl.size_field,
                  self.sdl.symbol_field, self.sdl.rotation_field,
                  self.sdl.shadowheight_field]

        output = {}
        for field in fields:
            output[field.id] = field

        return output

    def __init__(self, shapedatalegend, symbolmanager):
        """Read shapedatalegend and store all info locally. The
        symbolmanager is used to generate symbols.

        dimensions: color, size, symbol, rotation, shadowheight
        """

        self.sdl = shapedatalegend
        self.sm = symbolmanager

        if not self.sdl.color:
            raise Exception('ShapeDataLegend has no entry for color.')
        if not self.sdl.size:
            raise Exception('ShapeDataLegend has no entry for size.')
        if not self.sdl.symbol:
            raise Exception('ShapeDataLegend has no entry for symbol.')
        if not self.sdl.rotation:
            raise Exception('ShapeDataLegend has no entry for rotation.')
        if not self.sdl.shadowheight:
            raise Exception('ShapeDataLegend has no entry for shadowheight.')

        #read color input values in a tuple (value_in, value_out)
        self.values = {}
        self.value_dict = {}

        self.values['color'], self.value_dict['color'] = (
            self.convert_mapping_to_tuple(
                self.sdl.color.get_visualizer_set().all()))
        self.values['size'], self.value_dict['size'] = (
            self.convert_mapping_to_tuple(
                self.sdl.size.get_visualizer_set().all()))
        self.values['symbol'], self.value_dict['symbol'] = (
            self.convert_mapping_to_tuple(
                self.sdl.symbol.get_visualizer_set().all()))
        self.values['rotation'], self.value_dict['rotation'] = (
            self.convert_mapping_to_tuple(
                self.sdl.rotation.get_visualizer_set().all()))
        self.values['shadowheight'], self.value_dict['shadowheight'] = (
            self.convert_mapping_to_tuple(
                self.sdl.shadowheight.get_visualizer_set().all()))

        #fieldnames
        self.fn = {}
        self.fn['color'] = self.sdl.color_field.name_in_source
        self.fn['size'] = self.sdl.size_field.name_in_source
        self.fn['symbol'] = self.sdl.symbol_field.name_in_source
        self.fn['rotation'] = self.sdl.rotation_field.name_in_source
        self.fn['shadowheight'] = self.sdl.shadowheight_field.name_in_source

        for k, v in self.values.items():
            if not v:
                raise Exception(
                    ('legend mapping is not valid: %s has no entries '
                     'in corresponding model') % k)
