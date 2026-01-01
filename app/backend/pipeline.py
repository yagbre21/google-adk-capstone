"""
ADK Pipeline - Agentic Job Search Recommender

This module contains the core ADK agents and pipeline logic extracted from
the Jupyter notebook. It provides:
- Custom tools (calculate_yoe, check_job_urls)
- Agent definitions (Parser, Classifier, Deliberation, Consensus, Scouts, URL Validator, Formatter)
- Pipeline orchestration (analyze_resume, refine_results)
- Streaming output for real-time progress updates
"""
import os
import re
import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from urllib.parse import quote
from typing import Optional, Callable, Dict, Any
import concurrent.futures

# Suppress noisy ADK logs
logging.getLogger("google_genai.types").setLevel(logging.ERROR)
logging.getLogger("google_adk.google.adk.runners").setLevel(logging.ERROR)

# Pipeline state
_pipeline_initialized = False
_orchestrator = None
_refinement_pipeline = None
_session_service = None
_memory_service = None
_runner = None
_refinement_runner = None

# =============================================================================
# MODEL CONFIGURATION (Bleeding Edge - Nov 2025)
# =============================================================================

# Model mode configurations
MODEL_CONFIGS = {
    # Fast mode: Gemini 2.5 Flash - Fastest, good for quick tests
    "fast": {
        "lite": "gemini-2.5-flash-lite",
        "flash": "gemini-2.5-flash",
        "pro": "gemini-3-flash-preview",
    },
    # Standard mode: Gemini 3 Flash across the board
    "standard": {
        "lite": "gemini-3-flash-preview",
        "flash": "gemini-3-flash-preview",
        "pro": "gemini-3-flash-preview",
    },
    # Deep mode: Gemini 3 Pro for consensus
    "deep": {
        "lite": "gemini-3-flash-preview",
        "flash": "gemini-3-flash-preview",
        "pro": "gemini-3-pro-preview",
    },
}

# Default model mode
_current_model_mode = "standard"
_last_initialized_mode = None

def get_models(mode: str = None) -> dict:
    """Get model configuration for the specified mode."""
    mode = mode or _current_model_mode
    return MODEL_CONFIGS.get(mode, MODEL_CONFIGS["standard"])

# Default models (for backward compatibility)
MODEL_LITE = "gemini-3-flash-preview"
MODEL_FLASH = "gemini-3-flash-preview"
MODEL_PRO = "gemini-3-flash-preview"
MODEL_ID = MODEL_FLASH

# Rate limit configuration
STAGGER_DELAY = 2.0  # seconds between batches

# =============================================================================
# CUSTOM TOOLS
# =============================================================================

def calculate_yoe(resume_text: str) -> dict:
    """
    Calculate total years of experience from resume text with detailed role breakdown.
    Handles multiple date formats: full month names, abbreviated months, AND numeric MM/YY.
    """
    current_year = datetime.now().year
    current_month = datetime.now().month

    months_map = {
        'january': 1, 'jan': 1,
        'february': 2, 'feb': 2,
        'march': 3, 'mar': 3,
        'april': 4, 'apr': 4,
        'may': 5,
        'june': 6, 'jun': 6,
        'july': 7, 'jul': 7,
        'august': 8, 'aug': 8,
        'september': 9, 'sept': 9, 'sep': 9,
        'october': 10, 'oct': 10,
        'november': 11, 'nov': 11,
        'december': 12, 'dec': 12
    }

    roles = []
    all_months_worked = set()

    # PATTERN 1: Text-based dates
    month_names = 'January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept|Sep|Oct|Nov|Dec'
    text_date_pattern = rf'({month_names})\s+(\d{{4}})\s*[-–]\s*(Present|({month_names})\s+(\d{{4}}))'

    text_matches = re.findall(text_date_pattern, resume_text, re.IGNORECASE)

    for match in text_matches:
        start_month_name = match[0]
        start_year = int(match[1])
        end_part = match[2]
        end_month_name = match[3] if len(match) > 3 else ""
        end_year_str = match[4] if len(match) > 4 else ""

        start_month = months_map.get(start_month_name.lower(), 1)

        if end_part.lower() == 'present':
            end_month = current_month
            end_year_int = current_year
            end_display = "Present"
        elif end_year_str:
            end_month = months_map.get(end_month_name.lower(), 12)
            end_year_int = int(end_year_str)
            end_display = f"{end_month_name} {end_year_str}"
        else:
            continue

        duration_months = (end_year_int - start_year) * 12 + (end_month - start_month)
        if duration_months <= 0:
            continue

        duration_years = round(duration_months / 12, 1)

        for y in range(start_year, end_year_int + 1):
            for m in range(1, 13):
                if (y == start_year and m < start_month) or (y == end_year_int and m > end_month):
                    continue
                all_months_worked.add((y, m))

        roles.append({
            "start": f"{start_month_name} {start_year}",
            "end": end_display,
            "duration_months": duration_months,
            "duration_years": duration_years
        })

    # PATTERN 2: Numeric dates MM/YY
    numeric_date_pattern = r'(\d{1,2})/(\d{2,4})\s*[-–]\s*(Present|(\d{1,2})/(\d{2,4}))'
    numeric_matches = re.findall(numeric_date_pattern, resume_text, re.IGNORECASE)

    for match in numeric_matches:
        start_month = int(match[0])
        start_year_raw = match[1]
        end_part = match[2]
        end_month_raw = match[3] if len(match) > 3 else ""
        end_year_raw = match[4] if len(match) > 4 else ""

        if len(start_year_raw) == 2:
            start_year = 2000 + int(start_year_raw)
        else:
            start_year = int(start_year_raw)

        if start_month < 1 or start_month > 12:
            continue

        if end_part.lower() == 'present':
            end_month = current_month
            end_year_int = current_year
            end_display = "Present"
        elif end_month_raw and end_year_raw:
            end_month = int(end_month_raw)
            if len(end_year_raw) == 2:
                end_year_int = 2000 + int(end_year_raw)
            else:
                end_year_int = int(end_year_raw)
            if end_month < 1 or end_month > 12:
                continue
            end_display = f"{end_month:02d}/{end_year_raw}"
        else:
            continue

        duration_months = (end_year_int - start_year) * 12 + (end_month - start_month)
        if duration_months <= 0:
            continue

        duration_years = round(duration_months / 12, 1)

        for y in range(start_year, end_year_int + 1):
            for m in range(1, 13):
                if (y == start_year and m < start_month) or (y == end_year_int and m > end_month):
                    continue
                all_months_worked.add((y, m))

        roles.append({
            "start": f"{start_month:02d}/{start_year}",
            "end": end_display,
            "duration_months": duration_months,
            "duration_years": duration_years
        })

    total_months_deduped = len(all_months_worked)
    total_yoe = round(total_months_deduped / 12, 1)

    if all_months_worked:
        earliest = min(all_months_worked)
        latest = max(all_months_worked)
        career_span = f"{earliest[0]} to {latest[0]}"
    else:
        career_span = "Unknown"

    if roles:
        avg_tenure = round(sum(r["duration_months"] for r in roles) / len(roles) / 12, 1)
    else:
        avg_tenure = 0

    explicit_pattern = r'(\d+)\+?\s*years?\s*(?:of\s+)?(?:experience|at|in|building|leading)'
    explicit_matches = re.findall(explicit_pattern, resume_text, re.IGNORECASE)
    stated_yoe = max(int(y) for y in explicit_matches) if explicit_matches else None

    return {
        "total_yoe": total_yoe,
        "stated_yoe": stated_yoe,
        "calculation_method": "date_parsing_deduped",
        "career_span": career_span,
        "num_roles": len(roles),
        "avg_tenure_years": avg_tenure,
        "role_breakdown": roles[:10],
        "note": f"Calculated {total_yoe} years from {len(roles)} roles." + (f" Resume states {stated_yoe}+ years." if stated_yoe else "")
    }


