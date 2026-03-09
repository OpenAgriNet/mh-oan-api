"""Mock MahaDBT scheme status tool for Maharashtra synthetic conversations."""

import random
from datetime import datetime, timedelta
from pydantic_ai import RunContext
from synthetic.deps import FarmerContext
from synthetic.mock_data import (
    MAHADBT_STATUSES, MAHADBT_FINANCIAL_YEARS,
    SCHEME_LIST, should_fail,
)


async def get_scheme_status(ctx: RunContext[FarmerContext]) -> str:
    """Fetch a summary of the farmer's scheme applications and their status from MahaDBT API. Returns a summary of the farmer's scheme applications and their status from MahaDBT, including application status, disbursement information, and scheme details."""
    if not ctx.deps.farmer_id:
        return "Farmer ID is not available in the context. Please register with your farmer ID."

    if should_fail():
        return "Scheme status information service is currently unavailable. Please try again later."

    # 20% chance no applications found
    if random.random() < 0.20:
        return "## MahaDBT Scheme Status Information\n\n❌ No scheme application information found for the requested farmer ID."

    # Build scheme lookup
    scheme_lookup = {s["scheme_code"]: s["scheme_name"] for s in SCHEME_LIST}

    # Generate 1-5 applications
    num_apps = random.randint(1, 5)

    # Use profile's scheme codes if available, otherwise random
    from synthetic.mock_data import SAMPLE_STATE_SCHEMES, SAMPLE_CENTRAL_SCHEMES
    all_codes = SAMPLE_STATE_SCHEMES + SAMPLE_CENTRAL_SCHEMES
    app_codes = random.sample(all_codes, min(num_apps, len(all_codes)))

    lines = [
        "## MahaDBT Scheme Status Information",
        "",
        f"📊 **Summary: {len(app_codes)} total applications**",
    ]

    # Generate status summary
    status_counts = {}
    app_details = []
    for code in app_codes:
        status = random.choice(MAHADBT_STATUSES)
        status_counts[status] = status_counts.get(status, 0) + 1
        scheme_name = scheme_lookup.get(code, code)
        app_details.append((code, scheme_name, status))

    STATUS_LABELS = {
        "Fund Disbursed": "✅ Fund Disbursed (पैसे दिले गेले)",
        "Winner": "🏆 Winner (निवड झाली)",
        "Wait List": "⏳ Wait List (प्रतीक्षा यादीत आहे)",
        "Application cancelled by applicant": "❌ Cancelled by Applicant (तुम्ही अर्ज रद्द केला)",
        "Department Cancelled": "🚫 Department Cancelled (विभागाने अर्ज रद्द केला)",
        "Approved": "✅ Approved (अर्ज मंजूर झाला)",
        "Rejected": "❌ Rejected (अर्ज नाकारला)",
        "Under Review": "📋 Under Review (अर्ज तपासणीमध्ये आहे)",
        "Pending": "⏳ Pending (अर्ज थांबलेला आहे)",
        "Upload Documents": "📄 Upload Documents (कागदपत्रे टाका)",
        "Document scrutiny before pre-sanction": "🔍 Document scrutiny before pre-sanction (पूर्वमंजुरीसाठी कागदपत्र पडताळणी)",
        "Application Approved and Sanction letter generated": "✅ Application Approved – Sanction Letter Ready (अर्ज मंजूर – मंजुरी पत्र तयार आहे)",
    }

    for status, count in status_counts.items():
        label = STATUS_LABELS.get(status, f"📄 {status}")
        lines.append(f"  • {count} {label}")

    lines.append("")
    lines.append("### Detailed Information:")
    lines.append("")

    for code, scheme_name, status in app_details:
        app_id = "".join(str(random.randint(0, 9)) for _ in range(8))
        masked_app_id = f"***{app_id[-4:]}"
        fy = random.choice(MAHADBT_FINANCIAL_YEARS)
        fy_display = f"20{fy[:2]}-20{fy[2:]}"

        # Random dates
        last_updated = (datetime.now() - timedelta(days=random.randint(1, 180))).strftime("%d %b %Y")

        label = STATUS_LABELS.get(status, f"📄 {status}")
        lines.append(f"> **{scheme_name}**")
        lines.append(f"  Application ID: {masked_app_id}")
        lines.append(f"  Status: {label}")
        lines.append(f"  Financial Year: {fy_display}")
        lines.append(f"  Last Updated: {last_updated}")

        if status == "Fund Disbursed":
            disb_date = (datetime.now() - timedelta(days=random.randint(1, 90))).strftime("%d %b %Y")
            lines.append(f"  Disbursement Date: {disb_date}")

        lines.append("")

    return "\n".join(lines)
