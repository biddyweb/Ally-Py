'''
Created on Nov 1, 2013

@package: support sqlalchemy
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the SQL Alchemy validation based on meta mappings.
'''

from inspect import isclass
import logging
from sqlalchemy.orm.mapper import Mapper
from sqlalchemy.schema import MetaData
from sqlalchemy.types import String

from ally.api.operator.type import TypeModel, TypePropertyContainer
from ally.api.type import typeFor
from ally.api.validate import IValidation, AutoId, Mandatory, MaxLen, Relation, \
    validationsFor, ReadOnly
from ally.design.processor.attribute import requires
from ally.design.processor.context import Context
from ally.design.processor.handler import HandlerProcessor
from ally.support.util_sys import getAttrAndClass
from sql_alchemy.support.mapper import DeclarativeMetaModel, mappingFor
from sqlalchemy.schema import Column
from sqlalchemy.ext.hybrid import hybrid_property

# --------------------------------------------------------------------
log = logging.getLogger(__name__)

# --------------------------------------------------------------------

class Register(Context):
    '''
    The register context.
    '''
    # ---------------------------------------------------------------- Required
    validations = requires(dict)
    
# --------------------------------------------------------------------

class MappedValidationHandler(HandlerProcessor):
    '''
    Implementation for a processor that provides the SQL Alchemy validation based on meta mappings.
    '''

    def process(self, chain, register:Register, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Register the vlaidations based on the meta data definitions.
        '''
        assert isinstance(register, Register), 'Invalid register %s' % register
        if not register.validations: return
        
        for validations in register.validations.values():
            assert isinstance(validations, list), 'Invalid validations %s' % validations
            
            k, mvalidations = 0, []
            while k < len(validations):
                validation, _target = validations[k]
                k += 1
                if isinstance(validation, DeclarativeMetaModel):
                    mvalidations.extend(self.validations(validation))
                    k -= 1
                    del validations[k]
                    continue
            validations.extend(mvalidations)

    def validations(self, mapped):
        '''
        Provides the mapped class validations that can be performed based on the SQL alchemy mapping.
        
        @param mapped: class
            The mapped model class.
        @return: list[Validation, DeclarativeMetaModel]
            The list of validations obtained.
        '''
        assert isclass(mapped), 'Invalid class %s' % mapped
        assert isinstance(mapped.metadata, MetaData), 'Invalid mapped class %s' % mapped
        mapper, model = mappingFor(mapped), typeFor(mapped)
        assert isinstance(mapper, Mapper), 'Invalid mapped class %s' % mapped
        assert isinstance(model, TypeModel), 'Invalid model class %s' % mapped

        # TODO: Gabriel: check if polymorphic will still be handled as validation
        mappers = [(True, model, mapper)]
        for mapper in mapper.polymorphic_iterator():
            pmodel = typeFor(mapper.class_)
            if not isinstance(pmodel, TypeModel) or not issubclass(pmodel.clazz, model.clazz): continue
            mappers.append((False, pmodel, mapper))

        validations = []
        for isMain, model, mapper in mappers:
            mvalidations = validationsFor(mapper.class_)
            if mvalidations:
                for validation, target in mvalidations:
                    if not isinstance(validation, IValidation):
                        assert callable(validation), 'Invalid created validation %s' % validation
                        validation = validation()
                    assert isinstance(validation, IValidation), 'Invalid validation %s' % validation
                    if not isMain and isinstance(validation, Mandatory): continue
                    validations.append((validation, target))
            
            for name, prop in model.properties.items():
                descriptor, dclazz = getAttrAndClass(mapper.class_, name)
                dvalidations = validationsFor(descriptor)
                if dvalidations:
                    for creator, target in dvalidations:
                        validation = creator(prop)
                        assert isinstance(validation, IValidation), 'Invalid validation %s' % validation
                        if target == descriptor: target = dclazz
                        validations.append((validation, target))
                    continue
                
                if isinstance(descriptor, hybrid_property):
                    assert isinstance(descriptor, hybrid_property)
                    if descriptor.fset is None: validations.append((ReadOnly(prop), dclazz))
                    continue
                
                column = getattr(mapper.c, name, None)
                if column is None or not isinstance(column, Column): continue
                assert isinstance(column, Column)
        
                if isMain:
                    if column.primary_key:
                        if column.autoincrement: validations.append((AutoId(prop), mapper.class_))
                        else: validations.append((Mandatory(prop), mapper.class_))
                    elif not column.nullable and column.default is None and column.server_default is None:
                        validations.append((Mandatory(prop), mapper.class_))
        
                if isinstance(column.type, String) and column.type.length:
                    validations.append((MaxLen(prop, column.type.length), mapper.class_))
                
                if isinstance(prop, TypePropertyContainer): validations.append((Relation(prop), mapper.class_))
            
        return validations        
