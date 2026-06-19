from documenteer.conf.guide import *

# Override documenteer's default ReDoc bundle URL. Documenteer points
# ``redoc_uri`` at the ``redoc@next`` dist-tag on jsDelivr, which upstream has
# removed (it now 404s and fails the docs build). Pin to a working release so
# the OpenAPI page renders.
redoc_uri = "https://cdn.jsdelivr.net/npm/redoc@2.5.0/bundles/redoc.standalone.js"  # noqa: E501,F405