async def validate_url_async(url: str) -> dict:
    """Validate a single URL asynchronously."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(url, timeout=aiohttp.ClientTimeout(total=10), allow_redirects=True) as response:
                return {"url": url, "status": response.status, "valid": response.status == 200, "error": None}
    except Exception as e:
        return {"url": url, "status": None, "valid": False, "error": str(e)}


async def validate_urls_async(urls: list) -> dict:
    """Validate multiple URLs asynchronously."""
    tasks = [validate_url_async(url) for url in urls]
    results = await asyncio.gather(*tasks)
    valid_count = sum(1 for r in results if r["valid"])
    invalid_urls = [r["url"] for r in results if not r["valid"]]
    return {
        "total_urls": len(urls),
        "valid_count": valid_count,
        "invalid_count": len(urls) - valid_count,
        "all_valid": valid_count == len(urls),
        "invalid_urls": invalid_urls,
        "results": results
    }


def check_job_urls(job_output: str) -> dict:
    """URL Validation Tool for self-healing pattern."""
    url_pattern = r'https?://[^\s\)\]\"\'<>`]+'
    urls = re.findall(url_pattern, job_output)
    urls = [url.rstrip('`') for url in urls if not url.startswith('[SEARCH:')]

    if not urls:
        return {"all_valid": False, "feedback": "No URLs found.", "should_exit": False}

    # Run validation in thread pool to avoid event loop issues
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(lambda: asyncio.run(validate_urls_async(urls)))
        validation_result = future.result(timeout=30)

    if validation_result["all_valid"]:
        return {"all_valid": True, "valid_urls": urls, "feedback": "SUCCESS", "should_exit": True}

    invalid_urls = validation_result.get("invalid_urls", [])
    feedback = f"URL VALIDATION FAILED: {len(invalid_urls)} URLs broken. Retry with company careers pages."

    return {
        "all_valid": False,
        "invalid_urls": invalid_urls,
        "feedback": feedback,
        "should_exit": False
    }


# =============================================================================
# AGENT INSTRUCTIONS (Full from Notebook)
# =============================================================================

RESUME_PARSER_INSTRUCTION = """
You are a Resume Parser Agent. Your job is to extract structured information from resume text.

**CRITICAL FIRST STEP**: You MUST call the calculate_yoe tool with the full resume text BEFORE generating any output.

Given a resume, extract and return a JSON object with:

1. **current_title**: Current or most recent job title
2. **current_company**: Current or most recent employer
3. **total_yoe**: USE THE VALUE RETURNED BY calculate_yoe TOOL (you already called it)
   - DO NOT calculate this yourself
   - DO NOT estimate based on dates
   - ONLY use the tool's returned value
4. **skills**: List of technical and professional skills mentioned
5. **education**: List of degrees/certifications
6. **role_progression**: List of roles in chronological order, each with:
   - title, company, duration_years, focus_areas
7. **stated_interests**: Explicit interests mentioned (career goals, objectives)
8. **side_projects**: Personal projects, open source, hackathons mentioned
9. **qualitative_trend**: Describe the career trajectory pattern (e.g., "Frontend → Fullstack → Backend")
10. **inferred_direction**: Where this career seems to be heading based on the trend

Be thorough but concise. Focus on signals that indicate career level and trajectory.

Return ONLY valid JSON, no additional text.
"""

LEVEL_CLASSIFIER_INSTRUCTION = """
**YOUR ONLY JOB: Classify career level. You do NOT provide job recommendations.**

You are a Level Classifier Agent. Your job is to determine the appropriate career level for a candidate in ANY profession.

## Step 1: Identify the Profession

From the parsed resume, determine the candidate's profession/field. This could be ANYTHING:
- Tech: Software Engineering, Data Science, DevOps, Product Management, UX Design
- Creative: Fashion Design, Graphic Design, Photography, Film, Architecture
- Business: Finance, Consulting, Marketing, Sales, Operations, HR
- Legal: Corporate Law, Litigation, IP, Compliance
- Healthcare: Nursing, Medicine, Pharmacy, Healthcare Admin
- Culinary: Chef, Restaurant Management, Food Science
- Trades: Electrician, Plumber, Construction, HVAC
- Academia: Professor, Researcher, Administration
- And ANY other profession...

