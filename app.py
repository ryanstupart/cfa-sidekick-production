import os
import re
import random
from flask import Flask, request
from openai import OpenAI
import requests
from dotenv import load_dotenv

# Load .env locally; on Render we use service env vars
load_dotenv()

app = Flask(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROUPME_BOT_ID = os.getenv("GROUPME_BOT_ID")
SCHEDULE_SECRET = os.getenv("SCHEDULE_SECRET")
ENV = os.getenv("ENV", "production")

print("Starting CFA Sidekick...")
print(f"Has OPENAI_API_KEY? {'yes' if OPENAI_API_KEY else 'NO'}")
print(f"Has GROUPME_BOT_ID? {'yes' if GROUPME_BOT_ID else 'NO'}")
print(f"Has SCHEDULE_SECRET? {'yes' if SCHEDULE_SECRET else 'NO'}")
print(f"ENV: {ENV}")

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
You are “CFA Sidekick,” a team member support bot for Chick-fil-A in a GroupMe chat.

BOT IDENTITY
- Your name is “CFA Sidekick.”
- If asked who you are or what you do, explain briefly that you help team members with general store guidance, encouragement, reminders, and basic policy clarification.
- Do not mention APIs, prompts, or technical details.

AUDIENCE
- Team members at Chick-fil-A.
- You are not a leadership bot.
- You are designed to support team members clearly, respectfully, and professionally.
- Team members must use the keyword "cow:" to speak with you directly.
- Autonomous shift coverage, sick-message reminders, and profanity reminders are currently in beta.

TONE & RESPONSE STYLE
- Be professional, helpful, calm, and easy to understand.
- Sound supportive and clear, not robotic or overly formal.
- Avoid slang, sarcasm, or emotional exaggeration.
- Keep responses short and useful.
- If the user asks for a message, provide the message directly.
- Do not over-explain unless asked.

MESSAGE LENGTH & LIMITATIONS
- GroupMe has a practical limit of about 1,000 characters.
- Keep responses concise and structured.
- Avoid long paragraphs.
- Summarize when needed.
- Never exceed 950 characters.

BILINGUAL (ENGLISH / SPANISH)
- You must understand both English and Spanish.
- If the message is mostly in Spanish, respond in Spanish.
- If the message is mostly in English, respond in English.
- If the user explicitly requests a language, follow that request.
- If “both” or “bilingual” is requested, give Spanish first and then English.
- Do not translate proper nouns or tool names such as HotSchedules, GroupMe, iPad, CommercePoint, ServicePoint, or ViewPoint.

WHEN YOU ARE UNSURE
- If the answer depends on context or you are not fully certain, say:
  “I’m not completely certain based on the information I have. Please confirm with a leader.”
- For serious matters such as harassment, safety, injury, discrimination, theft, or HR issues:
  - Do not give detailed advice.
  - Direct the team member to a leader.

WHAT YOU CAN HELP WITH
You can help team members with:
1) General store policy reminders.
2) Uniform and readiness expectations.
3) Breaks, food policy, and drink policy.
4) Basic coverage process reminders.
5) Encouragement, quotes, and affirmations.
6) General CommercePoint knowledge.
7) Guest name expectations.
8) Basic health policy reminders.
9) Drafting simple respectful messages if asked.

STORE GUIDANCE & POLICY

1) RESPECT & CONDUCT
- “Guest first, always” applies to guests and team members.
- Treat everyone with honor, dignity, and respect.
- No bullying, harassment, intimidation, teasing, or throwing items.
- No hostile work environment.
- Profanity is prohibited.
- Concerns should be brought to a leader.

2) CLOCKING IN & READINESS
- Clock in only when fully ready:
  - Uniform complete
  - Shirt tucked
  - Belt on
  - Name tag attached
  - Personal items stored in a locker
- Clock in at front counter registers.
- Do not clock in and then finish getting ready.

3) UNIFORM & NAME TAGS
- Required:
  - Chick-fil-A polo
  - Oobe pants
  - Belt
  - Name tag
  - Approved non-slip shoes
- Missing name tag should be reported before clock-in.
- Replacement name tags cost $5.

4) PERSONAL DEVICES
- Phones are not allowed while working.
- General enforcement:
  - 1st offense: warning
  - 2nd offense: confiscation
  - Refusal: write-up and sent home
- Expo is held to a higher standard because of the trust level of that role.

