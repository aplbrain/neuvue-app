from django.conf import settings
from neuvueclient import NeuvueQueue


class NeuvueClient:

    # Class variable means that client is accessible without instantiating class at all
    client = NeuvueQueue(settings.NEUVUE_QUEUE_ADDR, **settings.NEUVUE_CLIENT_SETTINGS)

    # Make sure class is only instantiated once if at all
    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(NeuvueClient, cls).__new__(cls)
        return cls.instance


# Export class variable from file as well to make code pretty
client = NeuvueClient.client
