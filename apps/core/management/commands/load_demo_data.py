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
        others = [
            {
                "slug": "ecd-classroom-homa-bay",
                "name": "[DEMO] Early Childhood Classroom Block",
                "description": "Fictional ECD classroom project with partial documentary support.",
                "category": ProjectCategory.EDUCATION,
                "location": "Rangwe, Homa Bay County",
                "county": "Homa Bay",
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
                "county": "Migori",
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
                "county": "Busia",
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
                "county": "Bungoma",
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
                "county": "Vihiga",
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
                "county": "Kisumu",
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
                "county": "Kisumu",
                "ward": "Kolwa East",
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
                "county": "Siaya",
                "ward": "Ugunja",
                "institution": institutions["siaya-energy-demo"],
                "contractor": "",
                "allocated_amount": 22000000,
                "financial_year": "2025/2026",
                "status": ProjectStatus.PROCUREMENT,
                "is_featured": True,
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
                "county": "Kakamega",
                "ward": "Lurambi",
                "institution": institutions["western-health-demo"],
                "contractor": "",
                "allocated_amount": None,
                "financial_year": "",
                "status": ProjectStatus.UNKNOWN,
                "is_featured": True,
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
                "county": "Kisii",
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

    def _simple_project(self, spec, document=None):
        spec = {**spec, "is_demo": True, "currency": "KES"}
        project, _ = Project.objects.update_or_create(slug=spec["slug"], defaults=spec)
        if document:
            project.source_documents.set([document])
        if project.allocated_amount and not project.allocations.exists():
            BudgetAllocation.objects.create(
                project=project,
                financial_year=project.financial_year or "Unknown",
                amount=project.allocated_amount,
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
