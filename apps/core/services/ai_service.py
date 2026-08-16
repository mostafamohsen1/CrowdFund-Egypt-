"""
CrowdFund Egypt - Generative AI Service
---------------------------------------
Handles live project data context retrieval, conversation formatting,
and communication with Free-tier AI Providers (Google Gemini API & Groq).
"""

import json
import logging
import requests
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from django.db.models import Avg, Sum, Count

from apps.projects.models import Project, Category, Tag

logger = logging.getLogger(__name__)


def build_crowdfund_context():
    """
    Queries live Django database to create structured context about
    current campaigns, categories, and platform rules.
    """
    now = timezone.now()
    
    # 1. Categories
    categories = Category.objects.annotate(project_count=Count('projects')).all()
    cat_summary = []
    for cat in categories:
        cat_summary.append(f"- {cat.name}: {cat.project_count} campaigns ({cat.description})")
    categories_text = "\n".join(cat_summary) if cat_summary else "No categories yet."

    # 2. Active Projects
    active_projects = Project.objects.filter(
        is_cancelled=False
    ).select_related('category', 'creator').prefetch_related('tags', 'ratings').order_by('-created_at')

    projects_summary = []
    total_funds = Decimal('0.00')

    for p in active_projects:
        total_funds += p.current_donations
        pct = p.percentage_raised
        days_left = p.days_left
        status = "Active" if p.is_running else ("Ended" if now > p.end_time else "Upcoming")
        tags_list = ", ".join([f"#{t.name}" for t in p.tags.all()])
        avg_rating = p.average_rating
        
        projects_summary.append(
            f"• Title: {p.title}\n"
            f"  Category: {p.category.name}\n"
            f"  Target: {p.total_target:,.2f} EGP | Raised: {p.current_donations:,.2f} EGP ({pct}% funded)\n"
            f"  Status: {status} ({days_left} days left)\n"
            f"  Rating: {avg_rating}/5.0 stars\n"
            f"  Tags: {tags_list or 'None'}\n"
            f"  Creator: {p.creator.get_full_name()} ({p.creator.email})\n"
            f"  Direct Link: /projects/{p.slug}/\n"
            f"  Summary: {p.details[:180]}..."
        )

    projects_text = "\n\n".join(projects_summary) if projects_summary else "No campaigns currently active."

    # 3. Overall Stats
    total_count = active_projects.count()
    stats_text = f"Total Active Campaigns: {total_count} | Total Funds Raised: {total_funds:,.2f} EGP"

    # 4. Assembled System Instructions
    system_instruction = f"""You are 'Masry Fund AI' (مساعد كراود فند مصر), the friendly, knowledgeable, and helpful AI assistant for CrowdFund Egypt — a leading crowdfunding platform empowering impactful Egyptian projects, charities, tech innovations, and cultural revivals.

CURRENT PLATFORM REAL-TIME DATA:
--------------------------------
{stats_text}

AVAILABLE CATEGORIES:
{categories_text}

LIVE CAMPAIGNS IN SYSTEM:
{projects_text}

PLATFORM RULES & CAPABILITIES:
1. Donating: Users must be logged in to donate. Donations are in Egyptian Pounds (EGP).
2. Starting a Campaign: Logged-in users can create campaigns via '/projects/create/' by setting a target (min 10 EGP), start & end date, category, cover image, and details.
3. Cancellation Policy: A project creator can cancel their campaign ONLY if current donations are LESS THAN 25% of the total target.
4. Ratings & Comments: Community members can rate campaigns (1 to 5 stars) and post comments/replies.
5. Search & Filters: Users can search by title, details, or #tags, and filter by category or sort by target/popularity.

YOUR BEHAVIOR GUIDELINES:
- Greet users warmly and speak as the official CrowdFund Egypt assistant.
- When recommending campaigns, use the EXACT data (titles, targets in EGP, current raised %, direct URLs) from the LIVE CAMPAIGNS above.
- Always include the campaign link in markdown format, e.g. [Title](/projects/slug/) so users can click directly to the campaign.
- Answer questions in the language the user asks (Egyptian Arabic / Arabic or English).
- Be concise, inspiring, clear, and accurate. Do NOT invent fake campaigns or fake numbers.
- If asked how to start a campaign or donate, guide them step-by-step based on platform rules.
"""
    return system_instruction, {
        'total_count': total_count,
        'total_funds': float(total_funds),
        'projects': list(active_projects)
    }


