from datetime import date

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.policies.models import Policy, PolicyStatus, PolicyType
from apps.projects.models import (
    AllocationType,
    BudgetAllocation,
    Institution,
    InstitutionType,
    Project,
    ProjectCategory,
    ProjectStatus,
    TimelineEvent,
    TimelineStage,
)
from apps.sources.extraction import make_simple_docx, make_simple_pdf, make_simple_xlsx
from apps.sources.models import (
    DocumentType,
    Evidence,
    EvidenceVerificationStatus,
    SourceDocument,
    VerificationLevel,
)


class Command(BaseCommand):
    help = "Load labelled fictional demo data for TheHydra MVP."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing demo records before loading.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            Policy.objects.filter(is_demo=True).delete()
            Project.objects.filter(is_demo=True).delete()
            Institution.objects.filter(name__contains="[DEMO]").delete()
            SourceDocument.objects.filter(is_demo=True).delete()
            self.stdout.write("Removed previous demo records.")

        institutions = self._institutions()
        documents = self._documents()
        self._attach_demo_files(documents)
        self._projects(institutions, documents)
        self._policies(institutions, documents)
        self.stdout.write(self.style.SUCCESS("Demo data loaded. Records are labelled as demo / fictional."))

    def _institutions(self):
        specs = [
            {
                "slug": "kisumu-water-demo",
                "name": "[DEMO] Kisumu County Department of Water",
                "description": "Fictional county water department used only for TheHydra demonstrations.",
                "institution_type": InstitutionType.COUNTY_DEPARTMENT,
                "location": "Kisumu, Kenya",
                "website": "https://example.go.ke/kisumu-water-demo",
            },
            {
                "slug": "siaya-energy-demo",
                "name": "[DEMO] Siaya County Energy Office",
                "description": "Fictional energy office for demonstration projects.",
                "institution_type": InstitutionType.COUNTY_DEPARTMENT,
                "location": "Siaya, Kenya",
            },
            {
                "slug": "western-health-demo",
                "name": "[DEMO] Western Region Health Works Unit",
                "description": "Fictional health works unit. Not a real institution.",
                "institution_type": InstitutionType.AGENCY,
                "location": "Kakamega, Kenya",
            },
            {
                "slug": "nyanza-works-demo",
                "name": "[DEMO] Nyanza Public Works Desk",
                "description": "Fictional public works coordination desk for demo records.",
                "institution_type": InstitutionType.COUNTY_DEPARTMENT,
                "location": "Kisii, Kenya",
            },
            {
                "slug": "lakeside-education-demo",
                "name": "[DEMO] Lakeside Education Infrastructure Office",
                "description": "Fictional education infrastructure office.",
                "institution_type": InstitutionType.COUNTY_DEPARTMENT,
                "location": "Homa Bay, Kenya",
            },
            {
                "slug": "dar-water-demo",
                "name": "[DEMO] Dar es Salaam Water and Sanitation Desk",
                "description": "Fictional regional water desk used only for TheHydra demonstrations.",
                "institution_type": InstitutionType.AGENCY,
                "location": "Dar es Salaam, Tanzania",
            },
            {
                "slug": "mwanza-works-demo",
                "name": "[DEMO] Mwanza Regional Works Office",
                "description": "Fictional regional works office. Not a real institution.",
                "institution_type": InstitutionType.AGENCY,
                "location": "Mwanza, Tanzania",
            },
            {
                "slug": "dodoma-health-demo",
                "name": "[DEMO] Dodoma Regional Health Works Unit",
                "description": "Fictional health works unit for demonstration records.",
                "institution_type": InstitutionType.AGENCY,
                "location": "Dodoma, Tanzania",
            },
            {
                "slug": "bujumbura-water-demo",
                "name": "[DEMO] Bujumbura Water Service Desk",
                "description": "Fictional provincial water desk used only for demonstrations.",
                "institution_type": InstitutionType.AGENCY,
                "location": "Bujumbura, Burundi",
            },
            {
                "slug": "gitega-education-demo",
                "name": "[DEMO] Gitega Communal Education Office",
                "description": "Fictional communal education office. Not a real institution.",
                "institution_type": InstitutionType.AGENCY,
                "location": "Gitega, Burundi",
            },
            {
                "slug": "burunga-agriculture-demo",
                "name": "[DEMO] Burunga Agriculture Works Desk",
                "description": "Fictional agriculture works desk for demo irrigation records.",
                "institution_type": InstitutionType.AGENCY,
                "location": "Rumonge, Burundi",
            },
            {
                "slug": "kinshasa-works-demo",
                "name": "[DEMO] Kinshasa Urban Drainage Desk",
                "description": "Fictional provincial works desk used only for demonstrations.",
                "institution_type": InstitutionType.AGENCY,
                "location": "Kinshasa, Democratic Republic of the Congo",
            },
            {
                "slug": "nord-kivu-health-demo",
                "name": "[DEMO] Nord-Kivu Health Infrastructure Unit",
                "description": "Fictional provincial health infrastructure unit.",
                "institution_type": InstitutionType.AGENCY,
                "location": "Goma, Democratic Republic of the Congo",
            },
            {
                "slug": "haut-katanga-markets-demo",
                "name": "[DEMO] Haut-Katanga Markets Office",
                "description": "Fictional markets office. Not a real institution.",
                "institution_type": InstitutionType.AGENCY,
                "location": "Lubumbashi, Democratic Republic of the Congo",
            },
            {
                "slug": "lagos-health-demo",
                "name": "[DEMO] Lagos State Primary Health Works Unit",
                "description": "Fictional state health works unit used only for demonstrations.",
                "institution_type": InstitutionType.AGENCY,
                "location": "Ikeja, Lagos, Nigeria",
            },
            {
                "slug": "kano-roads-demo",
                "name": "[DEMO] Kano State Urban Roads Desk",
                "description": "Fictional state roads desk. Not a real institution.",
                "institution_type": InstitutionType.AGENCY,
                "location": "Kano, Nigeria",
            },
            {
                "slug": "rivers-education-demo",
                "name": "[DEMO] Rivers State School Infrastructure Office",
                "description": "Fictional school infrastructure office for demo records.",
                "institution_type": InstitutionType.AGENCY,
                "location": "Port Harcourt, Nigeria",
            },
        ]
        created = {}
        for spec in specs:
            obj, _ = Institution.objects.update_or_create(slug=spec["slug"], defaults=spec)
            created[spec["slug"]] = obj
        return created

    def _documents(self):
        specs = [
            {
                "key": "kisumu-budget",
                "title": "[DEMO] Kisumu County Development Budget 2025/26 — Water Annex",
                "publisher": "Fictional Kisumu County Treasury (demo)",
                "document_type": DocumentType.BUDGET,
                "publication_date": date(2025, 6, 18),
                "description": "Demo budget annex used to evidence a water project allocation. Not an official document.",
                "verification_level": VerificationLevel.OFFICIAL,
                "source_url": "https://example.go.ke/demo/kisumu-budget-2025-26",
            },
            {
                "key": "water-tender",
                "title": "[DEMO] Tender notice: Community Water Access Project",
                "publisher": "Fictional Kisumu Procurement Portal (demo)",
                "document_type": DocumentType.TENDER,
                "publication_date": date(2025, 8, 4),
                "description": "Demo tender notice.",
                "verification_level": VerificationLevel.OFFICIAL,
            },
            {
                "key": "water-contract",
                "title": "[DEMO] Contract award notice — Community Water Access",
                "publisher": "Fictional Kisumu Procurement Portal (demo)",
                "document_type": DocumentType.CONTRACT,
                "publication_date": date(2025, 10, 9),
                "description": "Demo contract award notice naming a fictional contractor.",
                "verification_level": VerificationLevel.VERIFIED,
            },
            {
                "key": "water-progress",
                "title": "[DEMO] Quarterly implementation report Q1 2026",
                "publisher": "Fictional Department of Water (demo)",
                "document_type": DocumentType.PROJECT_REPORT,
                "publication_date": date(2026, 3, 31),
                "description": "Demo progress report stating 60% completion.",
                "verification_level": VerificationLevel.VERIFIED,
            },
            {
                "key": "siaya-budget",
                "title": "[DEMO] Siaya energy development estimates 2025/26",
                "publisher": "Fictional Siaya Treasury (demo)",
                "document_type": DocumentType.BUDGET,
                "publication_date": date(2025, 6, 12),
                "verification_level": VerificationLevel.OFFICIAL,
            },
            {
                "key": "market-audit",
                "title": "[DEMO] Internal comparison note on market works",
                "publisher": "Fictional oversight note (demo)",
                "document_type": DocumentType.AUDIT,
                "publication_date": date(2026, 1, 20),
                "description": "Demo note that records a different amount from the budget annex.",
                "verification_level": VerificationLevel.UNVERIFIED,
            },
            {
                "key": "market-budget",
                "title": "[DEMO] Kisii markets development annex 2024/25",
                "publisher": "Fictional Kisii Treasury (demo)",
                "document_type": DocumentType.BUDGET,
                "publication_date": date(2024, 6, 10),
                "verification_level": VerificationLevel.OFFICIAL,
            },
            {
                "key": "access-policy",
                "title": "[DEMO] County access to project information note",
                "publisher": "Fictional Nyanza Public Works Desk (demo)",
                "document_type": DocumentType.POLICY,
                "publication_date": date(2024, 11, 2),
                "verification_level": VerificationLevel.OFFICIAL,
            },
            {
                "key": "dar-water-budget",
                "title": "[DEMO] Dar es Salaam water development estimates 2025/26",
                "publisher": "Fictional Dar es Salaam Water Desk (demo)",
                "document_type": DocumentType.BUDGET,
                "publication_date": date(2025, 5, 20),
                "description": "Demo estimates used to evidence a piped water extension. Not an official document.",
                "verification_level": VerificationLevel.OFFICIAL,
            },
            {
                "key": "dar-water-tender",
                "title": "[DEMO] Tender notice: Kigamboni Piped Water Extension",
                "publisher": "Fictional Dar es Salaam procurement board (demo)",
                "document_type": DocumentType.TENDER,
                "publication_date": date(2025, 7, 14),
                "verification_level": VerificationLevel.OFFICIAL,
            },
            {
                "key": "mwanza-road-budget",
                "title": "[DEMO] Mwanza regional roads annex 2025/26",
                "publisher": "Fictional Mwanza Works Office (demo)",
                "document_type": DocumentType.BUDGET,
                "publication_date": date(2025, 6, 2),
                "verification_level": VerificationLevel.OFFICIAL,
            },
            {
                "key": "bujumbura-water-budget",
                "title": "[DEMO] Bujumbura water service estimates 2025",
                "publisher": "Fictional Bujumbura Water Service Desk (demo)",
                "document_type": DocumentType.BUDGET,
                "publication_date": date(2025, 3, 12),
                "verification_level": VerificationLevel.OFFICIAL,
            },
            {
                "key": "gitega-sanitation-note",
                "title": "[DEMO] Gitega school sanitation implementation note",
                "publisher": "Fictional Gitega Education Office (demo)",
                "document_type": DocumentType.PROJECT_REPORT,
                "publication_date": date(2025, 9, 1),
                "verification_level": VerificationLevel.UNVERIFIED,
            },
            {
                "key": "kinshasa-drainage-budget",
                "title": "[DEMO] Kinshasa urban drainage estimates 2025",
                "publisher": "Fictional Kinshasa Urban Drainage Desk (demo)",
                "document_type": DocumentType.BUDGET,
                "publication_date": date(2025, 4, 8),
                "verification_level": VerificationLevel.OFFICIAL,
            },
            {
                "key": "goma-clinic-progress",
                "title": "[DEMO] Goma clinic water connection site note",
                "publisher": "Fictional Nord-Kivu Health Unit (demo)",
                "document_type": DocumentType.PROJECT_REPORT,
                "publication_date": date(2026, 1, 15),
                "verification_level": VerificationLevel.UNVERIFIED,
            },
            {
                "key": "lubumbashi-market-budget",
                "title": "[DEMO] Lubumbashi market lighting annex 2024",
                "publisher": "Fictional Haut-Katanga Markets Office (demo)",
                "document_type": DocumentType.BUDGET,
                "publication_date": date(2024, 11, 4),
                "verification_level": VerificationLevel.OFFICIAL,
            },
            {
                "key": "lubumbashi-market-note",
                "title": "[DEMO] Internal comparison note on market lighting",
                "publisher": "Fictional oversight note (demo)",
                "document_type": DocumentType.AUDIT,
                "publication_date": date(2025, 2, 18),
                "description": "Demo note that records a different amount from the budget annex.",
                "verification_level": VerificationLevel.UNVERIFIED,
            },
            {
                "key": "lagos-phc-budget",
                "title": "[DEMO] Lagos State primary health capital estimates 2025",
                "publisher": "Fictional Lagos State Health Works Unit (demo)",
                "document_type": DocumentType.BUDGET,
                "publication_date": date(2025, 1, 22),
                "verification_level": VerificationLevel.OFFICIAL,
            },
            {
                "key": "lagos-phc-contract",
                "title": "[DEMO] Contract award notice — Ikeja Primary Health Centre Extension",
                "publisher": "Fictional Lagos procurement portal (demo)",
                "document_type": DocumentType.CONTRACT,
                "publication_date": date(2025, 6, 11),
                "verification_level": VerificationLevel.VERIFIED,
            },
            {
                "key": "kano-roads-budget",
                "title": "[DEMO] Kano State neighbourhood roads estimates 2025",
                "publisher": "Fictional Kano Urban Roads Desk (demo)",
                "document_type": DocumentType.BUDGET,
                "publication_date": date(2025, 2, 9),
                "verification_level": VerificationLevel.OFFICIAL,
            },
            {
                "key": "tz-access-policy",
                "title": "[DEMO] Regional access to project information note (Tanzania)",
                "publisher": "Fictional Dar es Salaam Water Desk (demo)",
                "document_type": DocumentType.POLICY,
                "publication_date": date(2024, 10, 7),
                "verification_level": VerificationLevel.OFFICIAL,
            },
        ]
        created = {}
        for spec in specs:
            key = spec.pop("key")
            spec["is_demo"] = True
            obj, _ = SourceDocument.objects.update_or_create(title=spec["title"], defaults=spec)
            created[key] = obj
        return created

    def _attach_demo_files(self, documents):
        attachments = {
            "kisumu-budget": (
                "kisumu-water-budget.pdf",
                make_simple_pdf(
                    "Kisumu water annex. Community Water Access Project allocation 35000000 for boreholes and kiosks."
                ),
            ),
            "water-tender": (
                "community-water-tender.docx",
                make_simple_docx(
                    [
                        "Tender notice",
                        "Community Water Access Project",
                        "Works include boreholes, kiosks, and pipeline repairs in Kisumu.",
                    ]
                ),
            ),
            "siaya-budget": (
                "siaya-energy-estimates.xlsx",
                make_simple_xlsx(
                    [
                        ["Item", "Amount"],
                        ["Solar street lighting", 18000000],
                        ["Maintenance", 1200000],
                    ],
                    "Energy",
                ),
            ),
            "dar-water-budget": (
                "kigamboni-water-estimates.pdf",
                make_simple_pdf(
                    "Dar es Salaam water annex. Kigamboni Piped Water Extension allocation 4200000000 Tanzania shillings."
                ),
            ),
            "bujumbura-water-budget": (
                "mukaza-standpipes.pdf",
                make_simple_pdf(
                    "Bujumbura water estimates. Mukaza Public Standpipe Rehabilitation allocation 850000000 Burundi francs."
                ),
            ),
            "kinshasa-drainage-budget": (
                "gombe-drainage-estimates.pdf",
                make_simple_pdf(
                    "Kinshasa urban drainage annex. Gombe Drainage and Culverts allocation 12500000000 Congolese francs."
                ),
            ),
            "lagos-phc-budget": (
                "ikeja-phc-estimates.xlsx",
                make_simple_xlsx(
                    [
                        ["Item", "Amount"],
                        ["Ikeja Primary Health Centre Extension", 480000000],
                        ["Furniture", 18000000],
                    ],
                    "Health",
                ),
            ),
        }
        for key, (filename, payload) in attachments.items():
            document = documents[key]
            if document.file:
                continue
            document.original_filename = filename
            document.file.save(filename, ContentFile(payload), save=True)

    def _projects(self, institutions, documents):
        self._full_water_project(institutions, documents)
        self._partial_electrification(institutions, documents)
        self._missing_health(institutions)
        self._conflicting_market(institutions, documents)
        self._tanzania_projects(institutions, documents)
        self._burundi_projects(institutions, documents)
        self._drc_projects(institutions, documents)
        self._nigeria_projects(institutions, documents)
        others = [
            {
                "slug": "ecd-classroom-homa-bay",
                "name": "[DEMO] Early Childhood Classroom Block",
                "description": "Fictional ECD classroom project with partial documentary support.",
                "category": ProjectCategory.EDUCATION,
                "location": "Rangwe, Homa Bay County",
                "country": "KE",
                "county": "Homa Bay",
                "constituency": "Rangwe",
                "ward": "Rangwe",
                "institution": institutions["lakeside-education-demo"],
                "contractor": "Lakeside Builders Ltd (fictional)",
                "allocated_amount": 12000000,
                "financial_year": "2025/2026",
                "status": ProjectStatus.IN_PROGRESS,
                "start_date": date(2025, 9, 1),
                "expected_completion_date": date(2026, 6, 30),
            },
            {
                "slug": "road-grading-migori",
                "name": "[DEMO] Road Grading and Culvert Works",
                "description": "Fictional rural road grading project. Completion date is not evidenced.",
                "category": ProjectCategory.ROADS,
                "location": "Rongo, Migori County",
                "country": "KE",
                "county": "Migori",
                "constituency": "Rongo",
                "ward": "Rongo",
                "institution": institutions["nyanza-works-demo"],
                "contractor": "",
                "allocated_amount": 18500000,
                "financial_year": "2024/2025",
                "status": ProjectStatus.DELAYED,
                "start_date": date(2024, 11, 1),
                "expected_completion_date": date(2025, 8, 31),
            },
            {
                "slug": "sanitation-busia",
                "name": "[DEMO] Public Sanitation Facilities",
                "description": "Fictional sanitation block programme with limited source documents.",
                "category": ProjectCategory.SANITATION,
                "location": "Funyula, Busia County",
                "country": "KE",
                "county": "Busia",
                "constituency": "Funyula",
                "ward": "Funyula",
                "institution": institutions["western-health-demo"],
                "contractor": "Lakeshore Civils (fictional)",
                "allocated_amount": 6400000,
                "financial_year": "2025/2026",
                "status": ProjectStatus.PROCUREMENT,
            },
            {
                "slug": "irrigation-bungoma",
                "name": "[DEMO] Irrigation Canal Rehabilitation",
                "description": "Fictional canal lining project. Implementation evidence is unavailable.",
                "category": ProjectCategory.AGRICULTURE,
                "location": "Webuye, Bungoma County",
                "country": "KE",
                "county": "Bungoma",
                "constituency": "Webuye East",
                "ward": "Webuye East",
                "institution": institutions["nyanza-works-demo"],
                "contractor": "Valley Irrigation Co. (fictional)",
                "allocated_amount": 42000000,
                "financial_year": "2023/2024",
                "status": ProjectStatus.UNKNOWN,
            },
            {
                "slug": "polytechnic-vihiga",
                "name": "[DEMO] Youth Polytechnic Workshop",
                "description": "Fictional workshop construction with a verified allocation and unknown contractor evidence.",
                "category": ProjectCategory.EDUCATION,
                "location": "Mbale, Vihiga County",
                "country": "KE",
                "county": "Vihiga",
                "constituency": "Vihiga",
                "ward": "Mbale",
                "institution": institutions["lakeside-education-demo"],
                "contractor": "",
                "allocated_amount": 9800000,
                "financial_year": "2025/2026",
                "status": ProjectStatus.APPROVED,
                "start_date": date(2026, 1, 15),
                "expected_completion_date": date(2026, 12, 15),
            },
            {
                "slug": "waste-kisumu",
                "name": "[DEMO] Solid Waste Collection Upgrade",
                "description": "Fictional waste collection equipment purchase. Timeline is incomplete.",
                "category": ProjectCategory.SANITATION,
                "location": "Kisumu Central",
                "country": "KE",
                "county": "Kisumu",
                "constituency": "Kisumu Central",
                "ward": "Market Milimani",
                "institution": institutions["kisumu-water-demo"],
                "contractor": "Lakeside Logistics (fictional)",
                "allocated_amount": 15000000,
                "financial_year": "2025/2026",
                "status": ProjectStatus.PLANNED,
            },
        ]
        for spec in others:
            self._simple_project(spec, documents.get("access-policy"))

    def _full_water_project(self, institutions, documents):
        project, _ = Project.objects.update_or_create(
            slug="community-water-access-project",
            defaults={
                "name": "[DEMO] Community Water Access Project",
                "description": (
                    "Fictional community water project in Kisumu used for the product demo. "
                    "Official records in this dataset state an allocation of KSh 35 million "
                    "in financial year 2025/2026. All names and documents are labelled demo data."
                ),
                "category": ProjectCategory.WATER,
                "location": "Kolwa East, Kisumu County",
                "country": "KE",
                "county": "Kisumu",
                "ward": "Kolwa East",
                "constituency": "Kisumu East",
                "institution": institutions["kisumu-water-demo"],
                "contractor": "Nyanza Borehole Services Ltd (fictional)",
                "allocated_amount": 35000000,
                "currency": "KES",
                "financial_year": "2025/2026",
                "start_date": date(2025, 11, 1),
                "expected_completion_date": date(2026, 12, 15),
                "status": ProjectStatus.IN_PROGRESS,
                "is_featured": True,
                "is_demo": True,
            },
        )
        project.source_documents.set(
            [
                documents["kisumu-budget"],
                documents["water-tender"],
                documents["water-contract"],
                documents["water-progress"],
            ]
        )
        project.allocations.all().delete()
        BudgetAllocation.objects.create(
            project=project,
            financial_year="2025/2026",
            amount=35000000,
            currency="KES",
            allocation_type=AllocationType.DEVELOPMENT,
            source_document=documents["kisumu-budget"],
            notes="Original development allocation recorded in the demo budget annex.",
        )
        project.evidence_items.all().delete()
        evidence = {}
        evidence["allocation"] = Evidence.objects.create(
            project=project,
            claim="Project allocation is KSh 35 million.",
            evidence_text="The demo budget annex lists KSh 35,000,000 for the Community Water Access Project in FY 2025/26.",
            source_document=documents["kisumu-budget"],
            page_number=42,
            verification_status=EvidenceVerificationStatus.VERIFIED,
        )
        evidence["approval"] = Evidence.objects.create(
            project=project,
            claim="The project was approved for implementation in FY 2025/2026.",
            evidence_text="The demo budget annex includes the project under approved water development works.",
            source_document=documents["kisumu-budget"],
            page_number=41,
            verification_status=EvidenceVerificationStatus.VERIFIED,
        )
        evidence["tender"] = Evidence.objects.create(
            project=project,
            claim="A tender was published for the works.",
            evidence_text="Demo tender notice dated 4 August 2025 invites bids for borehole and distribution works.",
            source_document=documents["water-tender"],
            page_number=1,
            verification_status=EvidenceVerificationStatus.VERIFIED,
        )
        evidence["contract"] = Evidence.objects.create(
            project=project,
            claim="The contract was awarded to Nyanza Borehole Services Ltd (fictional).",
            evidence_text="Demo award notice names Nyanza Borehole Services Ltd as the successful bidder.",
            source_document=documents["water-contract"],
            page_number=2,
            verification_status=EvidenceVerificationStatus.VERIFIED,
        )
        evidence["progress"] = Evidence.objects.create(
            project=project,
            claim="The project is reported as 60 percent complete.",
            evidence_text="Demo Q1 2026 implementation report states physical progress at 60%.",
            source_document=documents["water-progress"],
            page_number=6,
            verification_status=EvidenceVerificationStatus.PARTIALLY_VERIFIED,
            notes="Progress is self-reported. Independent verification is not attached.",
        )
        evidence["completion"] = Evidence.objects.create(
            project=project,
            claim="Expected completion is December 2026.",
            evidence_text="Demo implementation report gives an expected completion of December 2026.",
            source_document=documents["water-progress"],
            page_number=7,
            verification_status=EvidenceVerificationStatus.VERIFIED,
        )
        evidence["unknown"] = Evidence.objects.create(
            project=project,
            claim="Water quality test results after commissioning.",
            evidence_text="",
            verification_status=EvidenceVerificationStatus.UNKNOWN,
            notes="No commissioning tests are attached because the project is not recorded as complete.",
        )
        self._replace_timeline(
            project,
            [
                (TimelineStage.ALLOCATION, "KSh 35M allocated", "Development allocation for FY 2025/2026.", 35000000, date(2025, 6, 18), evidence["allocation"], 1),
                (TimelineStage.APPROVAL, "Approved in county estimates", "Listed under approved water development works.", None, date(2025, 6, 18), evidence["approval"], 2),
                (TimelineStage.PROCUREMENT, "Tender published", "Open tender for borehole and distribution works.", None, date(2025, 8, 4), evidence["tender"], 3),
                (TimelineStage.CONTRACT, "Contract awarded", "Award notice names a fictional contractor.", None, date(2025, 10, 9), evidence["contract"], 4),
                (TimelineStage.IMPLEMENTATION, "Reported as 60% complete", "Self-reported physical progress in Q1 2026.", None, date(2026, 3, 31), evidence["progress"], 5),
                (TimelineStage.COMPLETION, "Expected December 2026", "Expected completion date; actual completion is not recorded.", None, date(2026, 12, 15), evidence["completion"], 6),
            ],
        )

    def _partial_electrification(self, institutions, documents):
        project, _ = Project.objects.update_or_create(
            slug="rural-electrification-extension",
            defaults={
                "name": "[DEMO] Rural Electrification Extension",
                "description": "Fictional last-mile electricity extension. Allocation is evidenced; procurement evidence is unavailable.",
                "category": ProjectCategory.ENERGY,
                "location": "Ugunja, Siaya County",
                "country": "KE",
                "county": "Siaya",
                "constituency": "Ugunja",
                "ward": "Ugunja",
                "institution": institutions["siaya-energy-demo"],
                "contractor": "",
                "allocated_amount": 22000000,
                "financial_year": "2025/2026",
                "status": ProjectStatus.PROCUREMENT,
                "is_featured": False,
                "is_demo": True,
                "start_date": date(2025, 10, 1),
                "expected_completion_date": date(2026, 9, 30),
            },
        )
        project.source_documents.set([documents["siaya-budget"]])
        project.allocations.all().delete()
        BudgetAllocation.objects.create(
            project=project,
            financial_year="2025/2026",
            amount=22000000,
            allocation_type=AllocationType.DEVELOPMENT,
            source_document=documents["siaya-budget"],
        )
        project.evidence_items.all().delete()
        alloc = Evidence.objects.create(
            project=project,
            claim="Allocation is KSh 22 million.",
            evidence_text="Demo Siaya energy estimates list KSh 22,000,000 for rural extension.",
            source_document=documents["siaya-budget"],
            page_number=18,
            verification_status=EvidenceVerificationStatus.VERIFIED,
        )
        Evidence.objects.create(
            project=project,
            claim="A contractor has been appointed.",
            evidence_text="",
            verification_status=EvidenceVerificationStatus.UNKNOWN,
        )
        self._replace_timeline(
            project,
            [
                (TimelineStage.ALLOCATION, "KSh 22M allocated", "", 22000000, date(2025, 6, 12), alloc, 1),
                (TimelineStage.APPROVAL, "Listed in estimates", "", None, date(2025, 6, 12), alloc, 2),
                (TimelineStage.PROCUREMENT, "Procurement stage recorded", "No tender document is attached.", None, None, None, 3),
            ],
        )

    def _missing_health(self, institutions):
        project, _ = Project.objects.update_or_create(
            slug="county-health-centre-upgrade",
            defaults={
                "name": "[DEMO] County Health Centre Upgrade",
                "description": "Fictional health centre upgrade with almost no attached evidence. Status is unknown.",
                "category": ProjectCategory.HEALTH,
                "location": "Lurambi, Kakamega County",
                "country": "KE",
                "county": "Kakamega",
                "constituency": "Lurambi",
                "ward": "Lurambi",
                "institution": institutions["western-health-demo"],
                "contractor": "",
                "allocated_amount": None,
                "financial_year": "",
                "status": ProjectStatus.UNKNOWN,
                "is_featured": False,
                "is_demo": True,
            },
        )
        project.source_documents.clear()
        project.allocations.all().delete()
        project.evidence_items.all().delete()
        Evidence.objects.create(
            project=project,
            claim="Works have started on the maternity wing.",
            evidence_text="",
            verification_status=EvidenceVerificationStatus.UNKNOWN,
        )
        project.timeline_events.all().delete()

    def _conflicting_market(self, institutions, documents):
        project, _ = Project.objects.update_or_create(
            slug="market-rehabilitation-programme",
            defaults={
                "name": "[DEMO] Market Rehabilitation Programme",
                "description": "Fictional market rehabilitation used to demonstrate conflicting documentary amounts. No finding of wrongdoing is made.",
                "category": ProjectCategory.MARKETS,
                "location": "Kisii Town",
                "country": "KE",
                "county": "Kisii",
                "constituency": "Kitutu Chache North",
                "ward": "Bosongo",
                "institution": institutions["nyanza-works-demo"],
                "contractor": "Highlands Civil Works (fictional)",
                "allocated_amount": 28000000,
                "financial_year": "2024/2025",
                "status": ProjectStatus.IN_PROGRESS,
                "is_featured": True,
                "is_demo": True,
                "start_date": date(2024, 9, 1),
                "expected_completion_date": date(2026, 3, 31),
            },
        )
        project.source_documents.set([documents["market-budget"], documents["market-audit"]])
        project.allocations.all().delete()
        BudgetAllocation.objects.create(
            project=project,
            financial_year="2024/2025",
            amount=28000000,
            allocation_type=AllocationType.DEVELOPMENT,
            source_document=documents["market-budget"],
        )
        project.evidence_items.all().delete()
        budget_claim = Evidence.objects.create(
            project=project,
            claim="Allocated amount is KSh 28 million.",
            evidence_text="Demo budget annex lists KSh 28,000,000.",
            source_document=documents["market-budget"],
            page_number=11,
            verification_status=EvidenceVerificationStatus.CONFLICTING,
            notes="A second demo note records a different amount. Requires further verification.",
        )
        Evidence.objects.create(
            project=project,
            claim="Allocated amount is KSh 19 million.",
            evidence_text="Demo comparison note records KSh 19,000,000 against the same project title.",
            source_document=documents["market-audit"],
            page_number=3,
            verification_status=EvidenceVerificationStatus.CONFLICTING,
        )
        self._replace_timeline(
            project,
            [
                (TimelineStage.ALLOCATION, "Allocation recorded", "Two demo documents list different amounts.", 28000000, date(2024, 6, 10), budget_claim, 1),
                (TimelineStage.CONTRACT, "Contractor named in project record", "No award notice is attached.", None, None, None, 4),
                (TimelineStage.IMPLEMENTATION, "Recorded as in progress", "No site report is attached.", None, None, None, 5),
            ],
        )

    def _tanzania_projects(self, institutions, documents):
        project, _ = Project.objects.update_or_create(
            slug="kigamboni-piped-water-extension",
            defaults={
                "name": "[DEMO] Kigamboni Piped Water Extension",
                "description": (
                    "Fictional piped water extension in Dar es Salaam used for the product demo. "
                    "Official records in this dataset state an allocation of TZS 4,200,000,000 "
                    "in financial year 2025/2026. All names and documents are labelled demo data."
                ),
                "category": ProjectCategory.WATER,
                "location": "Kigamboni, Dar es Salaam",
                "country": "TZ",
                "county": "Dar es Salaam",
                "constituency": "Kigamboni",
                "ward": "Kigamboni",
                "institution": institutions["dar-water-demo"],
                "contractor": "Coastal Pipeline Works Ltd (fictional)",
                "allocated_amount": 4200000000,
                "currency": "TZS",
                "financial_year": "2025/2026",
                "start_date": date(2025, 9, 1),
                "expected_completion_date": date(2026, 11, 30),
                "status": ProjectStatus.IN_PROGRESS,
                "is_featured": True,
                "is_demo": True,
            },
        )
        project.source_documents.set([documents["dar-water-budget"], documents["dar-water-tender"]])
        project.allocations.all().delete()
        BudgetAllocation.objects.create(
            project=project,
            financial_year="2025/2026",
            amount=4200000000,
            currency="TZS",
            allocation_type=AllocationType.DEVELOPMENT,
            source_document=documents["dar-water-budget"],
            notes="Original development allocation recorded in the demo estimates.",
        )
        project.evidence_items.all().delete()
        alloc = Evidence.objects.create(
            project=project,
            claim="Project allocation is TZS 4,200,000,000.",
            evidence_text="The demo Dar es Salaam water estimates list TZS 4,200,000,000 for the Kigamboni Piped Water Extension.",
            source_document=documents["dar-water-budget"],
            page_number=14,
            verification_status=EvidenceVerificationStatus.VERIFIED,
        )
        tender = Evidence.objects.create(
            project=project,
            claim="A tender was published for the works.",
            evidence_text="Demo tender notice dated 14 July 2025 invites bids for pipeline and kiosk works.",
            source_document=documents["dar-water-tender"],
            page_number=1,
            verification_status=EvidenceVerificationStatus.VERIFIED,
        )
        Evidence.objects.create(
            project=project,
            claim="Physical progress after commissioning.",
            evidence_text="",
            verification_status=EvidenceVerificationStatus.UNKNOWN,
            notes="No completion certificate is attached.",
        )
        self._replace_timeline(
            project,
            [
                (TimelineStage.ALLOCATION, "TZS 4.2B allocated", "Development allocation for FY 2025/2026.", 4200000000, date(2025, 5, 20), alloc, 1),
                (TimelineStage.PROCUREMENT, "Tender published", "Open tender for pipeline and kiosk works.", None, date(2025, 7, 14), tender, 2),
                (TimelineStage.IMPLEMENTATION, "Recorded as in progress", "No independent site report is attached.", None, None, None, 3),
            ],
        )
        self._simple_project(
            {
                "slug": "ilemela-market-access-road",
                "name": "[DEMO] Ilemela Market Access Road",
                "description": "Fictional market access road in Mwanza. Allocation is evidenced; contractor evidence is unavailable.",
                "category": ProjectCategory.ROADS,
                "location": "Ilemela, Mwanza",
                "country": "TZ",
                "county": "Mwanza",
                "constituency": "Ilemela",
                "ward": "Ilemela",
                "institution": institutions["mwanza-works-demo"],
                "contractor": "",
                "allocated_amount": 1800000000,
                "currency": "TZS",
                "financial_year": "2025/2026",
                "status": ProjectStatus.PROCUREMENT,
            },
            documents["mwanza-road-budget"],
        )
        self._simple_project(
            {
                "slug": "chamwino-dispensary-upgrade",
                "name": "[DEMO] Chamwino Dispensary Upgrade",
                "description": "Fictional dispensary upgrade in Dodoma with almost no attached evidence. Status is unknown.",
                "category": ProjectCategory.HEALTH,
                "location": "Chamwino, Dodoma",
                "country": "TZ",
                "county": "Dodoma",
                "constituency": "Chamwino",
                "ward": "Chamwino",
                "institution": institutions["dodoma-health-demo"],
                "contractor": "",
                "allocated_amount": None,
                "currency": "TZS",
                "financial_year": "",
                "status": ProjectStatus.UNKNOWN,
            }
        )

    def _burundi_projects(self, institutions, documents):
        project, _ = Project.objects.update_or_create(
            slug="mukaza-public-standpipe-rehabilitation",
            defaults={
                "name": "[DEMO] Mukaza Public Standpipe Rehabilitation",
                "description": (
                    "Fictional standpipe rehabilitation in Bujumbura used for the product demo. "
                    "Official records in this dataset state an allocation of BIF 850,000,000 for 2025. "
                    "All names and documents are labelled demo data."
                ),
                "category": ProjectCategory.WATER,
                "location": "Mukaza, Bujumbura",
                "country": "BI",
                "county": "Bujumbura",
                "constituency": "Mukaza",
                "ward": "Mukaza",
                "institution": institutions["bujumbura-water-demo"],
                "contractor": "Rift Valley Hydraulics (fictional)",
                "allocated_amount": 850000000,
                "currency": "BIF",
                "financial_year": "2025",
                "start_date": date(2025, 6, 1),
                "expected_completion_date": date(2026, 3, 31),
                "status": ProjectStatus.IN_PROGRESS,
                "is_featured": True,
                "is_demo": True,
            },
        )
        project.source_documents.set([documents["bujumbura-water-budget"]])
        project.allocations.all().delete()
        BudgetAllocation.objects.create(
            project=project,
            financial_year="2025",
            amount=850000000,
            currency="BIF",
            allocation_type=AllocationType.DEVELOPMENT,
            source_document=documents["bujumbura-water-budget"],
        )
        project.evidence_items.all().delete()
        alloc = Evidence.objects.create(
            project=project,
            claim="Project allocation is BIF 850,000,000.",
            evidence_text="The demo Bujumbura water estimates list BIF 850,000,000 for Mukaza Public Standpipe Rehabilitation.",
            source_document=documents["bujumbura-water-budget"],
            page_number=8,
            verification_status=EvidenceVerificationStatus.VERIFIED,
        )
        Evidence.objects.create(
            project=project,
            claim="A contractor has been appointed.",
            evidence_text="",
            verification_status=EvidenceVerificationStatus.UNKNOWN,
            notes="No award notice is attached.",
        )
        self._replace_timeline(
            project,
            [
                (TimelineStage.ALLOCATION, "BIF 850M allocated", "Development allocation for 2025.", 850000000, date(2025, 3, 12), alloc, 1),
                (TimelineStage.IMPLEMENTATION, "Recorded as in progress", "No independent site report is attached.", None, None, None, 2),
            ],
        )
        self._simple_project(
            {
                "slug": "gitega-school-latrine-block",
                "name": "[DEMO] Gitega School Latrine Block",
                "description": "Fictional school sanitation block in Gitega. A site note is attached; the allocation page is not.",
                "category": ProjectCategory.SANITATION,
                "location": "Gitega commune, Gitega",
                "country": "BI",
                "county": "Gitega",
                "constituency": "Gitega",
                "ward": "Gitega",
                "institution": institutions["gitega-education-demo"],
                "contractor": "Plateau Masonry Co. (fictional)",
                "allocated_amount": 420000000,
                "currency": "BIF",
                "financial_year": "2025",
                "status": ProjectStatus.IN_PROGRESS,
            },
            documents["gitega-sanitation-note"],
        )
        self._simple_project(
            {
                "slug": "rumonge-marsh-irrigation-canals",
                "name": "[DEMO] Rumonge Marsh Irrigation Canals",
                "description": "Fictional irrigation lining in Burunga. Implementation evidence is unavailable.",
                "category": ProjectCategory.AGRICULTURE,
                "location": "Rumonge, Burunga",
                "country": "BI",
                "county": "Burunga",
                "constituency": "Rumonge",
                "ward": "Rumonge",
                "institution": institutions["burunga-agriculture-demo"],
                "contractor": "",
                "allocated_amount": None,
                "currency": "BIF",
                "financial_year": "",
                "status": ProjectStatus.UNKNOWN,
            }
        )

    def _drc_projects(self, institutions, documents):
        project, _ = Project.objects.update_or_create(
            slug="gombe-drainage-and-culverts",
            defaults={
                "name": "[DEMO] Gombe Drainage and Culverts",
                "description": (
                    "Fictional urban drainage works in Kinshasa used for the product demo. "
                    "Official records in this dataset state an allocation of CDF 12,500,000,000 for 2025. "
                    "All names and documents are labelled demo data."
                ),
                "category": ProjectCategory.SANITATION,
                "location": "Gombe, Kinshasa",
                "country": "CD",
                "county": "Kinshasa",
                "constituency": "Gombe",
                "ward": "Gombe",
                "institution": institutions["kinshasa-works-demo"],
                "contractor": "Fleuve Civil Works (fictional)",
                "allocated_amount": 12500000000,
                "currency": "CDF",
                "financial_year": "2025",
                "start_date": date(2025, 7, 1),
                "expected_completion_date": date(2026, 8, 31),
                "status": ProjectStatus.IN_PROGRESS,
                "is_featured": True,
                "is_demo": True,
            },
        )
        project.source_documents.set([documents["kinshasa-drainage-budget"]])
        project.allocations.all().delete()
        BudgetAllocation.objects.create(
            project=project,
            financial_year="2025",
            amount=12500000000,
            currency="CDF",
            allocation_type=AllocationType.DEVELOPMENT,
            source_document=documents["kinshasa-drainage-budget"],
        )
        project.evidence_items.all().delete()
        alloc = Evidence.objects.create(
            project=project,
            claim="Project allocation is CDF 12,500,000,000.",
            evidence_text="The demo Kinshasa drainage estimates list CDF 12,500,000,000 for Gombe Drainage and Culverts.",
            source_document=documents["kinshasa-drainage-budget"],
            page_number=21,
            verification_status=EvidenceVerificationStatus.VERIFIED,
        )
        self._replace_timeline(
            project,
            [
                (TimelineStage.ALLOCATION, "CDF 12.5B allocated", "Development allocation for 2025.", 12500000000, date(2025, 4, 8), alloc, 1),
                (TimelineStage.IMPLEMENTATION, "Recorded as in progress", "No independent site report is attached.", None, None, None, 2),
            ],
        )
        self._simple_project(
            {
                "slug": "goma-clinic-water-connection",
                "name": "[DEMO] Goma Clinic Water Connection",
                "description": "Fictional clinic water connection in Nord-Kivu. A site note is attached; the budget page is not.",
                "category": ProjectCategory.WATER,
                "location": "Goma, Nord-Kivu",
                "country": "CD",
                "county": "Nord-Kivu",
                "constituency": "Goma",
                "ward": "Goma",
                "institution": institutions["nord-kivu-health-demo"],
                "contractor": "",
                "allocated_amount": 3100000000,
                "currency": "CDF",
                "financial_year": "2025",
                "status": ProjectStatus.DELAYED,
            },
            documents["goma-clinic-progress"],
        )
        market, _ = Project.objects.update_or_create(
            slug="lubumbashi-market-lighting",
            defaults={
                "name": "[DEMO] Lubumbashi Market Lighting",
                "description": "Fictional market lighting used to demonstrate conflicting documentary amounts. No finding of wrongdoing is made.",
                "category": ProjectCategory.MARKETS,
                "location": "Lubumbashi, Haut-Katanga",
                "country": "CD",
                "county": "Haut-Katanga",
                "constituency": "Lubumbashi",
                "ward": "Lubumbashi",
                "institution": institutions["haut-katanga-markets-demo"],
                "contractor": "Katanga Electrics (fictional)",
                "allocated_amount": 2100000000,
                "currency": "CDF",
                "financial_year": "2024",
                "status": ProjectStatus.IN_PROGRESS,
                "is_demo": True,
            },
        )
        market.source_documents.set([documents["lubumbashi-market-budget"], documents["lubumbashi-market-note"]])
        market.allocations.all().delete()
        BudgetAllocation.objects.create(
            project=market,
            financial_year="2024",
            amount=2100000000,
            currency="CDF",
            allocation_type=AllocationType.DEVELOPMENT,
            source_document=documents["lubumbashi-market-budget"],
        )
        market.evidence_items.all().delete()
        budget_claim = Evidence.objects.create(
            project=market,
            claim="Allocated amount is CDF 2,100,000,000.",
            evidence_text="Demo budget annex lists CDF 2,100,000,000.",
            source_document=documents["lubumbashi-market-budget"],
            page_number=5,
            verification_status=EvidenceVerificationStatus.CONFLICTING,
            notes="A second demo note records a different amount. Requires further verification.",
        )
        Evidence.objects.create(
            project=market,
            claim="Allocated amount is CDF 1,450,000,000.",
            evidence_text="Demo comparison note records CDF 1,450,000,000 against the same project title.",
            source_document=documents["lubumbashi-market-note"],
            page_number=2,
            verification_status=EvidenceVerificationStatus.CONFLICTING,
        )
        self._replace_timeline(
            market,
            [
                (TimelineStage.ALLOCATION, "Allocation recorded", "Two demo documents list different amounts.", 2100000000, date(2024, 11, 4), budget_claim, 1),
                (TimelineStage.IMPLEMENTATION, "Recorded as in progress", "No site report is attached.", None, None, None, 2),
            ],
        )

    def _nigeria_projects(self, institutions, documents):
        project, _ = Project.objects.update_or_create(
            slug="ikeja-primary-health-centre-extension",
            defaults={
                "name": "[DEMO] Ikeja Primary Health Centre Extension",
                "description": (
                    "Fictional primary health centre extension in Lagos used for the product demo. "
                    "Official records in this dataset state an allocation of NGN 480,000,000 for 2025. "
                    "All names and documents are labelled demo data."
                ),
                "category": ProjectCategory.HEALTH,
                "location": "Ikeja, Lagos",
                "country": "NG",
                "county": "Lagos",
                "constituency": "Ikeja",
                "ward": "Ikeja",
                "institution": institutions["lagos-health-demo"],
                "contractor": "Harbourline Builders Ltd (fictional)",
                "allocated_amount": 480000000,
                "currency": "NGN",
                "financial_year": "2025",
                "start_date": date(2025, 8, 1),
                "expected_completion_date": date(2026, 7, 31),
                "status": ProjectStatus.IN_PROGRESS,
                "is_featured": True,
                "is_demo": True,
            },
        )
        project.source_documents.set([documents["lagos-phc-budget"], documents["lagos-phc-contract"]])
        project.allocations.all().delete()
        BudgetAllocation.objects.create(
            project=project,
            financial_year="2025",
            amount=480000000,
            currency="NGN",
            allocation_type=AllocationType.DEVELOPMENT,
            source_document=documents["lagos-phc-budget"],
        )
        project.evidence_items.all().delete()
        alloc = Evidence.objects.create(
            project=project,
            claim="Project allocation is NGN 480,000,000.",
            evidence_text="The demo Lagos primary health estimates list NGN 480,000,000 for the Ikeja Primary Health Centre Extension.",
            source_document=documents["lagos-phc-budget"],
            page_number=9,
            verification_status=EvidenceVerificationStatus.VERIFIED,
        )
        contract = Evidence.objects.create(
            project=project,
            claim="The contract was awarded to Harbourline Builders Ltd (fictional).",
            evidence_text="Demo award notice names Harbourline Builders Ltd as the successful bidder.",
            source_document=documents["lagos-phc-contract"],
            page_number=2,
            verification_status=EvidenceVerificationStatus.VERIFIED,
        )
        Evidence.objects.create(
            project=project,
            claim="The extension is commissioned.",
            evidence_text="",
            verification_status=EvidenceVerificationStatus.UNKNOWN,
            notes="No completion certificate is attached.",
        )
        self._replace_timeline(
            project,
            [
                (TimelineStage.ALLOCATION, "NGN 480M allocated", "Capital allocation for 2025.", 480000000, date(2025, 1, 22), alloc, 1),
                (TimelineStage.CONTRACT, "Contract awarded", "Award notice names a fictional contractor.", None, date(2025, 6, 11), contract, 2),
                (TimelineStage.IMPLEMENTATION, "Recorded as in progress", "No independent site report is attached.", None, None, None, 3),
            ],
        )
        self._simple_project(
            {
                "slug": "kano-neighbourhood-road-overlay",
                "name": "[DEMO] Kano Neighbourhood Road Overlay",
                "description": "Fictional neighbourhood road overlay in Kano. Allocation is evidenced; procurement evidence is unavailable.",
                "category": ProjectCategory.ROADS,
                "location": "Kano Municipal, Kano",
                "country": "NG",
                "county": "Kano",
                "constituency": "Kano Municipal",
                "ward": "Kano Municipal",
                "institution": institutions["kano-roads-demo"],
                "contractor": "",
                "allocated_amount": 1200000000,
                "currency": "NGN",
                "financial_year": "2025",
                "status": ProjectStatus.PROCUREMENT,
            },
            documents["kano-roads-budget"],
        )
        self._simple_project(
            {
                "slug": "port-harcourt-school-block",
                "name": "[DEMO] Port Harcourt School Block",
                "description": "Fictional classroom block in Rivers State. Contractor evidence is unavailable.",
                "category": ProjectCategory.EDUCATION,
                "location": "Port Harcourt, Rivers",
                "country": "NG",
                "county": "Rivers",
                "constituency": "Port Harcourt",
                "ward": "Port Harcourt",
                "institution": institutions["rivers-education-demo"],
                "contractor": "",
                "allocated_amount": 350000000,
                "currency": "NGN",
                "financial_year": "2025",
                "status": ProjectStatus.APPROVED,
            }
        )

    def _simple_project(self, spec, document=None):
        spec = {**spec, "is_demo": True}
        spec.setdefault("country", "KE")
        spec.setdefault("currency", "KES")
        project, _ = Project.objects.update_or_create(slug=spec["slug"], defaults=spec)
        if document:
            project.source_documents.set([document])
        if project.allocated_amount and not project.allocations.exists():
            BudgetAllocation.objects.create(
                project=project,
                financial_year=project.financial_year or "Unknown",
                amount=project.allocated_amount,
                currency=project.currency,
                allocation_type=AllocationType.DEVELOPMENT,
                source_document=document,
            )
        if not project.evidence_items.exists() and project.allocated_amount:
            status = (
                EvidenceVerificationStatus.VERIFIED
                if document
                else EvidenceVerificationStatus.UNKNOWN
            )
            Evidence.objects.create(
                project=project,
                claim=f"Allocated amount is {project.format_amount()}.",
                evidence_text="Recorded on the project form. Independent source may be unavailable." if not document else "Listed in the attached demo policy/budget document.",
                source_document=document,
                verification_status=status,
            )
        if not project.timeline_events.exists():
            TimelineEvent.objects.create(
                project=project,
                stage=TimelineStage.ALLOCATION,
                title=project.format_amount(),
                sort_order=1,
                amount=project.allocated_amount,
                currency=project.currency,
            )

    def _replace_timeline(self, project, rows):
        project.timeline_events.all().delete()
        for stage, title, description, amount, occurred_on, evidence, order in rows:
            TimelineEvent.objects.create(
                project=project,
                stage=stage,
                title=title,
                description=description,
                amount=amount,
                occurred_on=occurred_on,
                evidence=evidence,
                currency=project.currency,
                sort_order=order,
            )

    def _policies(self, institutions, documents):
        Policy.objects.update_or_create(
            slug="demo-access-to-project-information",
            defaults={
                "title": "[DEMO] Access to Project Information Note",
                "description": "Fictional note stating that project budgets and award notices should be published. Demo only.",
                "institution": institutions["nyanza-works-demo"],
                "policy_type": PolicyType.ACCESS_TO_INFO,
                "publication_date": date(2024, 11, 2),
                "source_document": documents["access-policy"],
                "status": PolicyStatus.ACTIVE,
                "is_demo": True,
            },
        )
        Policy.objects.update_or_create(
            slug="demo-development-budget-guidelines",
            defaults={
                "title": "[DEMO] Development Budget Documentation Guidelines",
                "description": "Fictional guideline that allocations should cite a budget annex page.",
                "institution": institutions["kisumu-water-demo"],
                "policy_type": PolicyType.BUDGET,
                "publication_date": date(2025, 5, 1),
                "source_document": documents["kisumu-budget"],
                "status": PolicyStatus.ACTIVE,
                "is_demo": True,
            },
        )
        Policy.objects.update_or_create(
            slug="demo-tanzania-access-to-project-information",
            defaults={
                "title": "[DEMO] Regional Access to Project Information Note (Tanzania)",
                "description": "Fictional note stating that project budgets and award notices should be published. Demo only.",
                "institution": institutions["dar-water-demo"],
                "policy_type": PolicyType.ACCESS_TO_INFO,
                "publication_date": date(2024, 10, 7),
                "source_document": documents["tz-access-policy"],
                "status": PolicyStatus.ACTIVE,
                "is_demo": True,
            },
        )