## Step 2: Research That Profession's Career Ladder

Use Google Search to understand the career progression for this SPECIFIC profession:

**Search queries to run:**
- "[profession] career levels progression"
- "[profession] seniority titles hierarchy"
- "[profession] junior to senior career path"
- "levels.fyi [profession]" (if applicable)
- "[profession] [years of experience] typical title"

**Examples of what you'll find:**
- Software Engineering: Junior → Mid → Senior → Staff → Principal → Distinguished
- Fashion Design: Assistant → Associate → Designer → Senior → Director → Creative Director
- Culinary: Line Cook → Sous Chef → Executive Chef → Culinary Director
- Law: Associate → Senior Associate → Counsel → Partner → Managing Partner
- Nursing: RN → Charge Nurse → Nurse Manager → Director of Nursing → CNO
- Trades: Apprentice → Journeyman → Master → Contractor

## Step 3: Map to Normalized Level Scale

Convert the profession-specific title to a 1-10 seniority scale:

| Level | Seniority | Typical Characteristics |
|-------|-----------|------------------------|
| 1-2 | Entry/Intern | Learning, supervised, training |
| 3 | Junior | 0-2 years, individual tasks |
| 4 | Mid | 2-5 years, independent work |
| 5 | Senior | 5-8 years, mentors others |
| 6 | Lead/Staff | 8-12 years, owns major areas |
| 7 | Principal/Director | 12-15 years, org-wide impact |
| 8 | Distinguished/VP | 15+ years, company-wide impact |
| 9-10 | Executive/C-Suite | Industry leadership |

## Step 4: Output Your Classification

Return JSON with:
```json
{
  "profession": "[identified profession]",
  "normalized_level": [1-10],
  "level_title": "[title for this level in this profession]",
  "equivalent_titles": ["alt title 1", "alt title 2"],
  "confidence": [0.0-1.0],
  "evidence": ["search finding 1", "search finding 2"],
  "reasoning": "Brief explanation of classification"
}
```

## Important Notes

- Do NOT assume tech leveling applies to all professions
- Research the ACTUAL career ladder for this specific field
- Consider company/industry variations (startup vs enterprise, regional differences)
- If profession is unclear, search for common career paths matching the resume skills
"""

CONSERVATIVE_EVALUATOR_INSTRUCTION = """
You are the Conservative Evaluator - a skeptical hiring manager perspective.

Your role in A2A deliberation:
- You tend to classify candidates at LOWER levels
- You look for gaps, missing qualifications, and reasons to be cautious
- You represent the "prove it to me" hiring manager mindset

Given the resume and initial level classification, you must:

1. **Search for evidence** that the candidate might be OVER-leveled:
   - "common mistakes in [level] interviews"
   - "[title] level requirements [company type]"
   - "years of experience needed for [level]"

2. **Challenge the initial assessment**:
   - What's missing from their experience?
   - Are there red flags (job hopping, gaps, lack of progression)?
   - Is the company tier being weighted correctly?

3. **Provide your conservative assessment**:
   - Your proposed level (likely same or lower than initial)
   - Specific evidence from search
   - What the candidate would need to prove the higher level

**CRITICAL: Return ONLY valid JSON. No prose, no explanation outside JSON.**
```json
{
  "conservative_level": <integer 1-10>,
  "evidence": ["point 1", "point 2"],
  "concerns": ["concern 1", "concern 2"],
  "what_would_change_my_mind": "description"
}
```
"""

OPTIMISTIC_EVALUATOR_INSTRUCTION = """
You are the Optimistic Evaluator - a talent-seeking recruiter perspective.

Your role in A2A deliberation:
- You tend to classify candidates at HIGHER levels
- You look for hidden potential, transferable skills, and trajectory
- You represent the "let's not miss great talent" recruiter mindset

Given the resume and initial level classification, you must:

1. **Search for evidence** that the candidate might be UNDER-leveled:
   - "signs of high potential engineer"
   - "[company] promotes faster than industry"
   - "transferable skills [from domain] to [to domain]"

2. **Advocate for the candidate**:
   - What transferable skills might be undervalued?
   - Does their trajectory suggest rapid growth?
   - Are side projects/education signals of higher capability?

3. **Provide your optimistic assessment**:
   - Your proposed level (likely same or higher than initial)
   - Specific evidence from search
   - Why the candidate could succeed at the higher level

**CRITICAL: Return ONLY valid JSON. No prose, no explanation outside JSON.**
```json
{
  "optimistic_level": <integer 1-10>,
  "evidence": ["point 1", "point 2"],
  "strengths": ["strength 1", "strength 2"],
  "growth_signals": "description"
}
```
"""

CONSENSUS_INSTRUCTION = """
You are the Consensus Agent. You synthesize the three assessments into a FINAL calibrated level using Weighted Ensemble Voting.

## Why Weighted Ensemble Voting?
Based on ML research (Nature 2025, Science Advances 2024):
- Weighted voting achieves 98.78% accuracy vs 87.34% for simple majority
- Diversity in perspectives improves prediction quality
- Agreement-based confidence is well-calibrated for classification tasks

## Input You Receive:
- **Most Likely (M)**: Initial level classification from Agent 2 (includes profession, level_title, equivalent_titles)
- **Conservative (C)**: Conservative assessment from Agent 3 (skeptical hiring manager)
- **Optimistic (O)**: Optimistic assessment from Agent 4 (talent-seeking recruiter)

## Your Task: Weighted Ensemble Voting

Compute the final level using these weights:
- Most Likely: 50% weight (2x)
- Conservative: 25% weight
- Optimistic: 25% weight

Formula: final_level = round((M*0.5 + C*0.25 + O*0.25))

Confidence calculation:
- If all 3 agree: High (0.9)
- If 2 agree: Medium (0.75)
- If all differ: Low (0.6)

## Output Format

