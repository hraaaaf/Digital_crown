# V1-07 Interactive Evidence Registry

Status: WORKING REGISTRY — NOT A COVERAGE PERCENTAGE

This registry links audit gates to behavioral proof families. It does not freeze the semantic denominator.

| Gate | Domain | Primary behavioral proof families | Current gate state |
|---|---|---|---|
| G1 | Shell/auth/onboarding | Login, Register, Landing, ActivateTrial, PublicNavigation, SetupWizard, OnboardingScanner, Sidebar, Header, MainLayout | functional proof present; exact-head CI pending |
| G2 | Dashboard/patients/dossier | DashboardInteractions, DashboardPage, PatientList, PatientListSearchSort, CsvImportModal, Add/Edit patient + variants, PatientDossierNumber, PatientDetails | functional proof present; exact-head CI pending |
| G3 | Agenda/frontdesk/notifications | AgendaStudio, AgendaModal, AgendaModalSecondary, FrontdeskModal, PendingRequestCard, GoogleImportModal, AgendaView, FrontdeskView, NotificationsView, WaitingRoomView | functional proof present; exact-head CI pending |
| G4 | Deep clinical/business | DocumentStudioShell, PrescriptionForm, CertificateLibre, DevisOdontogram, Honoraires, InstallmentStudio, DocumentGeneration, PatientFinances, Payments, ClinicalHubCore, ClinicalWizards, RVG, PanoramicStudio, CephaloWorkspace | functionally reconciled; exact-head CI pending |
| G5 | Cabinet/settings/team | SettingsContainer, ProfileTab, BrandingTab, CatalogTab, AgendaTab, IATab, SecurityTab, ClinicPractitionerBar, TeamManager LOT2 matrix | functionally reconciled; exact-head CI pending |
| G6 | SuperAdmin/licences | SuperAdmin pack matrix, trial codes, LicenseStatusPage | code remediated; visual + CI pending |
| G7 | Stock/marketplace/library | StockPage, PartnerMarketplacePage, PartnerDetailPages, PartnerCatalogAdminPage, marketplace hook, EliteLibrary, EliteScienceHub | code remediated; visual + CI pending |
| G8 | Transverse/adversarial | CrownDialog, OfflineQueueViewer, responsive contracts, CriticalMutationSingleFlight, cross-gate refusal/error/permission proofs | functionally reconciled; exact-head CI pending |

## Denominator freeze rule
The final denominator is not the number of files, tests, buttons, or raw static signals.

A semantic control is one distinct user action + business-result contract in a defined state/context.

Examples:
- a shared "Supprimer" component used for patient and stock deletion counts as different semantic controls when the business boundary and refusal behavior differ;
- one button with onClick + API mutation + toast is one semantic control, not three;
- a visible control and a forced deep-link permission bypass are separate contracts when both can change reachable behavior.

## Final G9 reconciliation inputs
- final G0 inventory artifact;
- this registry;
- canonical G1→G8 files;
- exact-head test/build outcome;
- required visual/runtime artifacts;
- explicit blockers/non-applicable rationales.

No global completion percentage may be published until these inputs are reconciled on the final candidate.
