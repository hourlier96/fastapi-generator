import logging
import socket

import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from googleapiclient.http import HttpRequest

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import requests
from requests.exceptions import ReadTimeout
from tenacity import (
    RetryError,
    TryAgain,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)
from urllib3.exceptions import ReadTimeoutError

DEFAULT_PEOPLE_SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
]
DEFAULT_DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]


class GoogleService:
    def __init__(
        self,
        service_name: str,
        version: str,
        scopes: list[str],
        credentials_path: str = "credentials.json",
        token_path: str = "token.json",
    ) -> None:
        self.service_name = service_name
        self.version = version
        self.scopes = scopes if isinstance(scopes, list) else [scopes]
        # OAuth client path file
        self.credentials_path = credentials_path
        # Stored token
        self.token_path = token_path
        self.creds = self.get_credentials()
        self.service = build(
            self.service_name,
            self.version,
            credentials=self.creds,
            cache_discovery=False,
            requestBuilder=HttpRequest,
        )

    def get_credentials(self, needs_refresh=False) -> Credentials:
        creds = None
        if needs_refresh:
            os.remove(self.token_path)
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.scopes)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.scopes
                )
                creds = flow.run_local_server(port=0)
            with open(self.token_path, "w") as token:
                token.write(creds.to_json())
        return creds

    def get(self):
        return self.service

    @retry(
        retry=retry_if_exception_type(TryAgain),
        stop=stop_after_attempt(10),
        wait=wait_random_exponential(multiplier=1, min=2, max=256),
    )
    def make_call(self, request):
        """
        Wrapper around a Google API request with error handling.

        Instead of building a `request` from a Google Service,
        calling `execute()` and handling errors from each method,
        call `self.make_call(request)` and benefit from error handling
        in one place.
        """
        try:
            return request.execute()
        except RetryError:
            # all attempts failed, we give up
            raise Exception("API quota error")
        except (
            ConnectionResetError,
            ReadTimeout,
            ReadTimeoutError,
            socket.timeout,
            BrokenPipeError,
        ):
            raise TryAgain
        except HttpError as e:
            if e.resp.status in [300, 429, 500, 502, 503, 504]:
                raise TryAgain

            msg: str = str(e).lower()

            # Vicious API error disguised as 403
            if (
                e.resp.status == 403
                and "exceeded" in msg
                and "teamdrive" not in msg
                and "file limit for this shared drive" not in msg
            ):
                raise TryAgain

            logging.exception(e)
            raise e
        except RefreshError:
            self.get_credentials(True)
            self.make_call(request)
        except Exception as e:
            logging.exception(e)
            raise Exception("Unknown error, see logs.")


class PeopleService(GoogleService):
    """
    Use the service with utils

    Example:
        client = PeopleService()
        resp = PeopleUtils.me(client)
    """

    def __init__(self):
        super().__init__("people", "v1", scopes=DEFAULT_PEOPLE_SCOPES)


class DriveService(GoogleService):
    """
    Use the service with utils

    Example:
        client = DriveService()
        resp = DriveUtils.get_file(
            client,
            file_id="<file_id>"
        )
    """

    def __init__(self):
        super().__init__("drive", "v3", scopes=DEFAULT_DRIVE_SCOPES)