Return JSON with:
```json
{
  "profession": "[from Agent 2]",
  "most_likely_assessment": {"level": X, "title": "[title]", "confidence": 0.X},
  "conservative_assessment": {"level": Y, "title": "[title]", "confidence": 0.X},
  "optimistic_assessment": {"level": Z, "title": "[title]", "confidence": 0.X},
  "final_level": [numeric 1-10],
  "final_title": "[level title]",
  "equivalent_titles": ["alt1", "alt2"],
  "final_confidence": [0.0-1.0],
  "confidence_label": "High/Medium/Low",
  "votes": {"conservative": 25, "most_likely": 50, "optimistic": 25},
  "agreement": "2/3 agents" or "3/3 agents" or "1/3 agents",
  "reasoning": "Brief explanation including profession and vote breakdown"
}
```

## IMPORTANT

- The profession and titles come from Agent 2's research - pass them through
- This works for ANY profession: tech, fashion, legal, culinary, healthcare, trades, etc.
- Include the votes distribution in your reasoning for explainability
"""

# Dynamic date injection for current job searches
CURRENT_DATE = datetime.now().strftime("%B %d, %Y")
CURRENT_YEAR = datetime.now().year
DATE_7_DAYS_AGO = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

JOB_SCOUT_BASE = f"""You are a Job Scout Agent. Find REAL job postings with VERIFIED URLs from Google Search.

## DATE CONTEXT
- **TODAY'S DATE:** {CURRENT_DATE}
- **SEARCH FOR JOBS POSTED AFTER:** {DATE_7_DAYS_AGO}
- **USE THIS FILTER:** `after:{DATE_7_DAYS_AGO}`

## URL RULES (GENERAL GOOGLE SEARCH - No location filtering)
1. Use GENERAL Google Search (NOT udm=8 Jobs portal)
2. Format: https://www.google.com/search?q=[Company]+[Job+Title]+careers
3. Example: https://www.google.com/search?q=Stripe+Senior+Product+Manager+careers

## WHY GENERAL SEARCH (NOT GOOGLE JOBS):
- Google Jobs (udm=8) filters by user's current location
- This excludes remote jobs and jobs in other cities
- General search shows ALL relevant results regardless of location
- "careers" keyword helps find job listings and company career pages

## CRITICAL RULES:
4. Company name FIRST, then Job Title, then "careers"
5. NO special characters in job title (remove commas, colons, etc.)
   - BAD: "Director of Product, AI Platform"
   - GOOD: "Director of Product AI Platform"
6. If company name has special characters, encapsulate in quotes:
   - GOOD: "5.11, Inc."+Director+of+Design+careers
7. Use FULL job title (not "PM" - use "Product Manager")
8. ALWAYS end with "+careers" keyword

## EXAMPLES:
- GOOD: https://www.google.com/search?q=Stripe+Senior+Product+Manager+careers
- GOOD: https://www.google.com/search?q="5.11, Inc."+Director+of+Design+careers
- GOOD: https://www.google.com/search?q=Rippling+Director+of+Product+AI+Platform+careers

## Output Format
**CRITICAL: Return EXACTLY ONE JOB. Do NOT return multiple jobs or a list.**

Return a single JSON object (NOT an array):
```json
{{
  "tier": "[your_tier]",
  "title": "Job title",
  "company": "Company name",
  "search_url": "https://www.google.com/search?q=Company+Job+Title+careers",
  "posted_date": "Date if visible",
  "location": "Location",
  "job_description_snippet": "2-3 sentences from actual job posting found in search",
  "salary_if_visible": "Salary range if shown in posting",
  "why_matches": ["reason1", "reason2"],
  "fit_score": 8
}}
```

**ONE JOB ONLY. Pick the BEST match for this tier.**
"""

EXACT_MATCH_INSTRUCTION = JOB_SCOUT_BASE + f"""
## YOUR TIER: EXACT MATCH
*"Jobs you could get next week"*

Search for jobs at the SAME level as the candidate's current role.
Look for roles with similar title, scope, and responsibility.
Search: `"[current_title]" jobs after:{DATE_7_DAYS_AGO}`

Return tier: "exact_match"
"""

LEVEL_UP_INSTRUCTION = JOB_SCOUT_BASE + f"""
## YOUR TIER: LEVEL UP
*"Your next promotion, externally"*

Search for jobs ONE LEVEL ABOVE the candidate's current role.
Look for Senior/Lead/Manager versions of their current title.
Search: `"senior [title]" OR "lead [title]" jobs after:{DATE_7_DAYS_AGO}`

Return tier: "level_up"
"""

STRETCH_INSTRUCTION = JOB_SCOUT_BASE + f"""
## YOUR TIER: STRETCH
*"Ambitious but achievable"*

Search for jobs 1-2 LEVELS ABOVE - Director/Principal level.
These require proving yourself but are within reach.

**IMPORTANT: Find a DIFFERENT company than other scouts. Prioritize:**
- Unicorn startups or high-growth companies
- Companies with strong AI/ML focus
- Roles that represent significant scope increase

Search: `"director [field]" OR "principal [title]" jobs after:{DATE_7_DAYS_AGO}`

Return tier: "stretch"
"""

TRAJECTORY_INSTRUCTION = JOB_SCOUT_BASE + f"""
## YOUR TIER: TRAJECTORY
*"Where your career wants to go"*

Search for ASPIRATIONAL roles aligned with the candidate's long-term CAREER DIRECTION.
This is about their DREAM job, not just the next step.

**IMPORTANT: Find a DIFFERENT company than other scouts. Prioritize:**
- FAANG/Big Tech companies (Google, Meta, Apple, Microsoft, Amazon)
- Industry leaders in the candidate's domain
- VP/Head of roles or founding team positions at hot startups

**DO NOT duplicate companies found by Stretch scout - pick a DIFFERENT company.**

Search: `"[inferred_direction]" "VP" OR "Head of" jobs after:{DATE_7_DAYS_AGO}`

