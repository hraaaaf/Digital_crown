"""Digital Crown backend package.

Extension models that share ``models.Base`` are imported here so they are registered in
SQLAlchemy metadata before startup/test ``create_all`` runs.
"""
from . import models as models
from . import models_identity_p4 as _models_identity_p4  # noqa: F401
from . import models_clinical_p3 as _models_clinical_p3  # noqa: F401
from . import models_imaging_p4 as _models_imaging_p4  # noqa: F401
