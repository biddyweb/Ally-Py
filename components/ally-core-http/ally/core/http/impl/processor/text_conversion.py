'''
Created on Aug 10, 2011

@package: ally core babel
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Gabriel Nistor

Provides the converters for the response content and request content.
'''

from ally.api.operator.container import Model
from ally.api.operator.type import TypeModel
from ally.api.type import Type, Percentage, Number, Date, DateTime, Time, \
    Boolean, List, Locale as TypeLocale
from ally.container.ioc import injected
from ally.core.http.spec.codes import FORMATING_ERROR
from ally.core.spec.resources import Converter
from ally.design.processor.attribute import requires, defines, optional
from ally.design.processor.handler import HandlerProcessor
from ally.http.spec.headers import HeaderRaw, HeadersRequire, HeadersDefines
from ally.internationalization import _
from babel import numbers as bn, dates as bd
from babel.core import Locale
from datetime import datetime
import logging
from ally.support.util import immut
from ally.http.spec.codes import CodedHTTP

# --------------------------------------------------------------------

log = logging.getLogger(__name__)

# --------------------------------------------------------------------

FORMATTED_TYPE = (Number, Percentage, Date, Time, DateTime)
# The formatted types for the babel converter.
LIST_LOCALE = List(TypeLocale)
# The locale list used to set as an additional argument.

FORMAT = immut({clsTyp: HeaderRaw('X-Format-%s' % clsTyp.__name__) for clsTyp in FORMATTED_TYPE})
# The custom format headers indexed by type.
CONTENT_FORMAT = immut({clsTyp: HeaderRaw('X-Content-Format-%s' % clsTyp.__name__) for clsTyp in FORMATTED_TYPE})
# The custom content format headers indexed by type.

# --------------------------------------------------------------------

class FormatError(Exception):
    '''
    Thrown for invalid formatting.
    '''
    def __init__(self, message):
        assert isinstance(message, str), 'Invalid message %s' % message
        self.message = message
        super().__init__(message)

class BabelConfigurations:
    '''
    Provides general babel configurations.
    '''

    languageDefault = str
    # The default language on the response used when none is specified
    formats = {
               Date:('full', 'long', 'medium', 'short'),
               Time:('full', 'long', 'medium', 'short'),
               DateTime:('full', 'long', 'medium', 'short')
               }
    # The known keyed formats.

    defaults = {
               Date:'short',
               Time:'short',
               DateTime:'short'
               }
    # The default formats.

    def __init__(self):
        assert isinstance(self.languageDefault, str), 'Invalid default language %s' % self.languageDefault
        assert isinstance(self.formats, dict), 'Invalid formats %s' % self.formats
        assert isinstance(self.defaults, dict), 'Invalid defaults %s' % self.defaults

    def processFormats(self, locale, formats):
        '''
        Process the formats to a complete list of formats that will be used by conversion.
        '''
        assert isinstance(formats, dict), 'Invalid formats %s' % formats
        assert isinstance(locale, Locale), 'Invalid locale %s' % locale

        for clsTyp, format in formats.items():
            # In here we just check that the format is valid.
            try:
                if clsTyp in (Number, Percentage): bn.parse_pattern(format)
                elif format not in self.formats[clsTyp]: bd.parse_pattern(format)
            except Exception as e:
                raise FormatError('invalid %s format \'%s\' because: %s' % (clsTyp.__name__, format, str(e)))

        if Number not in formats: formats[Number] = locale.decimal_formats.get(None).pattern
        if Percentage not in formats: formats[Percentage] = locale.percent_formats.get(None).pattern

        for clsTyp, default in self.defaults.items():
            if clsTyp not in formats: formats[clsTyp] = default

        return formats
        
# --------------------------------------------------------------------

class Response(CodedHTTP):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Defined
    text = defines(str)
    errorMessage = defines(str)
    
class RequestConverter(HeadersRequire):
    '''
    The request converter context.
    '''
    # ---------------------------------------------------------------- Optional
    language = optional(str)
    # ---------------------------------------------------------------- Defined
    converter = defines(Converter, doc='''
    @rtype: Converter
    The converter to use for decoding request content.
    ''')
    
