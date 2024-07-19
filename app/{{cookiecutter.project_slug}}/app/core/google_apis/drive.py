from app.core.google_clients import DriveService

DRIVE_DEFAULT_FIELDS = "kind,id,name,mimeType,webViewLink,iconLink,modifiedTime,driveId"

GOOGLE_DOCS_MIMETYPE = "application/vnd.google-apps.document"
GOOGLE_SHEETS_MIMETYPE = "application/vnd.google-apps.spreadsheet"
GOOGLE_SLIDES_MIMETYPE = "application/vnd.google-apps.presentation"


class DriveUtils:
    @staticmethod
    def get_file(client: DriveService, file_id: str, fields: str = DRIVE_DEFAULT_FIELDS):
        return client.make_call(
            client.get().files().get(fileId=file_id, supportsAllDrives=True, fields=fields)
        )

    @staticmethod
    def create_file(client: DriveService, filename: str, parentFolderId, mimeType):
        file_metadata = {
            "name": filename,
            "parents": [parentFolderId],
            "mimeType": mimeType,
        }
        return client.make_call(
            client.get()
            .files()
            .create(
                body=file_metadata,
                supportsAllDrives=True,
            )
        )
