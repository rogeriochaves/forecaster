import os
import sentry_sdk

APP_ENV = os.environ.get('APP_ENV', 'dev')

if APP_ENV == 'prod':
    sentry_sdk.init(
        "https://a510c31a6fcb4ed4b84cba4b8064372d@o378045.ingest.sentry.io/5735160",
        traces_sample_rate=1.0
    )