class RequestExtra(HeadersRequire):
    '''
    The request for response converter context.
    '''
    # ---------------------------------------------------------------- Optional
    argumentsOfType = optional(dict)
    accLanguages = optional(list)

class ResponseConverter(Response):
    '''
    The response converter context.
    '''
    # ---------------------------------------------------------------- Defined
    language = defines(str, doc='''
    @rtype: string
    The language that the converter is using for the response.
    ''')
    converter = defines(Converter, doc='''
    @rtype: Converter
    The converter to use for decoding request content.
    ''')

class ResponseEncode(HeadersDefines):
    '''
    The response context.
    '''
    # ---------------------------------------------------------------- Required
    converter = requires(Converter)

# --------------------------------------------------------------------

@injected
class BabelConverterRequestHandler(HandlerProcessor, BabelConfigurations):
    '''
    Implementation based on Babel for a processor that provides the converters based on language and object formating 
    for the request.
    '''

    def __init__(self):
        BabelConfigurations.__init__(self)
        HandlerProcessor.__init__(self)

    def process(self, chain, request:RequestConverter, response:Response, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provide the character conversion for request.
        '''
        assert isinstance(request, RequestConverter), 'Invalid request %s' % request
        assert isinstance(response, Response), 'Invalid response %s' % response

        formats = {}
        for clsTyp, header in CONTENT_FORMAT.items():
            assert isinstance(header, HeaderRaw), 'Invalid header %s' % header
            value = header.fetch(request)
            if value: formats[clsTyp] = value

        locale = None
        if RequestConverter.language in request and request.language is not None:
            try: locale = Locale.parse(request.language, sep='-')
            except: assert log.debug('Invalid request content language %s', request.language) or True

        if locale is None:
            if RequestConverter.language in request: request.language = self.languageDefault
            locale = Locale.parse(self.languageDefault)

        try: formats = self.processFormats(locale, formats)
        except FormatError as e:
            assert isinstance(e, FormatError)
            if response.isSuccess is False: return  # Skip in case the response is in error
            FORMATING_ERROR.set(response)
            response.text = 'Bad request content formatting'
            response.errorMessage = 'Bad request content formatting, %s' % e.message
            return

        request.converter = ConverterBabel(locale, formats)

@injected
class BabelConverterResponseHandler(HandlerProcessor, BabelConfigurations):
    '''
    Implementation based on Babel for a processor that provides the converters based on language and object formating 
    for the response.
    '''

    def __init__(self):
        BabelConfigurations.__init__(self)
        HandlerProcessor.__init__(self)

    def process(self, chain, request:RequestExtra, response:ResponseConverter, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provide the character conversion for response.
        '''
        assert isinstance(request, RequestExtra), 'Invalid request %s' % request
        assert isinstance(response, ResponseConverter), 'Invalid response %s' % response

        formats = {}
        for clsTyp, header in FORMAT.items():
            assert isinstance(header, HeaderRaw), 'Invalid header %s' % header
            value = header.fetch(request)
            if value: formats[clsTyp] = value

        locale = None
        if response.language:
            try: locale = Locale.parse(response.language, sep='-')
            except: assert log.debug('Invalid response content language %s', response.language) or True

        if locale is None:
            if RequestExtra.accLanguages in request and request.accLanguages is not None:
                for lang in request.accLanguages:
                    try: locale = Locale.parse(lang, sep='-')
                    except:
                        assert log.debug('Invalid accepted content language %s', lang) or True
                        continue
                    assert log.debug('Accepted language %s for response', locale) or True
                    break

            if locale is None:
                locale = Locale.parse(self.languageDefault)
                if RequestExtra.accLanguages in request:
                    if request.accLanguages is not None:
                        request.accLanguages.insert(0, self.languageDefault)
                        accLanguages = request.accLanguages
                    else: accLanguages = request.accLanguages = [self.languageDefault]
                else: accLanguages = [self.languageDefault]
                if RequestExtra.argumentsOfType in request and request.argumentsOfType is not None:
                    request.argumentsOfType[LIST_LOCALE] = accLanguages
                assert log.debug('No language specified for the response, set default %s', locale) or True

            response.language = str(locale)

            if RequestExtra.argumentsOfType in request and request.argumentsOfType is not None:
                request.argumentsOfType[TypeLocale] = response.language

        try: formats = self.processFormats(locale, formats)
        except FormatError as e:
            assert isinstance(e, FormatError)
            if response.isSuccess is False: return  # Skip in case the response is in error
            FORMATING_ERROR.set(response)
            response.text = 'Bad content formatting for response'
            response.errorMessage = 'Bad content formatting for response, %s' % e.message
            return

        response.converter = ConverterBabel(locale, formats)
        
# --------------------------------------------------------------------

@injected
class BabelConversionEncodeHandler(HandlerProcessor):
    '''
    Implementation based on Babel for a processor that encodes the Babel converter format.
    '''
    
    def process(self, chain, response:ResponseEncode, **keyargs):
        '''
        @see: HandlerProcessor.process
        
        Provide the response formatting header encode.
        '''
        assert isinstance(response, ResponseEncode), 'Invalid response %s' % response

        if isinstance(response.converter, ConverterBabel):
            assert isinstance(response.converter, ConverterBabel)
            if response.headers is None: response.headers = {}
            for clsTyp, format in response.converter.formats.items():
                header = CONTENT_FORMAT.get(clsTyp)
                if header:
                    assert isinstance(header, HeaderRaw), 'Invalid header %s' % header
                    header.put(response, format)

# --------------------------------------------------------------------

class ConverterBabel(Converter):
    '''
    Converter implementation based on Babel.
    '''
    __slots__ = ('locale', 'formats')

    def __init__(self, locale, formats):
        assert isinstance(locale, Locale), 'Invalid locale %s' % locale
        assert isinstance(formats, dict), 'Invalid formats %s' % formats
        self.locale = locale
        self.formats = formats

    def asString(self, objValue, objType):
        '''
        @see: Converter.asString
        '''
        assert isinstance(objType, Type), 'Invalid object type %s' % objType
        if isinstance(objType, TypeModel):  # If type model is provided we consider the model property type
            assert isinstance(objType, TypeModel)
            container = objType.container
            assert isinstance(container, Model)
            objType = container.properties[container.propertyId]
        if objType.isOf(str):
            return objValue
        if objType.isOf(bool):
            return str(objValue)
        if objType.isOf(Percentage):
            return bn.format_percent(objValue, self.formats.get(Percentage, None), self.locale)
        if objType.isOf(Number):
            return bn.format_decimal(objValue, self.formats.get(Number, None), self.locale)
        if objType.isOf(Date):
            return bd.format_date(objValue, self.formats.get(Date, None), self.locale)
        if objType.isOf(Time):
            return bd.format_time(objValue, self.formats.get(Time, None), self.locale)
        if objType.isOf(DateTime):
            return bd.format_datetime(objValue, self.formats.get(DateTime, None), None, self.locale)
        raise TypeError('Invalid object type %s for Babel converter' % objType)

    # TODO: add proper support for parsing.
    # Currently I haven't found a proper library for parsing numbers and dates, Babel has a very week support for
    # this you cannot specify the format of parsing for instance, so at this point we will use python standard.
    def asValue(self, strValue, objType):
        '''
        @see: Converter.asValue
        '''
        assert isinstance(objType, Type), 'Invalid object type %s' % objType
        if strValue is None: return None
        if isinstance(objType, TypeModel):  # If type model is provided we consider the model property type 
            assert isinstance(objType, TypeModel)
            container = objType.container
            assert isinstance(container, Model)
            objType = container.properties[container.propertyId]
        if objType.isOf(str):
            return strValue
        if objType.isOf(Boolean):
            return strValue.strip().lower() == _('true').lower()
        if objType.isOf(Percentage):
            return float(strValue) / 100
        if objType.isOf(int):
            return int(strValue)
        if objType.isOf(Number):
            return bn.parse_decimal(strValue, self.locale)
        if objType.isOf(Date):
            return datetime.strptime(strValue, '%Y-%m-%d').date()
        if objType.isOf(Time):
            return datetime.strptime(strValue, '%H:%M:%S').time()
        if objType.isOf(DateTime):
            return datetime.strptime(strValue, '%Y-%m-%d %H:%M:%S')
        raise TypeError('Invalid object type %s for Babel converter' % objType)
