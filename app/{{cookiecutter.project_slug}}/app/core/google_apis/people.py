from app.core.google_clients import PeopleService


class PeopleUtils:
    @staticmethod
    def me(client: PeopleService):
        return client.make_call(
            client.get()
            .people()
            .get(resourceName="people/me", personFields="names,emailAddresses")
        )
