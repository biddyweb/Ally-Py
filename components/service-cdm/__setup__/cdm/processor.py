'''
Created on Jan 5, 2012

@package: service CDM
@copyright: 2012 Sourcefabric o.p.s.
@license http://www.gnu.org/licenses/gpl - 3.0.txt
@author: Mugur Rus

Provides the configurations for delivering files from the local file system.
'''

from ..ally_http.processor import contentLengthEncode, contentTypeEncode, header, \
    allowEncode, internalError
from ally.container import ioc
from ally.core.cdm.processor.content_delivery import ContentDeliveryHandler
from ally.design.processor import Handler, Assembly
from os import path

# --------------------------------------------------------------------

@ioc.config
def repository_path():
    ''' The repository absolute or relative (to the distribution folder) path from where to serve the files '''
    return path.join('workspace', 'shared', 'cdm')

# --------------------------------------------------------------------
# Creating the processors used in handling the request

@ioc.entity
def assemblyContent() -> Assembly:
    '''
    The assembly containing the handlers that will be used in processing a content file request.
    '''
    return Assembly()

@ioc.entity
def contentDelivery() -> Handler:
    h = ContentDeliveryHandler()
    h.repositoryPath = repository_path()
    return h

# --------------------------------------------------------------------

@ioc.before(assemblyContent)
def updateAssemblyContent():
    assemblyContent().add(internalError(), header(), contentDelivery(), allowEncode(), contentTypeEncode(),
                          contentLengthEncode())
    