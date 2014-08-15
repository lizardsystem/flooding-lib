"""
Custom template tags
20090317 kkh
"""

from django import template

register = template.Library()


@register.inclusion_tag("base/tag_search.html", takes_context=True)
def search(context, search_fields):
    """
    Advanced search form with submit button. Always redirects to '.'

    Input:
    search_fields = list of dictionaries. each dictionary is a

    filter row, with the following format: {'name': <name>, 'type':
    <type>, 'options': {'<option>': <value>}, 'fields': ((<name>,
    <value>), (<name>, <value>), ...)], ...}

    type in['checkbox', 'select', 'text']
    the field tuples are type dependent:
      checkbox: (<name>, <value>, <checked>)
      text: (<value>)

    options is optional, available options depend on type:
      type select: "disabled": 1

    Output:
    after submitting, get parameters (name=value) are added to current url
    """

    return {
        'search_fields': search_fields,
        }


@register.inclusion_tag("base/search_form.html", takes_context=True)
def search_form(context, search_field='q', search_value='', hidden_fields={}):
    """Places a search form on the page.

    It always redirects to "."

    search_field: optional
    search_value: optional
    hidden_fields: optional: dictionaries of {fieldname:
    fieldvalue}. removes key entry with search_field

    """

    fields = hidden_fields.copy()
    if search_field in fields:
        del fields[search_field]

    return {
        'search_field': search_field,
        'search_value': search_value,
        'hidden_fields': fields,
        }

LEADING_PAGE_RANGE_DISPLAYED = TRAILING_PAGE_RANGE_DISPLAYED = 10
LEADING_PAGE_RANGE = TRAILING_PAGE_RANGE = 8
NUM_PAGES_OUTSIDE_RANGE = 2
ADJACENT_PAGES = 4


@register.inclusion_tag("base/digg_paginator.html", takes_context=True)
def digg_paginator(context, digg_fields={}):
    """Displays digg style paginator

    input: paginator, page, base_url (optional), extra_fields (optional)

    if paginator is None, or page is None, or nrof pages == 1, then
    is_paginated = False

    extra_fields is a dictionary with {field_name: field_value},
    removes 'page_nr' and 'items_per_page'
    """
    paginator = context.get('paginator', None)
    page = context.get('page', None)
    if paginator and page:
        if paginator.num_pages == 1:
            is_paginated = False
        else:
            is_paginated = True
    else:
        is_paginated = False

    if (is_paginated):
        " Initialize variables "
        in_leading_range = in_trailing_range = False
        pages_outside_leading_range = pages_outside_trailing_range = range(0)

        if (paginator.num_pages <= LEADING_PAGE_RANGE_DISPLAYED):
            in_leading_range = in_trailing_range = True
            page_numbers = [
                n for n in range(1, paginator.num_pages + 1)
                if n > 0 and n <= paginator.num_pages]
        elif (page.number <= LEADING_PAGE_RANGE):
            in_leading_range = True
            page_numbers = [
                n for n in range(1, LEADING_PAGE_RANGE_DISPLAYED + 1)
                if n > 0 and n <= paginator.num_pages]
            pages_outside_leading_range = [
                n + paginator.num_pages
                for n in range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
        elif (page.number > paginator.num_pages - TRAILING_PAGE_RANGE):
            in_trailing_range = True
            page_numbers = [
                n for n in range(
                    paginator.num_pages - TRAILING_PAGE_RANGE_DISPLAYED + 1,
                    paginator.num_pages + 1)
                if n > 0 and n <= paginator.num_pages]
            pages_outside_trailing_range = [
                n + 1 for n in range(0, NUM_PAGES_OUTSIDE_RANGE)]
        else:
            page_numbers = [
                n for n in range(
                    page.number - ADJACENT_PAGES,
                    page.number + ADJACENT_PAGES + 1)
                if n > 0 and n <= paginator.num_pages]
            pages_outside_leading_range = [
                n + paginator.num_pages
                for n in range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
            pages_outside_trailing_range = [
                n + 1 for n in range(0, NUM_PAGES_OUTSIDE_RANGE)]

        if digg_fields:
            extra_fields = digg_fields.copy()
        else:
            extra_fields = context.get('extra_fields', {}).copy()
        if 'page_nr' in extra_fields:
            del extra_fields['page_nr']
        if 'items_per_page' in extra_fields:
            del extra_fields['items_per_page']
        return {
            "is_paginated": is_paginated,
            "base_url": context.get('base_url', ''),
            "extra_fields": extra_fields,
            "is_paginated": is_paginated,
            "results_per_page": paginator.per_page,
            "page": page,
            "paginator": paginator,
            "page_numbers": page_numbers,
            "in_leading_range": in_leading_range,
            "in_trailing_range": in_trailing_range,
            "pages_outside_leading_range": pages_outside_leading_range,
            "pages_outside_trailing_range": pages_outside_trailing_range,
        }


@register.inclusion_tag("base/filter_form.html", takes_context=True)
def filter_form(context, choices, output_fieldname, current_value,
                extra_fields, name=""):
    """renders a choice menu (to filter lists)

    choices: tuple of (value, name)
    output_name: name of GET parameter
    extra_fields: list of dictionaries [{'name': name, 'value':
      value}, ...] (removes entry with output_fieldname)

    """
    fields = extra_fields.copy()
    if output_fieldname in fields:
        del fields[output_fieldname]

    return {
        'choices': choices,
        'output_fieldname': output_fieldname,
        'current_value': current_value,
        'extra_fields': fields,
        'name': name,
        }


@register.inclusion_tag("base/filters_form.html", takes_context=False)
def filters(entries, extra_fields):
    """renders a choice menu with multiple entries (to filter lists)

    input:

    entries: list of dictionaries, each dictionary is a choice entry:
    'choices': tuple of (value, name)
    'output_name': name of GET parameter
    'current_value': value

    extra_fields: dictionaries {<name>: <value>, ...}
    (removes entries of all output_fieldnames)

    """
    fields = extra_fields.copy()
    for entry in entries:
        if entry['output_name'] in fields:
            del fields[entry['output_name']]

    return {
        'entries': entries,
        'extra_fields': fields,
        }


@register.inclusion_tag("base/objecttable.html", takes_context=False)
def objecttable(name, columns, data, sort):
    """Renders a nice looking table.

    input:

    name=name of table

    columns=list of dictionaries {'name':.., 'sort': output sort field value
      , 'sort_rev':..., 'width': (html width, e.g. "100%")}

    data=list of rows, where row = [{'url': optional url, 'value':
    value},... ] --> see below

    sort=current sort value


    data row dictionary has the following possible keys:
    url: displays a href around value and icon, (icon is not showed
    when urlpost has a value)
    urlpost: displays a form, be sure that icon has a value
    value: text to display
    icon: iconname, without extension .png. e.g. edit, edit_disabled,
    delete, delete_disabled
    icontitle: mouseover for icon
    postclickmessage: confirmtext to show before submitting
    """
    return {'name': name, 'sort': sort, 'columns': columns,
            'data': data}
