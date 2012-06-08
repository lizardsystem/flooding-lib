from models import ApprovalObjectType, ApprovalObject, ApprovalObjectState, ApprovalRule
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import Context, loader
from django.template.loader import render_to_string
from django.utils import simplejson
from django.utils.translation import ugettext as _
import datetime

def approvaltable(request,approvalobject_id, ignore_post = False):
    """
    Renders Lizard-flooding page with an overview of all exports
    """
    bool_transform = {True: 'true', False:'false', None:'-'}
    bool_transform_back = {'true':True, 'false':False, '-':None}
    
    def get_lines(approvalobject, approvalrule):
        lines = []
        for approvalrule in approvalrules:
            try:
                stat = approvalrule.approvalobjectstate_set.filter(approvalobject = approvalobject).latest()
                state = {"successful" : bool_transform[stat.successful],"creatorlog": stat.creatorlog,"remarks": stat.remarks, "date":stat.date }
            except ApprovalObjectState.DoesNotExist, e:
                state = {"successful" : bool_transform[None],"creatorlog": "","remarks": "", "date":datetime.datetime.now() }
            
            lines.append({'id':approvalrule.id,'date':state["date"].isoformat(), 'successful':state["successful"], 'name':approvalrule.name, 'description': approvalrule.description, 'creatorlog': state["creatorlog"], 'remarks':state["remarks"] })     
        return lines
    
    

    
    
    if request.method == 'POST' and not ignore_post: 
        update = False
        for rule_id in request.POST:
            data = simplejson.loads(request.POST.get(rule_id))
            if not (data['creatorlog'] == "" and bool_transform_back[data['successful']] == None and data['remarks'] == ""): #object is not new or has changed
                try:
                    stat = ApprovalObjectState.objects.filter(approvalobject=int(approvalobject_id), approvalrule=int(rule_id)).latest()
                    if stat.successful != bool_transform_back[data['successful']] or stat.remarks != data['remarks']:
                        changed = True
                    else:
                        changed = False
                         
                except ApprovalObjectState.DoesNotExist, e:
                    changed = True
                
                if changed:
                    obj = ApprovalObjectState.objects.create(approvalobject = ApprovalObject.objects.get(pk=int(approvalobject_id)), approvalrule = ApprovalRule.objects.get(pk=int(rule_id)), remarks = data['remarks'], successful = bool_transform_back[data['successful']],creatorlog= request.user.get_full_name())
                    update = True
       
                answer = {'ok':True, 'opm':'opgeslagen'}
        
        if update:
            approvalobject = ApprovalObject.objects.get(pk=approvalobject_id)
        
            #krijg alle rules die van toepassing zijn op dit object
            approvalrules = ApprovalRule.objects.filter(approvalobjecttype__in = approvalobject.approvalobjecttype.all()).order_by('-position')
            
            answer['lines'] = get_lines(approvalobject, approvalrules)
        
        return simplejson.dumps(answer)

    else:
        approvalobject = ApprovalObject.objects.get(pk=approvalobject_id)
        
        #krijg alle rules die van toepassing zijn op dit object
        approvalrules = ApprovalRule.objects.filter(approvalobjecttype__in = approvalobject.approvalobjecttype.all()).order_by('-position')
        
        lines = get_lines(approvalobject, approvalrules)
        
    post_url = reverse('flooding_tools_approval_table', kwargs={'approvalobject_id': approvalobject_id})
    return render_to_string('approval/approvaltable.js', 
                              {'lines': simplejson.dumps(lines),
                               'post_url':post_url
                               })        
    
def approvaltable_page(request,approvalobject_id):
    """
    """
    table = approvaltable(request,approvalobject_id )
    if request.method == 'POST':
        return HttpResponse(table, mimetype="application/json")
    else:
        return render_to_response('approval/table_page.html', 
                              {'table': table
                               }) 
