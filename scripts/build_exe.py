"""Legacy builder quarantine.

P6 makes DigitalCrown.spec the only production packaging authority.
This file stays as an explicit trap for old runbooks/scripts that still invoke it.
"""
raise SystemExit(
    "LEGACY_BUILDER_DISABLED: use the P6 packaging workflow / DigitalCrown.spec. "
    "The former script could bundle secrets and divergent runtime assets."
)
