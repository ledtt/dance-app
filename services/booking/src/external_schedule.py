# services/booking/external_schedule.py

import json
import httpx
import structlog
from typing import Union, Optional
from .service_auth import service_token_manager
from .config import settings

logger = structlog.get_logger()

async def get_class_template_by_id(class_id: str) -> Union[dict, None]:
    """Get class template information from schedule service"""
    try:
        # Get service token
        service_token = await service_token_manager.get_service_token()
        
        async with httpx.AsyncClient(timeout=15.0) as client: 
            headers = {"Authorization": f"Bearer {service_token}"}
            resp = await client.get(f"{settings.schedule_service_url}/schedule/{class_id}", headers=headers)
            
            if resp.status_code == 200:
                try:
                    return resp.json()
                except json.JSONDecodeError:
                    logger.error("Failed to decode JSON response from schedule-service", 
                               class_id=class_id, response_text=resp.text[:200])
                    return None
            elif resp.status_code == 404:
                logger.warning("Class not found in schedule service", class_id=class_id)
                return None
            else:
                logger.error("Unexpected status code from schedule service", 
                           class_id=class_id, status_code=resp.status_code, response_text=resp.text[:200])
                return None
    except httpx.TimeoutException:
        logger.error("Timeout when calling schedule service", class_id=class_id)
        return None
    except httpx.ConnectError:
        logger.error("Connection error when calling schedule service", class_id=class_id)
        return None
    except httpx.RequestError as e:
        logger.error("Request error when calling schedule service", class_id=class_id, error=str(e))
        return None
    except (ValueError, TypeError, ConnectionError) as e:
        logger.error("Unexpected error when calling schedule service", class_id=class_id, error=str(e))
        return None


async def get_user_by_id(user_id: str) -> Union[dict, None]:
    """Get user information from auth service"""
    try:
        # Get service token
        service_token = await service_token_manager.get_service_token()
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            headers = {"Authorization": f"Bearer {service_token}"}
            resp = await client.get(f"{settings.auth_service_url}/auth/internal/users/{user_id}", headers=headers)
            
            if resp.status_code == 200:
                try:
                    return resp.json()
                except json.JSONDecodeError:
                    logger.error("Failed to decode JSON response from auth-service", 
                               user_id=user_id, response_text=resp.text[:200])
                    return None
            elif resp.status_code == 404:
                logger.warning("User not found in auth service", user_id=user_id)
                return None
            else:
                logger.error("Unexpected status code from auth service", 
                           user_id=user_id, status_code=resp.status_code, response_text=resp.text[:200])
                return None
    except httpx.TimeoutException:
        logger.error("Timeout when calling auth service", user_id=user_id)
        return None
    except httpx.ConnectError:
        logger.error("Connection error when calling auth service", user_id=user_id)
        return None
    except httpx.RequestError as e:
        logger.error("Request error when calling auth service", user_id=user_id, error=str(e))
        return None
    except (ValueError, TypeError, ConnectionError) as e:
        logger.error("Unexpected error when calling auth service", user_id=user_id, error=str(e))
        return None


async def get_class_ids_by_filter(teacher: Optional[str] = None, name: Optional[str] = None) -> Union[list[str], None]:
    """Get class IDs filtered by teacher and/or name from schedule service"""
    try:
        logger.info("Getting class IDs by filter", teacher=teacher, name=name)
        
        # Get service token
        service_token = await service_token_manager.get_service_token()
        logger.info("Service token obtained", token_length=len(service_token) if service_token else 0)
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Build query parameters
            params = {}
            if teacher:
                params['teacher'] = teacher
            if name:
                params['name'] = name
            
            headers = {"Authorization": f"Bearer {service_token}"}
            logger.info("Making request to schedule service", 
                       url=f"{settings.schedule_service_url}/schedule/ids",
                       params=params, headers_keys=list(headers.keys()))
            
            resp = await client.get(f"{settings.schedule_service_url}/schedule/ids", params=params, headers=headers)
            
            logger.info("Response received from schedule service", 
                       status_code=resp.status_code, 
                       response_headers=dict(resp.headers))
            
            if resp.status_code == 200:
                try:
                    result = resp.json()
                    logger.info("Successfully decoded response", result_type=type(result).__name__)
                    return result
                except json.JSONDecodeError:
                    logger.error("Failed to decode JSON response from schedule-service", 
                               response_text=resp.text[:200])
                    return None
            else:
                logger.error("Unexpected status code from schedule service", 
                           status_code=resp.status_code, response_text=resp.text[:200])
                return None
    except httpx.TimeoutException:
        logger.error("Timeout when calling schedule service for class IDs")
        return None
    except httpx.ConnectError:
        logger.error("Connection error when calling schedule service for class IDs")
        return None
    except httpx.RequestError as e:
        logger.error("Request error when calling schedule service for class IDs", error=str(e))
        return None
    except (ValueError, TypeError, ConnectionError) as e:
        logger.error("Unexpected error when calling schedule service for class IDs", error=str(e), error_type=type(e).__name__)
        return None
