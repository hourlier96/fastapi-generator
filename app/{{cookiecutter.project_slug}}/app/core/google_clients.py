import logging

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import HttpRequest
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

from app.core.google_apis.auth.credentials import AuthType, get_credentials

DEFAULT_PEOPLE_SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/cloud-platform",
    "openid",
]
DEFAULT_DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]


class GoogleService:
    """
    Optional Parameters:
        To use with DWD authentication type
            Either use
                user_email:              (Optional) The email address of the user to impersonate.
                                                    If not specified, the identity used is the SA.
                service_account_email:   The email address of the Service account
            Or
                service_account_file:    The path to the Service account key file (not recommended)
                user_email:              The email address of the user to impersonate

        To use with OAuth2 authentication type
            oauth2_client:   The client ID and secret obtained from Google Cloud Platform
            token_file:      The path to the stored Credentials file
    """

    def __init__(
        self,
        service_name: str,
        version: str,
        scopes: list[str],
        auth_type: AuthType = AuthType.ADC,
        **kwargs
    ) -> None:
        self.service_name = service_name
        self.version = version
        self.scopes = scopes if isinstance(scopes, list) else [scopes]
        self.auth_type = auth_type
        self.creds = get_credentials(self, **kwargs)
        self.service = build(
            self.service_name,
            self.version,
            credentials=self.creds,
            cache_discovery=False,
            requestBuilder=HttpRequest,
        )

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
            TimeoutError,
            ConnectionResetError,
            ReadTimeout,
            ReadTimeoutError,
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

    def __init__(self, auth_type=AuthType.ADC, **kwargs):
        super().__init__(
            "people", "v1", scopes=DEFAULT_PEOPLE_SCOPES, auth_type=auth_type, **kwargs
        )


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

    def __init__(self, auth_type=AuthType.ADC, **kwargs):
        super().__init__("drive", "v3", scopes=DEFAULT_DRIVE_SCOPES, auth_type=auth_type, **kwargs)
