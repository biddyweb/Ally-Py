'''
Created on Jan 9, 2012

@package: internationalization
@copyright: 2011 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the services setup for internationalization.
'''

from ..plugin.registry import registerService
from .database import binders
from ally.cdm.spec import ICDM
from ally.cdm.support import ExtendPathCDM
from ally.container import support, ioc, bind
from ..cdm.service import contentDeliveryManager
import logging
from internationalization.core.impl.po_file_manager import DBPOFileManager
from internationalization.core.impl.cdm_syncronizer import poCDMSyncronyzer

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

SERVICES = 'internationalization.api.**.I*Service'

# --------------------------------------------------------------------

bind.bindToEntities('internationalization.impl.**.*Alchemy', poCDMSyncronyzer, DBPOFileManager, binders=binders)
support.createEntitySetup('internationalization.impl.**.*', 'internationalization.*.impl.**.*')
support.listenToEntities(SERVICES, listeners=registerService, beforeBinding=False)
support.loadAllEntities(SERVICES)

# --------------------------------------------------------------------

@ioc.entity
def cdmLocale() -> ICDM:
    '''
    The content delivery manager (CDM) for the locale files.
    '''
    return ExtendPathCDM(contentDeliveryManager(), 'cache/locale/%s')