def call_gemini_api(api_key, model_name, system_instruction, user_message, conversation_history=None):
    """
    Calls Google Gemini REST API with system context, user message, and chat history.
    Includes automatic model fallback for maximum resilience.
    """
    candidate_models = [model_name or 'gemini-3.6-flash', 'gemini-flash-latest', 'gemini-3.5-flash']
    # Deduplicate while preserving order
    seen = set()
    models_to_try = [m for m in candidate_models if m and not (m in seen or seen.add(m))]

    contents = []
    
    # Add previous turns
    if conversation_history:
        for turn in conversation_history:
            role = turn.get('role')
            content = turn.get('content', '').strip()
            if not content:
                continue
            gemini_role = "user" if role == "user" else "model"
            contents.append({
                "role": gemini_role,
                "parts": [{"text": content}]
            })
    
    # Add current user prompt
    contents.append({
        "role": "user",
        "parts": [{"text": user_message}]
    })

    payload = {
        "contents": contents,
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        },
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 800,
            "topP": 0.95
        }
    }

    headers = {"Content-Type": "application/json"}
    
    last_error = None
    for model in models_to_try:
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                candidates = data.get('candidates', [])
                if candidates:
                    parts = candidates[0].get('content', {}).get('parts', [])
                    if parts and 'text' in parts[0]:
                        return parts[0]['text']
                return "I received your message, but I couldn't generate a full answer right now. Please try again."
            
            elif response.status_code == 404:
                # Model name not found on this endpoint, try next candidate model
                continue
                
            elif response.status_code == 400:
                error_msg = response.json().get('error', {}).get('message', 'Invalid request or API key.')
                logger.error(f"Gemini API 400 Error: {error_msg}")
                raise ValueError(f"Gemini API Error: {error_msg}")
            
            elif response.status_code == 429:
                logger.warning("Gemini API Rate Limit hit.")
                raise RuntimeError("The AI rate limit was reached. Please wait a moment and try again.")
            
            else:
                last_error = f"HTTP {response.status_code}"
        except requests.RequestException as e:
            last_error = str(e)
            continue

    raise RuntimeError(f"AI service temporarily unavailable ({last_error or 'no response'}).")


def call_groq_api(api_key, model_name, system_instruction, user_message, conversation_history=None):
    """
    Calls Groq OpenAI-compatible Chat Completions REST API.
    """
    endpoint = "https://api.groq.com/openai/v1/chat/completions"
    
    messages = [{"role": "system", "content": system_instruction}]
    
    if conversation_history:
        for turn in conversation_history:
            role = turn.get('role')
            content = turn.get('content', '').strip()
            if content and role in ('user', 'assistant'):
                messages.append({"role": role, "content": content})
                
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": model_name or "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 800
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    response = requests.post(endpoint, json=payload, headers=headers, timeout=15)
    
    if response.status_code == 200:
        data = response.json()
        choices = data.get('choices', [])
        if choices and 'message' in choices[0]:
            return choices[0]['message'].get('content', '')
        return "I received your message, but no content was returned."
    elif response.status_code == 429:
        raise RuntimeError("Groq API rate limit reached. Please try again in a few seconds.")
    else:
        raise RuntimeError(f"Groq API returned status {response.status_code}.")


