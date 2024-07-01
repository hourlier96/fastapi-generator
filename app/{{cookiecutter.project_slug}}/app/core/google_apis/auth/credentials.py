import os

from google.oauth2 import service_account
from google.auth import default, transport
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google_auth_plugins import dwd_credentials

from enum import Enum


class AuthType(Enum):
    ADC = 1
    DWD = 2
    OAUTH2 = 3


def get_credentials(service, *args, **kwargs) -> Credentials:
    """
    Obtains user credentials for accessing a service based on the authentication type.

    Required Parameters:
        service: The service object which contains information about the authentication type.

    Optional Parameters:
        To use with DWD authentication type
            user_email:              The email address of the user to impersonate.
            service_account_email:   The email address of the Service account
            service_account_file:    The path to the Service account key file.

        To use with OAuth2 authentication type
            oauth2_client:   The client ID and secret obtained from Google Cloud Platform
            token_file:      The path to the stored Credentials file

    Returns:
        Credentials: The credentials required to access the service.
    """
    match service.auth_type:
        case AuthType.ADC:
            return __get_adc_credentials(*args, **kwargs)
        case AuthType.DWD:
            return __get_dwd_credentials(service, *args, **kwargs)
        case AuthType.OAUTH2:
            return __get_oauth_credentials(service, *args, **kwargs)
        case _:
            raise ValueError(f"Authentication type not currently managed: {service.auth_type}")


def __get_adc_credentials() -> Credentials:
    """
    Remember to pass scopes when logging with ADC
    Ex: gcloud auth application-default login --scopes="https://www.googleapis.com/auth/userinfo.profile,https://www.googleapis.com/auth/cloud-platform
    """
    credentials, _ = default()
    if credentials.expired or not credentials.valid:
        credentials.refresh(transport.requests.Request())
    return credentials


def __get_dwd_credentials(
    service, user_email=None, service_account_email=None, service_account_file=None
) -> Credentials:
    """
    Impersonate service account to access a specific service

    service_account_file SHOULD NOT BE USED if possible
    """
    if not user_email:
        raise ValueError("User email not specified, can't proceed DWD")

    # Get from SA key
    if service_account_file:
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=service.scopes
        )
        return credentials.with_subject(user_email)

    if not service_account_email:
        raise ValueError("Service account email not specified, can't proceed DWD without SA key")

    # Impersonate user without the need of Service Account key
    # Requires Service Account Token Creator on the ADC's account owner
    return dwd_credentials.Credentials(
        subject=user_email,
        source_credentials=__get_adc_credentials(service),
        target_principal=service_account_email,
        target_scopes=service.scopes,
    )


def __get_oauth_credentials(
    service, oauth2_client="credentials.json", token_file="token.json", needs_refresh=False
) -> Credentials:
    """
    Server to Server usage
    Uses OAuth client to prompt user and obtain credentials
    Stores the credentials locally
    """
    creds = None
    if needs_refresh:
        os.remove(token_file)
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, service.scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(oauth2_client, service.scopes)
            creds = flow.run_local_server(port=0)
        with open(token_file, "w") as token:
            token.write(creds.to_json())
    return creds
