"""Digital Crown backend package.

Extension models that share ``models.Base`` are imported here so they are registered in
SQLAlchemy metadata before startup/test ``create_all`` runs.
"""
from . import models as models
from . import models_identity_p4 as _models_identity_p4  # noqa: F401
from . import models_clinical_p3 as _models_clinical_p3  # noqa: F401
from . import models_imaging_p4 as _models_imaging_p4  # noqa: F401
from . import models_media_core as _models_media_core  # noqa: F401
from . import models_appointments_p0 as _models_appointments_p0  # noqa: F401
from . import models_ngap_reference as _models_ngap_reference  # noqa: F401
from .models_insurance_linkage import install_insurance_linkage
from .services.honoraires_archive_conflict_policy import install_honoraires_archive_conflict_policy

install_insurance_linkage()
install_honoraires_archive_conflict_policy()