def generate_smart_fallback(user_message, context_meta):
    """
    Intelligent local fallback assistant that queries live database objects
    when no API key is provided or when external network is unreachable.
    """
    msg_lower = user_message.lower()
    projects = context_meta.get('projects', [])
    
    # 1. Cancellation Policy (Check specific policy intent first)
    if any(k in msg_lower for k in ['cancel', 'cancellation', 'delete', 'الغاء', 'حذف']):
        return (
            "### Campaign Cancellation Policy:\n"
            "• Project creators can cancel their campaign from their project detail page.\n"
            "• **Important Rule**: Cancellation is only allowed if current donations are **less than 25%** of the total fundraising goal.\n"
            "• Once donations reach or exceed 25%, the campaign is committed to completion for investor protection."
        )

    # 2. How to start / create campaign
    if any(k in msg_lower for k in ['create', 'start', 'launch', 'new campaign', 'how to start', 'انشاء', 'حملة جديدة']):
        return (
            "### How to Start a Campaign on CrowdFund Egypt:\n"
            "1. **Log in** to your account (or register if new).\n"
            "2. Click on **[+ Start Campaign](/projects/create/)** in the navigation bar.\n"
            "3. Fill in your campaign details (Title, Category, Funding Target in EGP, Start & End Date).\n"
            "4. Upload a high-quality cover image and photo gallery to build trust.\n"
            "5. Submit to launch your campaign live across Egypt!"
        )

    # 3. How to donate / rate
    if any(k in msg_lower for k in ['how to donate', 'donation rule', 'how to rate', 'تبرع']):
        return (
            "### How to Support a Campaign:\n"
            "• Open any campaign page and click **Donate Now** to contribute in Egyptian Pounds (EGP).\n"
            "• You can also leave a 1 to 5 star rating and comment to encourage the creators."
        )

    # 4. Asking for recommendations or list of campaigns
    if any(k in msg_lower for k in ['recommend', 'campaign', 'project', 'show me', 'list', 'help', 'suggest', 'solar', 'health', 'tech', 'education', 'مشاريع', 'حملات']):
        # Filter by keywords
        matched = []
        for p in projects:
            p_text = f"{p.title} {p.category.name} {p.details}".lower()
            if any(term in p_text for term in msg_lower.split() if len(term) > 2):
                matched.append(p)
                
        if not matched:
            matched = projects[:3]
            
        items = []
        for p in matched[:3]:
            items.append(f"• **[{p.title}](/projects/{p.slug}/)** ({p.category.name})\n  Raised: **{p.current_donations:,.0f} EGP** of {p.total_target:,.0f} EGP ({p.percentage_raised}%)\n  *\"{p.details[:120]}...\"*")
            
        campaigns_str = "\n\n".join(items)
        return (
            f"Here are top impactful campaigns from CrowdFund Egypt matching your interest:\n\n"
            f"{campaigns_str}\n\n"
            f"💡 *You can click any campaign link to view details and donate!*"
        )

    # 5. General Greeting & Introduction
    return (
        f"Hello! I am **Masry Fund AI**, your CrowdFund Egypt assistant. 🇪🇬\n\n"
        f"I can help you:\n"
        f"- Discover active campaigns across {context_meta.get('total_count', 0)} active projects\n"
        f"- Find high-impact initiatives in Technology, Health, Education, Environment, and Arts\n"
        f"- Understand platform policies (donations, ratings, campaign creation, cancellation)\n\n"
        f"How can I assist your crowdfunding journey today?"
    )


def generate_chat_response(user_message, conversation_history=None):
    """
    Main entry point for AI chatbot response generation.
    Retrieves live project context, selects AI provider, and handles fallbacks.
    """
    user_message = (user_message or '').strip()
    if not user_message:
        return "Please enter a message or question."

    # Build live database context
    system_instruction, context_meta = build_crowdfund_context()

    provider = getattr(settings, 'AI_PROVIDER', 'gemini').lower()
    gemini_key = getattr(settings, 'GEMINI_API_KEY', '').strip()
    groq_key = getattr(settings, 'GROQ_API_KEY', '').strip()
    model_name = getattr(settings, 'AI_MODEL', 'gemini-2.5-flash').strip()

    # Try Google Gemini API
    if provider == 'gemini' and gemini_key and gemini_key != 'your_gemini_api_key_here':
        try:
            return call_gemini_api(
                api_key=gemini_key,
                model_name=model_name or 'gemini-2.5-flash',
                system_instruction=system_instruction,
                user_message=user_message,
                conversation_history=conversation_history
            )
        except Exception as e:
            logger.warning(f"Gemini API invocation failed ({e}). Attempting fallback.")
            # If Gemini fails, fallback to Groq if key exists, or smart fallback
            if groq_key:
                try:
                    return call_groq_api(
                        api_key=groq_key,
                        model_name='llama-3.3-70b-versatile',
                        system_instruction=system_instruction,
                        user_message=user_message,
                        conversation_history=conversation_history
                    )
                except Exception:
                    pass
            return generate_smart_fallback(user_message, context_meta)

    # Try Groq API
    elif provider == 'groq' and groq_key:
        try:
            return call_groq_api(
                api_key=groq_key,
                model_name=model_name or 'llama-3.3-70b-versatile',
                system_instruction=system_instruction,
                user_message=user_message,
                conversation_history=conversation_history
            )
        except Exception as e:
            logger.warning(f"Groq API invocation failed ({e}). Attempting fallback.")
            return generate_smart_fallback(user_message, context_meta)

    # If no API key configured, use live data smart fallback assistant
    return generate_smart_fallback(user_message, context_meta)
