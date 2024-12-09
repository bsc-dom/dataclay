"""
Middleware support class for role validation.
"""
import os
import logging
from dataclay.proxy.middleware import MiddlewareBase, MiddlewareException
logger = logging.getLogger(__name__)
from dataclay.proxy.middleware import middleware_context


class AppConfig:

    def prometheus_metrics_disabled(self) -> bool:
        return os.getenv("PROMETHEUS_METRICS_DISABLED")

    def security_disabled(self) -> bool:
        return os.getenv("SECURITY_DISABLED")


APP_CONFIG = AppConfig()



class MiddlewareValidation(MiddlewareBase):
    def __init__(self, rd):
        self._rd = rd

    async def __call__(self, method_name, request, context):   
        """Middleware function which checks if the user has access to the dataset.

        Raises:
            e: MiddlewareException which depends on the validate() function:
                -If the user is not authenticated: "The user could not be authenticated"
                -If the user have no roles // doesn't have the required role: "The user '{user}' does not have the required role to access the database"

        """
        logger.info("Role validating")
        mw_context = middleware_context.get()
        user = dict(mw_context).get('oidc_user')
        user_roles = dict(mw_context).get("oidc_roles")
        dataset = dict(mw_context).get("dataset-name")
        try:
            #return await self.validate(dataset,user,user_roles,method_name,request,context)
            return await self.validate(path,token_header,permissions,auth_status)
        except Exception as e:
            raise e

    # async def validate(self, dataset, user, user_roles, method_name, request, context):
    #     """Validates if the user have the necessary role to access the dataset

    #     Args:
    #         dataset (str): Dataset that will be accessed
    #         user (str): User username 
    #         user_roles ({str}): Roles the user has

    #     Raises:
    #         MiddlewareException: If the user is not authenticated- "The user could not be authenticated"
    #         MiddlewareException: If the user have no roles - "The user '{user}' does not have the required role to access the database"
    #         MiddlewareException: If the user doesn't have the required role - "The user '{user}' does not have the required role to access the database"

    #     """
    #     if dataset in self._rd:
    #         if user is None:
    #             raise MiddlewareException(f"The user could not be authenticated")
    #         if user_roles is None:
    #             raise MiddlewareException(f"The user '{user}' does not have the required role to access the database")
    #         for role in self._rd[dataset]:
    #             if role in user_roles:
    #                 return await self.__next_func(method_name,request,context)
    #         raise MiddlewareException(f"The user '{user}' does not have the required role to access the database")      
    #     return await self.__next_func(method_name,request,context)
    
###############################################################################################################
    async def validate(self, path, token_header, permissions, auth_status, method_name, request, context):
        """Validates if the user have the necessary role to access the dataset

        Args:
            dataset (str): Dataset that will be accessed
            user (str): User username 
            user_roles ({str}): Roles the user has

        Raises:
            MiddlewareException: If the user is not authenticated- "The user could not be authenticated"
            MiddlewareException: If the user have no roles - "The user '{user}' does not have the required role to access the database"
            MiddlewareException: If the user doesn't have the required role - "The user '{user}' does not have the required role to access the database"

        """
        if not should_perform_keycloak_validation(request.url.path):
            response = await call_next(request)
            return response

        if dataset in self._rd:
            if user is None:
                raise MiddlewareException(f"The user could not be authenticated")
            if user_roles is None:
                raise MiddlewareException(f"The user '{user}' does not have the required role to access the database")
            for role in self._rd[dataset]:
                if role in user_roles:
                    return await self.__next_func(method_name,request,context)
            raise MiddlewareException(f"The user '{user}' does not have the required role to access the database")      
        return await self.__next_func(method_name,request,context)
    
    def should_perform_keycloak_validation(request_url: str):
        if APP_CONFIG.security_disabled():
            return False
        if request_url.startswith('/health'):
            return False
        elif request_url.startswith('/docs'):
            return False
        elif request_url.startswith('/openapi.json'):
            return False
        elif request_url.startswith('/wazuh-prometheus') and not APP_CONFIG.prometheus_metrics_disabled():
            return False
        return True


###############################################################################################################




    async def __next_func(self, method_name, request, context):
        """Middleware continues and calls the function
        """
        try:
            m = getattr(self, method_name)
        except AttributeError:
            return
        logger.debug("Middleware %r is processing method %s" % (self, method_name))
        await m(request, context)