5) DRINK POLICY
- One medium tea or fountain drink per shift.
- Premium drinks must be purchased.

6) BREAKS
- 5 or more hours: one 30-minute break.
- Under 5 hours: a 15-minute break may be allowed if business allows.

7) BREAK FOOD & DISCOUNTS
- Break food:
  - one entrée
  - one medium or small side
- Excludes:
  - 30-count nuggets
  - 10-count strips
- Off-the-clock discount:
  - 50% off one entrée and one side once per day
- Desserts and seasonal items are full price.

8) FOOD POLICY & WASTE
- Food is never free.
- Extra food must be purchased, logged as waste, or disposed of properly.
- Taking food without paying is not allowed.

9) SHIFT CHECK-IN
- Team members should check in with a leader at the start and end of each shift.

10) ATTENDANCE & COVERAGE
- Team members are responsible for finding coverage if they cannot work.
- Proper process includes:
  1) releasing the shift in HotSchedules
  2) asking in GroupMe
  3) waiting for leader approval
- Coverage must match the shift start time and required skill set.
- No-call/no-show leads to disciplinary action.
- Sick callouts require a doctor’s note.

11) MINORS (GEORGIA — 15-YEAR-OLDS)
When school is in session:
- Maximum 3 hours per school day
- Maximum 18 hours per school week
- Work window is 7 AM to 7 PM
- Cannot work or cover shifts past 7 PM
- Work permit required
When school is not in session:
- Up to 8 hours per day
- Up to 40 hours per week
- Cannot work before 7 AM

12) COMMERCEPOINT
- CommercePoint is Chick-fil-A’s in-house system for order taking and kitchen management.
- It includes:
  - ServicePoint (POS)
  - ViewPoint (KPS)
- Leaders and team members should be patient as everyone continues learning the system.
- Equipment should be handled carefully.
- If a device is damaged, it should be reported honestly and quickly.
- Clocking in and out happens in the Time Punch app, separate from SPFlex.

13) GUEST NAME STANDARD
- Guest name should be used once during order taking.
- Guest name should be used once during meal delivery.
- Guiding phrase:
  - “See the name, say the name.”
- Good examples:
  - “How may I serve you today, Marcus?”
  - “Have a great day, Sarah.”
  - “Brian, I’ve got your order right here.”
- Saying only the name by itself is not the standard.

14) HEALTH POLICY
- Team members should report to a leader or Person in Charge if they have symptoms such as:
  - vomiting
  - diarrhea
  - jaundice
  - sore throat with fever
  - lesions with pus / infected draining wound
- Team members should also report severe respiratory symptoms such as:
  - new loss of taste or smell
  - cough with shortness of breath
  - or three or more of the following:
    - fever
    - fatigue
    - chills
    - body aches
    - cough
- Team members diagnosed with certain illnesses such as Norovirus, Hepatitis A, Shigellosis, Salmonella, COVID-19, Tuberculosis, or Influenza A/B should report that to leadership.
- If sick, team members should not come in sick and should follow leader instructions and store policy.

ENCOURAGEMENT & AFFIRMATIONS
- If a team member asks for encouragement, inspiration, a quote, or positive words, provide it directly.
- Keep it professional, uplifting, and appropriate for a Chick-fil-A environment.
- Do not over-disclaim.

WHAT YOU MUST NOT DO
- Do not approve schedule changes or time off.
- Do not make disciplinary decisions.
- Do not give legal, HR, or medical advice.
- Redirect serious matters to a leader.

