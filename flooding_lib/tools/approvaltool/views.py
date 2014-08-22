import json

from flooding_lib.tools.approvaltool.models import ApprovalObject
from flooding_lib.tools.approvaltool.models import ApprovalRule
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template.loader import render_to_string


def approvaltable(request, approvalobject_id, ignore_post=False):

    approvalobject = ApprovalObject.objects.get(pk=approvalobject_id)

    bool_transform = {True: 'true', False: 'false', None: '-'}
    bool_transform_back = {'true': True, 'false': False, '-': None}

    def get_lines(approvalobject, approvalrules):
        lines = []
        for approvalrule in approvalrules:
            state = approvalobject.state(approvalrule)
            lines.append({
                'id': approvalrule.id,
                'date': state.date.isoformat(),
                'successful': bool_transform[state.successful],
                'name': approvalrule.name,
                'description': approvalrule.description,
                'creatorlog': state.creatorlog,
                'remarks': state.remarks})
        return lines

    if request.method == 'POST' and not ignore_post:
        update = False
        answer = {}
        for rule_id, datajson in request.POST.items():
            rule = ApprovalRule.objects.get(pk=rule_id)
            data = json.loads(datajson)

            if not (data['creatorlog'] == "" and
                    bool_transform_back[data['successful']] is None and
                    data['remarks'] == ""):  # object is not new or has changed

                stat = approvalobject.state(rule)
                changed = (stat.successful !=
                           bool_transform_back[data['successful']] or
                           stat.remarks != data['remarks'])

                if changed:
                    approvalobject.approve(
                        rule=rule,
                        success=bool_transform_back[data['successful']],
                        creator=request.user.get_full_name(),
                        remarks=data['remarks'])
                    update = True

                answer = {'ok': True, 'opm': 'opgeslagen'}

        if update:
            #krijg alle rules die van toepassing zijn op dit object
            approvalrules = ApprovalRule.objects.filter(
                approvalobjecttype__in=approvalobject.approvalobjecttype.all()
                ).order_by('-position')

            answer['lines'] = get_lines(approvalobject, approvalrules)

        return json.dumps(answer)

    else:
        #krijg alle rules die van toepassing zijn op dit object
        approvalrules = ApprovalRule.objects.filter(
            approvalobjecttype__in=approvalobject.approvalobjecttype.all()
            ).order_by('-position')

        lines = get_lines(approvalobject, approvalrules)

    post_url = reverse(
        'flooding_tools_approval_table',
        kwargs={'approvalobject_id': approvalobject_id})
    return render_to_string('approval/approvaltable.js',
                            {'lines': json.dumps(lines),
                             'post_url': post_url
                             })


def approvaltable_page(request, approvalobject_id):
    """
    """
    table = approvaltable(request, approvalobject_id)
    if request.method == 'POST':
        return HttpResponse(table, mimetype="application/json")
    else:
        return render_to_response('approval/table_page.html',
                                  {'table': table})
