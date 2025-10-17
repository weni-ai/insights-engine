import time
import logging

import requests


logger = logging.getLogger(__name__)


def request_with_retry(
    url: str,
    headers: dict,
    params: dict,
    method: str,
    timeout: int = 60,
    max_retries: int = 3,
) -> dict:
    """
    Make a request with retry.
    """

    wait_time = 1

    for retry in range(max_retries):
        try:
            response = requests.request(
                method, url, headers=headers, params=params, timeout=timeout
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            if retry == max_retries - 1:
                logger.error(f"Error making request: {e}")
                raise e

            time.sleep(wait_time)
            wait_time *= 2
            logger.error(f"Error making request: {e}. Retrying in {wait_time} seconds.")
