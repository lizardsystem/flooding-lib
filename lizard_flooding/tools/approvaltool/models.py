
from django.contrib.gis.db import models
from django.utils.translation import ugettext as _

from flooding_base.models import Setting


class ApprovalObjectType(models.Model):
    """
    """
    TYPE_PROJECT = 10
    TYPE_IMPORTSCENARIO  = 20

    TYPE_CHOICES = (
         (TYPE_PROJECT, _('Project')),
         (TYPE_IMPORTSCENARIO, _('Import scenario')),
    )

    name = models.CharField(max_length=200, unique = True)
    type = models.IntegerField(choices=TYPE_CHOICES)
    approvalrule = models.ManyToManyField('ApprovalRule')

    def __unicode__(self):
        return self.name

class ApprovalObject(models.Model):
    """
    """
    name = models.CharField(max_length=100)
    approvalobjecttype = models.ManyToManyField(ApprovalObjectType)
    approvalrule = models.ManyToManyField('ApprovalRule', through = 'ApprovalObjectState')

    def __unicode__(self):
        return self.name

class ApprovalObjectState(models.Model):
    """
    """
    class Meta:
        get_latest_by = 'date'

    approvalobject = models.ForeignKey('ApprovalObject')
    approvalrule = models.ForeignKey('ApprovalRule')

    date = models.DateTimeField(auto_now_add=True)
    creatorlog = models.CharField(max_length=40)
    successful = models.NullBooleanField(null=True)
    remarks = models.TextField(blank=True)

    def __unicode__(self):
        return u'%s - %s - %s'%(self.approvalobject.name, self.approvalrule.name, self.successful)


class ApprovalRule(models.Model):
    """
    """

    name = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    position= models.IntegerField(default=0)
    permissionlevel = models.IntegerField(default = 1,help_text=_('Permission level of user for performing this task') )

    def __unicode__(self):
        return self.name