REMEMBER
- Your purpose is to support team members with clarity, encouragement, and general store guidance.
"""

DAILY_AFFIRMATIONS = [
    "Daily Affirmation: A welcoming tone matters as much as the words you say.",
    "Daily Affirmation: The next rush is a chance to show your preparation.",
    "Daily Affirmation: Make every guest feel seen and heard.",
    "Daily Affirmation: A great teammate notices the details others miss.",
    "Daily Affirmation: Be patient with yourself as you learn.",
    "Daily Affirmation: Service improves when we communicate early.",
    "Daily Affirmation: Your positive choices set an example.",
    "Daily Affirmation: Bring a fresh mindset to each new shift.",
    "Daily Affirmation: Even small tasks deserve careful attention.",
    "Daily Affirmation: Encourage the person working beside you.",
    "Daily Affirmation: A calm voice can make a busy moment easier.",
    "Daily Affirmation: Make kindness part of your routine.",
    "Daily Affirmation: You grow every time you practice a new skill.",
    "Daily Affirmation: Be proud of helping the team succeed.",
    "Daily Affirmation: Stay present for the guest in front of you.",
    "Daily Affirmation: Use feedback as a path to improvement.",
    "Daily Affirmation: A well-prepared station helps everyone.",
    "Daily Affirmation: One thoughtful question can prevent confusion.",
    "Daily Affirmation: Your attention can turn a mistake into a lesson.",
    "Daily Affirmation: The best teamwork begins with respect.",
    "Daily Affirmation: Let your actions reflect your values.",
    "Daily Affirmation: Show gratitude for the people around you.",
    "Daily Affirmation: Every shift is an opportunity to build confidence.",
    "Daily Affirmation: Take a moment to recognize a teammate's effort.",
    "Daily Affirmation: Good service includes a willingness to listen.",
    "Daily Affirmation: When plans change, stay flexible.",
    "Daily Affirmation: A strong finish starts with consistent effort.",
    "Daily Affirmation: Create a welcoming moment for the next guest.",
    "Daily Affirmation: You can make progress without rushing.",
    "Daily Affirmation: Help keep the team organized and ready.",
    "Daily Affirmation: Choose a respectful response under pressure.",
    "Daily Affirmation: Great habits are built one repetition at a time.",
    "Daily Affirmation: The little things are part of the big picture.",
    "Daily Affirmation: Make your next decision a thoughtful one.",
    "Daily Affirmation: Support your team with clear communication.",
    "Daily Affirmation: Your patience helps create a better environment.",
    "Daily Affirmation: A positive example is a powerful influence.",
    "Daily Affirmation: Learn from yesterday and focus on today.",
    "Daily Affirmation: Bring care and attention to every order.",
    "Daily Affirmation: Let your next interaction show genuine hospitality.",
    "Daily Affirmation: Trust grows when people follow through.",
    "Daily Affirmation: Ask for help when you need it.",
    "Daily Affirmation: Offer help when you can give it.",
    "Daily Affirmation: Every role is important to the guest experience.",
    "Daily Affirmation: Make time to acknowledge a job well done.",
    "Daily Affirmation: A good shift is built through cooperation.",
    "Daily Affirmation: You can improve a process by paying attention.",
    "Daily Affirmation: Approach challenges with curiosity.",
    "Daily Affirmation: Respect for teammates makes the work better.",
    "Daily Affirmation: The next small improvement starts with you.",
    "Daily Affirmation: Take pride in being ready when needed.",
    "Daily Affirmation: Be the teammate you would want beside you.",
    "Daily Affirmation: Make space for learning during a busy day.",
    "Daily Affirmation: The guest may remember your kindness most.",
    "Daily Affirmation: Good communication prevents unnecessary stress.",
    "Daily Affirmation: Bring your best attitude to the next task.",
    "Daily Affirmation: A difficult moment does not define your whole day.",
    "Daily Affirmation: Every careful step helps deliver quality.",
    "Daily Affirmation: Your willingness to adapt is valuable.",
    "Daily Affirmation: Focus on serving well, one order at a time.",
    "Daily Affirmation: Share what you know with patience.",
    "Daily Affirmation: Great teamwork includes giving others credit.",
    "Daily Affirmation: The work you do behind the scenes matters.",
    "Daily Affirmation: Stay focused and trust your training.",
    "Daily Affirmation: A simple thank-you strengthens a team.",
    "Daily Affirmation: You can be confident and still ask questions.",
    "Daily Affirmation: Take a fresh approach when something isn't working.",
    "Daily Affirmation: Your care helps create consistency.",
    "Daily Affirmation: Show up with a spirit of cooperation.",
    "Daily Affirmation: The next shift is another chance to improve.",
    "Daily Affirmation: Look for one way to make someone's day easier.",
    "Daily Affirmation: A steady attitude helps others stay steady.",
    "Daily Affirmation: Make hospitality a habit, not an exception.",
    "Daily Affirmation: A thoughtful handoff shows respect.",
    "Daily Affirmation: Keep growing through practice and reflection.",
    "Daily Affirmation: Your example can inspire a teammate.",
    "Daily Affirmation: Finish each task with care.",
    "Daily Affirmation: Choose to make the team stronger today.",
    "Daily Affirmation: Every guest interaction is an opportunity to serve.",
    "Daily Affirmation: End the day with gratitude for what you learned.",
    "Daily Affirmation: Every guest deserves to feel welcomed.",
    "Daily Affirmation: Your calm attitude can steady a busy shift.",
    "Daily Affirmation: Help a teammate before they have to ask.",
    "Daily Affirmation: Great service begins with listening.",
    "Daily Affirmation: A kind word can change someone's day.",
    "Daily Affirmation: Practice makes difficult tasks easier.",
    "Daily Affirmation: Focus on progress, not perfection.",
    "Daily Affirmation: A good handoff helps the whole team.",
    "Daily Affirmation: Today is another chance to grow.",
    "Daily Affirmation: Your preparation creates confidence.",
    "Daily Affirmation: Take pride in the little details.",
    "Daily Affirmation: Clear communication builds trust.",
    "Daily Affirmation: Your effort makes a real difference.",
    "Daily Affirmation: Stay curious and keep learning.",
    "Daily Affirmation: Show patience when the rush begins.",
    "Daily Affirmation: Each guest interaction is a fresh start.",
    "Daily Affirmation: Good habits build great teams.",
    "Daily Affirmation: Make room for kindness during busy moments.",
    "Daily Affirmation: Your reliability matters.",
    "Daily Affirmation: Be willing to learn from feedback.",
    "Daily Affirmation: Celebrate small improvements.",
    "Daily Affirmation: Lead through your actions.",
    "Daily Affirmation: Choose a solution-focused attitude.",
    "Daily Affirmation: Every shift teaches something valuable.",
    "Daily Affirmation: Bring care to routine tasks.",
    "Daily Affirmation: A thoughtful response is stronger than a rushed reaction.",
    "Daily Affirmation: You can encourage someone today.",
    "Daily Affirmation: Notice where your team needs help.",
    "Daily Affirmation: Hospitality is about people.",
    "Daily Affirmation: Give each task your attention.",
    "Daily Affirmation: Finish strong and with purpose.",
    "Daily Affirmation: Your professionalism shows under pressure.",
    "Daily Affirmation: Respect makes teamwork easier.",
    "Daily Affirmation: You can make a hard day better.",
    "Daily Affirmation: Growth begins with trying.",
    "Daily Affirmation: Keep your words constructive.",
    "Daily Affirmation: Patience and quality go together.",
    "Daily Affirmation: A smile can be meaningful.",
    "Daily Affirmation: Your best effort is worth giving.",
    "Daily Affirmation: Stay flexible and ready to help.",
    "Daily Affirmation: Careful work prevents avoidable mistakes.",
    "Daily Affirmation: Thank a teammate who helped you.",
    "Daily Affirmation: The next guest deserves your best.",
    "Daily Affirmation: Show up ready to contribute.",
    "Daily Affirmation: Good teamwork takes everyone.",
    "Daily Affirmation: Take ownership and keep moving.",
    "Daily Affirmation: Learn one new thing today.",
    "Daily Affirmation: A steady pace can beat a frantic rush.",
    "Daily Affirmation: Every role contributes to great service.",
    "Daily Affirmation: Choose encouragement over criticism.",
    "Daily Affirmation: Small moments create lasting impressions.",
    "Daily Affirmation: Trust is earned through consistency.",
    "Daily Affirmation: You are capable of improving.",
    "Daily Affirmation: Serve with confidence and humility.",
    "Daily Affirmation: Make your station better for the next person.",
    "Daily Affirmation: Stay focused on what matters.",
    "Daily Affirmation: Recognize your progress today.",
    "Daily Affirmation: Listen before you respond.",
    "Daily Affirmation: Support someone who is learning.",
    "Daily Affirmation: Your attitude can lift the whole team.",
    "Daily Affirmation: Treat people with dignity.",
    "Daily Affirmation: Keep your standards high and your tone kind.",
    "Daily Affirmation: A challenge is an opportunity to practice.",
    "Daily Affirmation: Good service starts with preparation.",
    "Daily Affirmation: Make every interaction count.",
    "Daily Affirmation: Bring positive energy to the team.",
    "Daily Affirmation: Your care is part of the guest experience.",
    "Daily Affirmation: Stay composed and communicate.",
    "Daily Affirmation: Build confidence one shift at a time.",
    "Daily Affirmation: Take pride in helping others succeed.",
    "Daily Affirmation: Be thoughtful even when you're busy.",
    "Daily Affirmation: Make today a little better than yesterday.",
    "Daily Affirmation: Your contribution is valuable.",
    "Daily Affirmation: Keep improving the way you serve.",
    "Daily Affirmation: One small kindness can have a big impact.",
    "Daily Affirmation: Be dependable in the details.",
    "Daily Affirmation: Help create a welcoming workplace.",
    "Daily Affirmation: Take time to appreciate a team win.",
    "Daily Affirmation: You can reset your mindset at any moment.",
    "Daily Affirmation: Strong teams support each other.",
    "Daily Affirmation: Show up with purpose. Small moments of consistency create big results.",
    "Daily Affirmation: You do not need to be perfect to make a positive difference today.",
    "Daily Affirmation: A calm attitude and steady effort can change the entire shift.",
    "Daily Affirmation: Stay focused, stay kind, and keep moving forward.",
    "Daily Affirmation: The way you carry yourself matters more than you think.",
    "Daily Affirmation: You can bring value to the team just by staying present and dependable.",
    "Daily Affirmation: Strong days are built on small choices made well.",
    "Daily Affirmation: Keep your standards high and your attitude steady.",
    "Daily Affirmation: Progress comes from consistency, not just motivation.",
    "Daily Affirmation: Do the next right thing and let momentum build from there.",
    "Daily Affirmation: Your effort today can make someone else’s day easier.",
    "Daily Affirmation: Stay patient with yourself while still giving your best.",
    "Daily Affirmation: You are stronger when you stay steady under pressure.",
    "Daily Affirmation: A good shift starts with a good mindset.",
    "Daily Affirmation: You do not have to rush to be effective. Stay clear and focused.",
    "Daily Affirmation: Excellence is often simple: be on time, be ready, be consistent.",
    "Daily Affirmation: The standard gets stronger every time you choose to uphold it.",
    "Daily Affirmation: Your presence, attitude, and work ethic all speak before you do.",
    "Daily Affirmation: Stay disciplined in the little things and the bigger things get easier.",
    "Daily Affirmation: One strong choice can reset the tone of your whole day.",
    "Daily Affirmation: Being dependable is a powerful form of leadership.",
    "Daily Affirmation: Keep your composure. Calm is strength.",
    "Daily Affirmation: The team gets better when each person takes ownership.",
    "Daily Affirmation: You can be both kind and committed to the standard.",
    "Daily Affirmation: Build trust today by doing what you said you would do.",
    "Daily Affirmation: Stay grounded, stay respectful, and do your part well.",
    "Daily Affirmation: Confidence grows when preparation and effort meet.",
    "Daily Affirmation: Keep going. Consistency always compounds.",
    "Daily Affirmation: There is value in doing ordinary things with excellence.",
    "Daily Affirmation: Take pride in being reliable. Reliability is rare and valuable.",
    "Daily Affirmation: A strong mindset helps you serve with clarity and patience.",
    "Daily Affirmation: You are more capable than one hard moment can make you feel.",
    "Daily Affirmation: Stay teachable. Growth follows humility.",
    "Daily Affirmation: Good habits make hard days easier to handle.",
    "Daily Affirmation: The standard is not there to limit you. It is there to strengthen you.",
    "Daily Affirmation: Bring energy, not drama. Bring focus, not excuses.",
    "Daily Affirmation: You can choose discipline even when motivation is low.",
    "Daily Affirmation: Respect, consistency, and effort never go out of style.",
    "Daily Affirmation: Keep building the version of yourself that can handle more.",
    "Daily Affirmation: Strong character shows in how you respond when no one is watching.",

]

INTRO_NOTE = (
    "Hey team — I’m CFA Sidekick. I’m here to help with general store guidance, encouragement, "
    "CommercePoint questions, health policy reminders, and policy guidance. To talk to me directly, "
    "use 'cow:' at the beginning of your message. I can also respond automatically to some shift "
    "coverage-related messages and some sick-message situations, and those autonomous features are "
    "currently in beta. Please do not abuse or overuse me. Use me for serious or useful questions only. "
    "If you notice issues, feedback, or problems, please let the owner know. I am up to date as of "
    "April 11th, 2026."
)


UPDATE_ANNOUNCEMENT = "🐮 Hey team! CFA Sidekick here! I've just received an update with smarter shift-coverage recognition and a fresh bank of 200 daily affirmations. I'm still improving, and some automatic features remain in beta. Thanks for your feedback and for letting me be part of the team. Have a great day! 🐄"

POLICY_ANNOUNCEMENT = (
    "🐮 CFA Sidekick | Friendly Team Reminders\n"
    "📱 Phones: Personal phone use is not allowed while working. If you need "
    "to use your phone or make a call, notify a leader and step into the designated area.\n"
    "💬 Language: No profanity or foul language at work or in the team chat.\n"
    "📅 Coverage: If you can't work a shift, release it in HotSchedules, find "
    "qualified coverage, and get leader approval. Unless an applicable exception "
    "applies, you remain responsible until coverage is approved.\n"
    "🤒 Illness: Notify a leader or Person in Charge promptly, follow food-safety "
    "requirements, and provide a doctor's note if required under applicable policy. "
    "Do not work with symptoms requiring exclusion.\n"
    "🥤 Food and drinks: No eating or drinking at the drive-through window or "
    "in designated drive-through work areas during operating hours.\n"
    "Thank you, team. Have a great day!"
)

COVERAGE_REMINDER = (
    "Coverage Reminder: Team members are responsible for finding coverage by releasing the shift in HotSchedules, "
    "asking in GroupMe, and securing leader approval. Coverage must match the exact start time and required skill set. "
    "If no coverage is found, the shift remains the team member’s responsibility unless there is a legitimate emergency."
)

SICK_REMINDER = (
    "I’m sorry you’re not feeling well. I hope you feel better soon. If you’re sick, please do not come in for your shift. "
    "Team members are responsible for finding coverage. Please release your shift, ask in the chat, and bring a doctor’s note if needed."
)

PROFANITY_RESPONSE = (
    "Reminder: Please keep this chat professional. Cursing is not permitted in the store or in this chat. "
    "Thank you for helping maintain a respectful environment."
)

PROFANITY_WORDS = [
    "fuck", "fucking", "fucked", "shit", "shitty", "bullshit", "bitch", "bitches",
    "asshole", "ass", "dumbass", "jackass", "bastard","goddamn", "damn", "hell", "wtf", "wth",
    "stfu", "mf", "motherfucker", "motherfucking", "pissed off", "crap", "screw you",
    "puta", "puto", "putos", "putas", "mierda", "chingar", "chingado", "chingada",
    "chingados", "chingadas", "pendejo", "pendeja", "pendejos", "pendejas",
    "cabron", "cabrón", "cabrona", "cabrones", "pinche", "verga", "no mames",
    "no mms", "wey", "guey", "vale madre", "vale madres", "chingon", "chingón"
]

def is_coverage_trigger(text: str) -> bool:
    t = text.lower().replace("’", "'")
    t = re.sub(r"\b(tmr|tmrw|2morrow)\b", "tomorrow", t)
    t = re.sub(r"\b(tdy|2day)\b", "today", t)
    t = re.sub(r"\s+", " ", t)
    day = r"(?:today|tomorrow|tonight|mon(?:day)?|tues?(?:day)?|wed(?:nesday)?|thu(?:rs(?:day)?)?|fri(?:day)?|sat(?:urday)?|sun(?:day)?)"
    times = r"\b\d{1,2}(?::\d{2})?\s*(?:-|–|—|to)\s*\d{1,2}(?::\d{2})?\b"
    context = rf"(?:\b(?:shift|work|schedule|hours|{day})\b|{times})"
    request = r"\b(?:anyone|anybody|someone|somebody)\b.{0,70}\b(?:take|cover|swap|switch|trade|pick up|pickup|work)\b|\b(?:need coverage|cover my|take my|swap my|switch my|trade my|pick up my|pickup my|shift covered)\b"
    inability = r"\b(?:i\s+)?(?:can't|cant|cannot|won't|wont|unable to|not able to)\s+(?:work|make|come|do|attend)\b"
    return bool(re.search(request, t) or (re.search(inability, t) and re.search(context, t)))


SICK_PATTERNS = [
    r"\bi[’']?m sick\b",
    r"\bim sick\b",
    r"\bi am sick\b",
    r"\bi[’']?m not feeling well\b",
    r"\bim not feeling well\b",
    r"\bi am not feeling well\b",
    r"\bi don[’']?t feel well\b",
    r"\bi dont feel well\b",
    r"\bi have a fever\b",
    r"\bi[’']?m throwing up\b",
    r"\bim throwing up\b",
    r"\bi have diarrhea\b",
    r"\bi[’']?m vomiting\b",
    r"\bim vomiting\b",
    r"\bi[’']?m nauseous\b",
    r"\bim nauseous\b",
    r"\bi[’']?m not feeling good\b",
    r"\bim not feeling good\b",
    r"\bi can[’']?t make my shift because i[’']?m sick\b",
    r"\bi cant make my shift because im sick\b",
    r"\bi can[’']?t make it because i[’']?m sick\b",
    r"\bi cant make it because im sick\b",
]

def send_groupme_message(text: str) -> None:
    if not GROUPME_BOT_ID:
        print("ERROR: GROUPME_BOT_ID is missing, cannot send message.")
        return

    url = "https://api.groupme.com/v3/bots/post"
    payload = {"bot_id": GROUPME_BOT_ID, "text": text[:995]}
    print(f"Sending message to GroupMe: {payload}")

    try:
        resp = requests.post(url, json=payload, timeout=15)
        print(f"GroupMe response status: {resp.status_code}, body: {resp.text}")
    except Exception as e:
        print(f"Error sending message to GroupMe: {e}")

def matches_patterns(text: str, patterns: list[str]) -> bool:
    lower_text = text.lower().strip()
    return any(re.search(pattern, lower_text) for pattern in patterns)

def contains_profanity(text: str) -> bool:
    lower = text.lower()
    return any(re.search(r"(?<!\w)" + re.escape(word) + r"(?!\w)", lower) for word in PROFANITY_WORDS)

@app.route("/", methods=["GET", "HEAD"])
def health_check():
    return "CFA Sidekick is running", 200

@app.route("/groupme_callback", methods=["GET", "POST"])
def groupme_callback():
    if request.method == "GET":
        print("Received GET /groupme_callback")
        return "groupme_callback is alive", 200

    data = request.json or {}
    # Avoid logging team member messages.

    text = data.get("text", "") or ""
    sender_type = data.get("sender_type", "")

    if sender_type == "bot":
        return "ok", 200

    if not text.strip():
        return "ok", 200

    if contains_profanity(text):
        send_groupme_message(PROFANITY_RESPONSE)
        return "ok", 200

    if matches_patterns(text, SICK_PATTERNS):
        send_groupme_message(SICK_REMINDER)
        return "ok", 200

    if is_coverage_trigger(text):
        send_groupme_message(COVERAGE_REMINDER)
        return "ok", 200

    if not text.lower().startswith("cow:"):
        return "ok", 200

    user_question = text[len("cow:"):].strip()


    if not OPENAI_API_KEY:
        send_groupme_message("CFA Sidekick error: OPENAI_API_KEY missing.")
        return "ok", 200

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_question},
            ],
            temperature=0.2,
        )

        ai_response = completion.choices[0].message.content

        send_groupme_message(ai_response)

    except Exception as e:
        print("Error calling OpenAI:", repr(e))
        send_groupme_message(
            "CFA Sidekick had an error processing that request. Please let a leader know."
        )

    return "ok", 200

@app.route("/scheduled/send", methods=["GET"])
def scheduled_send():
    token = request.args.get("token", "")
    kind = (request.args.get("kind", "") or "").lower().strip()

    if not SCHEDULE_SECRET or token != SCHEDULE_SECRET:
        return "Unauthorized", 401

    if kind == "affirmation":
        msg = random.choice(DAILY_AFFIRMATIONS)
    else:
        return "Bad Request: kind must be affirmation", 400

    send_groupme_message(msg)
    return "OK", 200

@app.route("/scheduled/intro", methods=["GET"])
def scheduled_intro():
    token = request.args.get("token", "")
    if not SCHEDULE_SECRET or token != SCHEDULE_SECRET:
        return "Unauthorized", 401

    send_groupme_message(INTRO_NOTE)
    return "OK", 200


@app.route("/scheduled/update-announcement", methods=["GET"])
def scheduled_update_announcement():
    token = request.args.get("token", "")
    if not SCHEDULE_SECRET or token != SCHEDULE_SECRET:
        return "Unauthorized", 401
    send_groupme_message(UPDATE_ANNOUNCEMENT)
    return "OK", 200

@app.route("/scheduled/policy-reminders", methods=["GET"])
def scheduled_policy_reminders():
    token = request.args.get("token", "")
    if not SCHEDULE_SECRET or token != SCHEDULE_SECRET:
        return "Unauthorized", 401
    send_groupme_message(POLICY_ANNOUNCEMENT)
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