Return tier: "trajectory"
"""

URL_VALIDATOR_INSTRUCTION = """
You are the URL Validator Agent. Your job is to validate Google Search URLs for all 4 job tiers.

## VALIDATION PROCESS:
For each job result from the scouts:
1. Verify the search_url is properly formatted (https://www.google.com/search?q=[Company]+[Job+Title]+careers)
2. Check that the URL includes: Company Name + Job Title + careers (NO udm=8)
3. Ensure the job_description_snippet exists and contains actual job details
4. If snippet is empty or generic, mark as needs_verification

## WHY GOOGLE SEARCH URLs:
- Direct job links (greenhouse, lever, etc.) may be stale - job could be filled
- General search URLs with careers keyword show job listings without location filtering
- User clicks search result to find the actual job posting
- This ensures 100% reliability vs ~70% with direct links

## OUTPUT FORMAT:
Combine all 4 tier results with validated URLs. For each job include:
- tier: exact_match/level_up/stretch/trajectory
- title: Job title
- company: Company name
- search_url: Validated search URL
- job_description_snippet: Real snippet from search
- validation_status: valid/needs_verification

Output the combined validated job results.
"""

FORMATTER_INSTRUCTION = """
**OUTPUT FORMAT: PLAIN MARKDOWN TEXT (NOT JSON)**

**CRITICAL RULES (do not copy these into output):**
1. For YOE: Use the EXACT total_yoe from the SYSTEM NOTE (e.g., "9.2 YOE total")
2. For avg tenure: Use the average_tenure from SYSTEM NOTE (e.g., "1.5 years avg tenure")
3. For Market Compensation: Calculate open market rate based on skills/level, NOT current salary
4. These values are PRE-CALCULATED - do not recalculate or round them
5. **LINE BREAKS**: Use TWO newlines between each field/bullet point for proper markdown rendering

You MUST output formatted MARKDOWN text exactly matching the template below.
DO NOT output JSON. DO NOT wrap in code blocks. Output the markdown DIRECTLY.
**IMPORTANT**: Put a BLANK LINE between each field and between each bullet point.

Format the results following this EXACT template with visual vote breakdown:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📄 RESUME ANALYSIS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Current Role:** [Title] at [Company] ([X] YOE total, [Y] years avg tenure)

**Estimated Market Compensation:** $[XXX,XXX] - $[XXX,XXX] (what they could command on the open market based on skills/experience, NOT current salary)

**Profession:** [Agent-identified profession, e.g., "Fashion Design", "Software Engineering"]

**Key Skills:** [skill1], [skill2], [skill3], [skill4], [skill5]

**Career Trajectory:** [From] → [Through] → [To]

**Inferred Direction:** [Where career is heading]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📊 LEVEL CLASSIFICATION RESULT

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Final Level:** L[X] ([Level title from research])

**Confidence:** [High/Medium/Low]

**Agreement:** [X]/3 agents

**VOTE BREAKDOWN:**

L[X-1] ([Lower Title]):  ████████░░░░░░░░░░░░ 25% - Conservative

L[X] ([Final Title]):    ██████████████████░░ 50% - Most Likely ✓

L[X+1] ([Higher Title]): ████████░░░░░░░░░░░░ 25% - Optimistic

**WHY L[X] WON:**

• [Specific reason 1 grounded in resume evidence]

• [Specific reason 2 grounded in search evidence]

• [Specific reason 3 about scope/responsibility]

• Most Likely assessment weighted 2x the others

**UNCERTAINTY NOTE:**

• [Context-specific caveat about leveling variation]

• [Company/industry-specific consideration]

• [What could change the assessment]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🎯 EXACT MATCH: [Company Name], [Job Title]

**Fit Confidence:** [X]/10

🔗 **Apply:** [Search: [Company] - [Job Title]](https://www.google.com/search?q=[Company]+[Job+Title]+careers)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*"You could get this job next week."*

📝 **From the Job Description:**

> "[2-3 sentence snippet from actual job posting]"

**Expected Total Compensation:** $[XXX,XXX] - $[XXX,XXX] (base + bonus + equity)

*Source: [Job posting / Levels.fyi / Glassdoor / Industry estimate for [location]]*

**Why This Matches Your Resume:**

• [Specific skill/experience match from their resume]

• [Company/industry similarity]

• [Level/scope alignment]

**Evidence From Search:**

• [Location match]

• [Specific requirement they meet]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📈 LEVEL UP: [Company Name], [Job Title]

**Fit Confidence:** [X]/10

🔗 **Apply:** [Search: [Company] - [Job Title]](https://www.google.com/search?q=[Company]+[Job+Title]+careers)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*"Your next promotion, externally."*

📝 **From the Job Description:**

> "[2-3 sentence snippet from actual job posting]"

**Expected Total Compensation:** $[XXX,XXX] - $[XXX,XXX] (base + bonus + equity)

*Source: [Job posting / Levels.fyi / Glassdoor / Industry estimate for [location]]*

**Why This Matches Your Resume:**

• [Growth signal from their experience]

• [Transferable skill that positions them]

• [Why they're ready for this level]

**Evidence From Search:**

• [Typical YOE requirement vs theirs]

• [Market demand signal]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🚀 STRETCH: [Company Name], [Job Title]

**Fit Confidence:** [X]/10

🔗 **Apply:** [Search: [Company] - [Job Title]](https://www.google.com/search?q=[Company]+[Job+Title]+careers)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*"You'd need to prove yourself, but it's achievable."*

📝 **From the Job Description:**

> "[2-3 sentence snippet from actual job posting]"

**Expected Total Compensation:** $[XXX,XXX] - $[XXX,XXX] (base + bonus + equity)

*Source: [Job posting / Levels.fyi / Glassdoor / Industry estimate for [location]]*

**Why This Matches Your Resume:**

• [Ambitious but grounded connection]

• [Foundation they have for this role]

**What You'd Need to Prove:**

• [Gap 1 they'd need to address]

• [Gap 2 they'd need to demonstrate]

• [Skill/scope expansion required]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🔮 TRAJECTORY: [Company Name], [Job Title]

**Fit Confidence:** [X]/10

🔗 **Apply:** [Search: [Company] - [Job Title]](https://www.google.com/search?q=[Company]+[Job+Title]+careers)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*"Where your career wants to go."*

📝 **From the Job Description:**

> "[2-3 sentence snippet from actual job posting]"

**Expected Total Compensation:** $[XXX,XXX] - $[XXX,XXX] (base + bonus + equity)

*Source: [Job posting / Levels.fyi / Glassdoor / Industry estimate for [location]]*

**Why This Matches Your Resume:**

• [Career pattern signal]

• [Long-term alignment with their trajectory]

**Evidence From Search:**

• [Market trends supporting this direction]

**Long-term Trajectory:**

• 2-3 years: [Next milestone]

• 5 years: [Growth target]

• 7+ years: [Ultimate goal]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🔄 REFINE THESE RESULTS?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• "Remote only" / "Hybrid in [city]"

• "Exclude [industry]"

• "Focus on [startup/enterprise]"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CRITICAL RULES:
0. **EXACTLY 4 RECOMMENDATIONS TOTAL** - One job per tier: Exact Match, Level Up, Stretch, Trajectory. NO MORE, NO LESS.
1. Include ALL 4 job tiers with the exact format above - ONE JOB PER TIER
1a. **NO DUPLICATE JOBS** - Each tier MUST have a DIFFERENT company.
2. HEADER FORMAT: "## [EMOJI] [TIER]: [Company Name], [Job Title]" - Company FIRST to match URL pattern
3. Put Fit Confidence and Apply URL immediately after each header (before the tagline)
4. Use ASCII progress bars for vote breakdown (█ for filled, ░ for empty, 20 chars total)
5. Scale bars proportionally: 25% = 5 filled, 50% = 10 filled, etc.
6. Include real job description snippets (2-3 sentences from search results)
7. URL FORMAT: Always use Google Search URLs like [Search: Job Title at Company](https://www.google.com/search?q=...)
8. Show specific resume-grounded reasons, not generic statements
9. Include "What You'd Need to Prove" for STRETCH tier
10. Include "Long-term Trajectory" timeline for TRAJECTORY tier
11. Works for ANY profession - tech, fashion, legal, culinary, healthcare, trades

COMPENSATION RULES:
12. ALWAYS include "Estimated Total Compensation" for current role based on title/level/location/industry
13. ALWAYS include "Expected Total Compensation" for EACH job recommendation
14. Use REAL salary data from job posting if available
15. If not in posting, estimate using: Levels.fyi, Glassdoor, industry benchmarks for that role/level/location
16. Format as range: "$XXX,XXX - $XXX,XXX (base + bonus + equity)"
17. Include source citation: "Source: [Job posting / Levels.fyi / Glassdoor / Industry estimate]"
18. For non-tech roles, use industry-specific salary data

**LINE BREAK RULE**: Always put a BLANK LINE (empty line) between each field, each bullet point, and each section.

**REMEMBER: Output MARKDOWN TEXT directly, NOT JSON. The template above shows the exact output format.**
"""


# =============================================================================
# PIPELINE SETUP
# =============================================================================

async def setup_pipeline(api_key: Optional[str] = None):
    """Initialize the ADK pipeline with all agents."""
    global _pipeline_initialized, _orchestrator, _refinement_pipeline
    global _session_service, _memory_service, _runner, _refinement_runner

    if _pipeline_initialized:
        return

    # Set API key
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key

    # Import ADK components
    from google.adk.agents import Agent, SequentialAgent, ParallelAgent
    from google.adk.sessions import InMemorySessionService
    from google.adk.memory import InMemoryMemoryService
    from google.adk.tools import google_search
    from google.adk.runners import Runner
    from google.genai import types

    # Initialize services
    _session_service = InMemorySessionService()
    _memory_service = InMemoryMemoryService()

    # Retry configuration
    retry_config = types.GenerateContentConfig(
        http_options=types.HttpOptions(timeout=120000)
    )

    # =========================
    # Agent 1: Resume Parser
    # =========================
    resume_parser = Agent(
        name="resume_parser",
        model=MODEL_FLASH,
        generate_content_config=retry_config,
        instruction=RESUME_PARSER_INSTRUCTION,
        tools=[calculate_yoe],
        output_key="parsed_resume"
    )

    # =========================
    # Agent 2: Level Classifier
    # =========================
    level_classifier = Agent(
        name="level_classifier",
        model=MODEL_FLASH,
        generate_content_config=retry_config,
        instruction=LEVEL_CLASSIFIER_INSTRUCTION,
        tools=[google_search],
        output_key="initial_level"
    )

    # =========================
    # Agents 3-4: A2A Deliberation
    # =========================
    conservative_evaluator = Agent(
        name="conservative_evaluator",
        model=MODEL_FLASH,
        generate_content_config=retry_config,
        instruction=CONSERVATIVE_EVALUATOR_INSTRUCTION,
        tools=[google_search],
        output_key="conservative_assessment"
    )

    optimistic_evaluator = Agent(
        name="optimistic_evaluator",
        model=MODEL_FLASH,
        generate_content_config=retry_config,
        instruction=OPTIMISTIC_EVALUATOR_INSTRUCTION,
        tools=[google_search],
        output_key="optimistic_assessment"
    )

    deliberation_agents = ParallelAgent(
        name="a2a_deliberation",
        sub_agents=[conservative_evaluator, optimistic_evaluator]
    )

    # =========================
    # Agent 5: Consensus
    # =========================
    consensus_agent = Agent(
        name="consensus",
        model=MODEL_PRO,
        generate_content_config=retry_config,
        instruction=CONSENSUS_INSTRUCTION,
        output_key="calibrated_level"
    )

    # =========================
    # Agents 6-9: Job Scouts (Batched 2+2)
    # =========================
    exact_match_scout = Agent(
        name="exact_match_scout",
        model=MODEL_FLASH,
        generate_content_config=retry_config,
        instruction=EXACT_MATCH_INSTRUCTION,
        tools=[google_search],
        output_key="exact_match_job"
    )

    level_up_scout = Agent(
        name="level_up_scout",
        model=MODEL_FLASH,
        generate_content_config=retry_config,
        instruction=LEVEL_UP_INSTRUCTION,
        tools=[google_search],
        output_key="level_up_job"
    )

    stretch_scout = Agent(
        name="stretch_scout",
        model=MODEL_FLASH,
        generate_content_config=retry_config,
        instruction=STRETCH_INSTRUCTION,
        tools=[google_search],
        output_key="stretch_job"
    )

    trajectory_scout = Agent(
        name="trajectory_scout",
        model=MODEL_FLASH,
        generate_content_config=retry_config,
        instruction=TRAJECTORY_INSTRUCTION,
        tools=[google_search],
        output_key="trajectory_job"
    )

    # Batched parallel scouts (2+2 for rate limit safety)
    parallel_batch_1 = ParallelAgent(
        name="job_scouts_batch_1",
        sub_agents=[exact_match_scout, level_up_scout]
    )

    parallel_batch_2 = ParallelAgent(
        name="job_scouts_batch_2",
        sub_agents=[stretch_scout, trajectory_scout]
    )

    batched_job_scouts = SequentialAgent(
        name="batched_job_scouts",
        sub_agents=[parallel_batch_1, parallel_batch_2]
    )

    # =========================
    # Agent 10: URL Validator
    # =========================
    url_validator_agent = Agent(
        name="url_validator",
        model=MODEL_LITE,
        generate_content_config=retry_config,
        instruction=URL_VALIDATOR_INSTRUCTION,
        tools=[check_job_urls],
        output_key="validated_jobs"
    )

    # =========================
    # Agent 11: Formatter
    # =========================
    formatter = Agent(
        name="formatter",
        model=MODEL_LITE,
        generate_content_config=retry_config,
        instruction=FORMATTER_INSTRUCTION,
        output_key="formatted_output"
    )

    # =========================
    # Main Pipeline
    # =========================
    _orchestrator = SequentialAgent(
        name="job_search_orchestrator",
        sub_agents=[
            resume_parser,
            level_classifier,
            deliberation_agents,
            consensus_agent,
            batched_job_scouts,
            url_validator_agent,
            formatter
        ]
    )

    # =========================
    # Refinement Pipeline (separate instances)
    # =========================
    exact_match_scout_ref = Agent(
        name="exact_match_scout_ref",
        model=MODEL_FLASH,
        generate_content_config=retry_config,
        instruction=EXACT_MATCH_INSTRUCTION,
        tools=[google_search],
        output_key="exact_match_job"
    )

    level_up_scout_ref = Agent(
        name="level_up_scout_ref",
        model=MODEL_FLASH,
        generate_content_config=retry_config,
        instruction=LEVEL_UP_INSTRUCTION,
        tools=[google_search],
        output_key="level_up_job"
    )

    stretch_scout_ref = Agent(
        name="stretch_scout_ref",
        model=MODEL_FLASH,
        generate_content_config=retry_config,
        instruction=STRETCH_INSTRUCTION,
        tools=[google_search],
        output_key="stretch_job"
    )

    trajectory_scout_ref = Agent(
        name="trajectory_scout_ref",
        model=MODEL_FLASH,
        generate_content_config=retry_config,
        instruction=TRAJECTORY_INSTRUCTION,
        tools=[google_search],
        output_key="trajectory_job"
    )

    parallel_batch_1_ref = ParallelAgent(
        name="job_scouts_batch_1_ref",
        sub_agents=[exact_match_scout_ref, level_up_scout_ref]
    )

    parallel_batch_2_ref = ParallelAgent(
        name="job_scouts_batch_2_ref",
        sub_agents=[stretch_scout_ref, trajectory_scout_ref]
    )

    batched_job_scouts_ref = SequentialAgent(
        name="batched_job_scouts_ref",
        sub_agents=[parallel_batch_1_ref, parallel_batch_2_ref]
    )

    url_validator_agent_ref = Agent(
        name="url_validator_ref",
        model=MODEL_LITE,
        generate_content_config=retry_config,
        instruction=URL_VALIDATOR_INSTRUCTION,
        tools=[check_job_urls],
        output_key="validated_jobs"
    )

    formatter_ref = Agent(
        name="formatter_refinement",
        model=MODEL_LITE,
        generate_content_config=retry_config,
        instruction=FORMATTER_INSTRUCTION,
        output_key="formatted_output"
    )

    _refinement_pipeline = SequentialAgent(
        name="refinement_orchestrator",
        sub_agents=[
            batched_job_scouts_ref,
            url_validator_agent_ref,
            formatter_ref
        ]
    )

    # =========================
    # Create Runners
    # =========================
    _runner = Runner(
        agent=_orchestrator,
        app_name="agentic_job_search",
        session_service=_session_service,
        memory_service=_memory_service
    )

    _refinement_runner = Runner(
        agent=_refinement_pipeline,
        app_name="agentic_job_search",
        session_service=_session_service,
        memory_service=_memory_service
    )

    print("✅ Pipeline initialized with full agentic flow")
    _pipeline_initialized = True


async def analyze_resume(
    resume_text: str,
    session_id: str = "default",
    progress_callback: Optional[Callable[[str, str], None]] = None,
    model_mode: str = "standard"
) -> str:
    """
    Run the full analysis pipeline on a resume with real-time streaming output.

    Args:
        resume_text: The raw text of the resume
        session_id: Session identifier for state management
        progress_callback: Optional callback(agent_name, preview) for streaming updates
        model_mode: "fast", "standard", or "deep" - controls model quality/speed

    Returns:
        Formatted job recommendations with explanations
    """
    global _runner, _session_service, _memory_service, _current_model_mode
    global MODEL_LITE, MODEL_FLASH, MODEL_PRO, MODEL_ID, _pipeline_initialized, _last_initialized_mode

    # Set the model mode for this analysis
    _current_model_mode = model_mode
    models = get_models(model_mode)
    mode_label = {"fast": "Fast", "standard": "Standard", "deep": "Deep"}.get(model_mode, "Standard")

    # Update global model variables based on mode
    MODEL_LITE = models["lite"]
    MODEL_FLASH = models["flash"]
    MODEL_PRO = models["pro"]
    MODEL_ID = MODEL_FLASH

    if progress_callback:
        progress_callback("system", f"📊 Using {mode_label} mode: {models['flash']} / {models['pro']}")

    # Only re-initialize if mode changed or not initialized
    if not _pipeline_initialized or _last_initialized_mode != model_mode:
        _pipeline_initialized = False
        _last_initialized_mode = model_mode
        await setup_pipeline()
    else:
        # Already initialized with correct mode
        pass

    from google.genai import types

    # PRE-CALCULATE YOE with detailed role breakdown
    yoe_result = calculate_yoe(resume_text)
    calculated_yoe = yoe_result.get("total_yoe", 0)
    stated_yoe = yoe_result.get("stated_yoe")
    avg_tenure = yoe_result.get("avg_tenure_years", 0)
    num_roles = yoe_result.get("num_roles", 0)
    career_span = yoe_result.get("career_span", "Unknown")

    # Send initial progress
    if progress_callback:
        progress_callback("career_analytics", f"📊 Total YOE: {calculated_yoe} years | Roles: {num_roles} | Avg tenure: {avg_tenure} years")
        if yoe_result.get("role_breakdown"):
            for role in yoe_result.get("role_breakdown", [])[:5]:
                progress_callback("role_breakdown", f"   • {role['start']} - {role['end']}: {role['duration_years']} years")

    # Inject detailed YOE into resume text
    yoe_note = f"""[SYSTEM NOTE - USE THESE EXACT VALUES:]
- Total Years of Experience: {calculated_yoe} years (calculated from dates, de-duped for overlapping roles)
- Career Span: {career_span}
- Number of Roles: {num_roles}
- Average Tenure: {avg_tenure} years per role
- Resume states: {stated_yoe}+ years (for reference)
"""
    enhanced_resume = f"{yoe_note}\n\n{resume_text}"

    # Get or create session
    try:
        await _session_service.create_session(
            app_name="agentic_job_search",
            user_id="user",
            session_id=session_id
        )
    except Exception:
        pass  # Session may already exist

    # Create the input message
    content = types.Content(
        role="user",
        parts=[types.Part(text=f"Analyze this resume and find job recommendations:\n\n{enhanced_resume}")]
    )

    # Agent labels for streaming
    agent_labels = {
        "resume_parser": "📄 Resume Parser",
        "level_classifier": "📊 Level Classifier",
        "conservative_evaluator": "🔍 Conservative Evaluator",
        "optimistic_evaluator": "🚀 Optimistic Evaluator",
        "consensus": "🤝 Consensus Agent",
        "exact_match_scout": "🎯 Exact Match Scout",
        "level_up_scout": "📈 Level Up Scout",
        "stretch_scout": "⭐ Stretch Scout",
        "trajectory_scout": "🔮 Trajectory Scout",
        "url_validator": "✅ URL Validator",
        "formatter": "📝 Formatter",
    }

    # Run pipeline with streaming
    final_response = "No response received from agent."
    seen_agents = set()

    async for event in _runner.run_async(
        user_id="user",
        session_id=session_id,
        new_message=content
    ):
        # Stream intermediate agent outputs
        if event.content and event.content.parts and event.author:
            agent_name = event.author

            if agent_name not in seen_agents:
                text = None
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        text = part.text
                        break

                if text:
                    seen_agents.add(agent_name)
                    preview = text[:150].replace("\n", " ").strip()
                    if len(text) > 150:
                        preview += "..."

                    label = agent_labels.get(agent_name, f"🤖 {agent_name}")

                    if progress_callback:
                        progress_callback(agent_name, f"{label}: {preview}")

        # Capture final response
        if event.is_final_response():
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        final_response = part.text
                        break

    return final_response


async def refine_results(
    feedback: str,
    session_id: str = "default",
    progress_callback: Optional[Callable[[str, str], None]] = None
) -> str:
    """
    Refine job recommendations based on user feedback with streaming output.

    Args:
        feedback: User's refinement request (e.g., "remote only", "no crypto")
        session_id: Same session to maintain state
        progress_callback: Optional callback for streaming updates

    Returns:
        Updated job recommendations
    """
    global _refinement_runner, _session_service

    if not _pipeline_initialized:
        await setup_pipeline()

    from google.genai import types

    # Ensure session exists
    try:
        await _session_service.create_session(
            app_name="agentic_job_search",
            user_id="user",
            session_id=session_id
        )
    except Exception:
        pass

    content = types.Content(
        role="user",
        parts=[types.Part(text=f"Refine job search with this feedback: {feedback}")]
    )

    agent_labels = {
        "exact_match_scout_ref": "🎯 Exact Match Scout",
        "level_up_scout_ref": "📈 Level Up Scout",
        "stretch_scout_ref": "⭐ Stretch Scout",
        "trajectory_scout_ref": "🔮 Trajectory Scout",
        "url_validator_ref": "✅ URL Validator",
        "formatter_refinement": "📝 Formatter",
    }

    final_response = "No response received from agent."
    seen_agents = set()

    async for event in _refinement_runner.run_async(
        user_id="user",
        session_id=session_id,
        new_message=content
    ):
        if event.content and event.content.parts and event.author:
            agent_name = event.author

            if agent_name not in seen_agents:
                text = None
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        text = part.text
                        break

                if text:
                    seen_agents.add(agent_name)
                    preview = text[:150].replace("\n", " ").strip()
                    if len(text) > 150:
                        preview += "..."

                    label = agent_labels.get(agent_name, f"🤖 {agent_name}")

                    if progress_callback:
                        progress_callback(agent_name, f"{label}: {preview}")

        if event.is_final_response():
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        final_response = part.text
                        break

    return final_response
