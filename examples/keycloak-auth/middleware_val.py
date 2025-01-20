import logging

from dataclay.contrib.middleware import MiddlewareValidation
from dataclay.proxy.middleware import middleware_context
logger = logging.getLogger(__name__)

class MyValidation(MiddlewareValidation):
    async def __call__(self, method_name, request, context):   
        logger.info("Role validating via MyValidation")
        context = middleware_context.get()
        user = dict(context).get('oidc_user')
        user_roles = dict(context).get("oidc_roles")
        dataset = dict(context).get("dataset_name")
        try:
            return await self.validate(dataset,user,user_roles,method_name,request,context)
        except Exception as e:
            raise e