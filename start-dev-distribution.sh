FULLPATH=$(cd ${0%/*} && echo $PWD/${0##*/})
ALLYPATH=`dirname "$FULLPATH"`

ALLYCOM=${ALLYPATH}/components/
PYTHONPATH=${PYTHONPATH}:${ALLYCOM}ally
PYTHONPATH=${PYTHONPATH}:${ALLYCOM}ally-api
PYTHONPATH=${PYTHONPATH}:${ALLYCOM}ally-core
PYTHONPATH=${PYTHONPATH}:${ALLYCOM}ally-core-http
PYTHONPATH=${PYTHONPATH}:${ALLYCOM}ally-indexing
PYTHONPATH=${PYTHONPATH}:${ALLYCOM}ally-http
PYTHONPATH=${PYTHONPATH}:${ALLYCOM}ally-http-asyncore-server
PYTHONPATH=${PYTHONPATH}:${ALLYCOM}ally-http-mongrel2-server
PYTHONPATH=${PYTHONPATH}:${ALLYCOM}ally-plugin
PYTHONPATH=${PYTHONPATH}:${ALLYCOM}distribution-ally-rest-basic
PYTHONPATH=${PYTHONPATH}:${ALLYCOM}service-assemblage
PYTHONPATH=${PYTHONPATH}:${ALLYCOM}service-cdm
PYTHONPATH=${PYTHONPATH}:${ALLYCOM}service-gateway

PYTHONPATH=${PYTHONPATH}:${ALLYPATH}/distribution/libraries/Babel-1.3-py3.2

ALLYPLUG=${ALLYPATH}/plugins/
PYTHONPATH=${PYTHONPATH}:${ALLYPLUG}gateway
PYTHONPATH=${PYTHONPATH}:${ALLYPLUG}gateway-acl
PYTHONPATH=${PYTHONPATH}:${ALLYPLUG}gui-action
PYTHONPATH=${PYTHONPATH}:${ALLYPLUG}gui-core
PYTHONPATH=${PYTHONPATH}:${ALLYPLUG}indexing
PYTHONPATH=${PYTHONPATH}:${ALLYPLUG}internationalization
PYTHONPATH=${PYTHONPATH}:${ALLYPLUG}language
PYTHONPATH=${PYTHONPATH}:${ALLYPLUG}security
PYTHONPATH=${PYTHONPATH}:${ALLYPLUG}security-rbac
PYTHONPATH=${PYTHONPATH}:${ALLYPLUG}support-cdm
PYTHONPATH=${PYTHONPATH}:${ALLYPLUG}support-mongoengine
PYTHONPATH=${PYTHONPATH}:${ALLYPLUG}support-sqlalchemy

ALLYCOMMON=${ALLYPATH}/../ally-py-common/
PYTHONPATH=${PYTHONPATH}:${ALLYCOMMON}content
PYTHONPATH=${PYTHONPATH}:${ALLYCOMMON}hr-user
PYTHONPATH=${PYTHONPATH}:${ALLYCOMMON}patch-praha
PYTHONPATH=${PYTHONPATH}:${ALLYCOMMON}security-user
PYTHONPATH=${PYTHONPATH}:${ALLYCOMMON}distribution-ally-user-management

export PYTHONPATH=$PYTHONPATH
export LC_CTYPE="en_US.UTF-8"
python3.2 distribution/run.py $*
