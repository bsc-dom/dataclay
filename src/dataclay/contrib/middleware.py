"""
Middleware support class for role validation.
"""
import os
import logging
import keycloak
from dataclay.proxy.middleware import MiddlewareBase
logger = logging.getLogger(__name__)
from dataclay.proxy.middleware import middleware_context


class AppConfig:

    def prometheus_metrics_disabled(self) -> bool:
        return os.getenv("PROMETHEUS_METRICS_DISABLED", "False").lower() in ["true", "1", "yes"]

    def security_disabled(self) -> bool:
        return os.getenv("SECURITY_DISABLED", "False").lower() in ["true", "1", "yes"]



APP_CONFIG = AppConfig()



class MiddlewareValidation(MiddlewareBase):

    def should_perform_keycloak_validation(self, request_url: str):
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
    
    def validate_permissions(self, permissions):
        for permission in permissions:
            scopes = permission.get('scopes')
            auth_status = keycloak.uma_permissions.AuthStatus(
                is_logged_in=True,  # Assuming the user is logged in
                is_authorized=True if permission.get('scopes') else False,  # Check if scopes exist
                missing_permissions=set()  # No missing permissions for now
            )

            if auth_status.is_logged_in and auth_status.is_authorized:
                logging.info("User is authorized in scope(s): %s", scopes)
                return True

        logging.warning("User is not authorized.")
        return False


    async def __next_func(self, method_name, request, context):
        """Middleware continues and calls the function
        """
        try:
            m = getattr(self, method_name)
        except AttributeError:
            return
        #logger.debug("Middleware %r is processing method %s" % (self, method_name))
        await m(request, context)
        
    async def validate(self, path, permissions, method_name, request, context):
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
        logger.info("Validation: Check if validation is needed")
        if method_name not in ["CallActiveMethod", "GetObjectAttribute","SetObjectAttribute","DelObjectAttribute"]:
            return await self.__next_func(method_name,request,context)
        
        logger.info("Validation: should_perform_keycloak_validation")
        if not self.should_perform_keycloak_validation(path):
            logger.info("next func?#######################################")
            return await self.__next_func(method_name,request,context)

        logger.info("Validation: validate_permissions")
        if not self.validate_permissions(permissions):
            err = 'Insufficient permissions.'
            error = {'message': err}
            logging.warning(err)
            #return JSONResponse(error, status_code=403)


        logger.info("____________________________________________")
        return await self.__next_func(method_name,request,context)


    async def __call__(self, method_name, request, context):   
        """Middleware function which checks if the user has access to the dataset.

        Raises:
            e: MiddlewareException which depends on the validate() function:
                -If the user is not authenticated: "The user could not be authenticated"
                -If the user have no roles // doesn't have the required role: "The user '{user}' does not have the required role to access the database"

        """
        logger.info("Role validating")
        mw_context = middleware_context.get()
        path = dict(mw_context).get("path")
        permissions = dict(mw_context).get("permissions")
        try:
            #return await self.validate(dataset,user,user_roles,method_name,request,context)
            return await self.validate(path,permissions, method_name, request, context)
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
    
    
    


###############################################################################################################





