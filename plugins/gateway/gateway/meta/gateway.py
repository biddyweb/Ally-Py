'''
Created on Jan 28, 2013

@package: gateway
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Contains the SQL alchemy meta for gateway data.
'''

from .metadata_gateway import Base
from sqlalchemy.schema import Column
from sqlalchemy.types import String, BLOB

# --------------------------------------------------------------------

class GatewayData(Base):
    '''
    Provides the gateway data.
    '''
    __tablename__ = 'gateway'

    hash = Column('hash', String(16), primary_key=True)
    identifier = Column('identifier', BLOB, nullable=False)
    navigate = Column('navigate', BLOB, nullable=False)

