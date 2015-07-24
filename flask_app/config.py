__author__ = 'jiaying.lu'

__all__ = ["LOGENTRIES_TOKEN", "BUGSNAG_TOKEN", "APP_ENV"]
import os

# Settings

LOGENTRIES_TEST_TOKEN = "ccea7c69-f8ca-4b7d-a2b7-ba79bae94f43"
LOGENTRIES_PROD_TOKEN = "b483fc5d-797c-4fd9-a5e7-5ecbe3c7ea29"
LOGENTRIES_LOCAL_TOKEN = "ccea7c69-f8ca-4b7d-a2b7-ba79bae94f43"

BUGSNAG_TEST_TOKEN = "c0594651935c34e9b02c992498702774"
BUGSNAG_PROD_TOKEN = "f280eb475711ed313b0fc139d11dd7ab"
BUGSNAG_LOCAL_TOKEN = "c0594651935c34e9b02c992498702774"

LOGENTRIES_TOKEN = ""
BUGSNAG_TOKEN = ""
APP_ENV = ""

# Configuration

try:
    APP_ENV = os.environ["APP_ENV"]
except KeyError, key:
    print("KeyError: There is no env var named %s" % key)
    print("The local env will be applied")
    APP_ENV = "local"
finally:
    if APP_ENV == "test":
        LOGENTRIES_TOKEN = LOGENTRIES_TEST_TOKEN
        BUGSNAG_TOKEN = BUGSNAG_TEST_TOKEN
    elif APP_ENV == "prod":
        LOGENTRIES_TOKEN = LOGENTRIES_PROD_TOKEN
        BUGSNAG_TOKEN = BUGSNAG_PROD_TOKEN
    elif APP_ENV == "local":
        LOGENTRIES_TOKEN = LOGENTRIES_LOCAL_TOKEN
        BUGSNAG_TOKEN = BUGSNAG_LOCAL_TOKEN
    else:
        LOGENTRIES_TOKEN = LOGENTRIES_LOCAL_TOKEN
        BUGSNAG_TOKEN = BUGSNAG_LOCAL_TOKEN
