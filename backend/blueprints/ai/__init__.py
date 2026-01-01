from flask import Blueprint, jsonify, request
from langchain_community.chat_models import ChatPerplexity
from langchain_core.prompts import ChatPromptTemplate
from utils.constant import PLANET_PROFESSIONS
import json
import re
import os

ai_bp = Blueprint('ai', __name__)

# Initialize chat model
chat = ChatPerplexity(
    model="sonar-pro",
    temperature=0.7,
    pplx_api_key=os.getenv('PPLX_API_KEY')
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{question}")
])

chain = prompt | chat

def generate_profession_prediction(profession_data):
    """Generate profession prediction using AI based on planet and house connectivity"""
    
    # Build profession reference text
    profession_reference = ""
    for planet in ['mars', 'sun', 'jupiter', 'mercury', 'saturn', 'venus', 'moon']:
        planet_upper = planet.upper()
        professions_list = PLANET_PROFESSIONS.get(planet, [])
        if professions_list:
            profession_reference += f"\n{planet_upper}: {', '.join(professions_list)}\n"
    
    # Build the prompt with all the profession data
    prompt_text = f"""You are an expert Vedic astrologer. Based on the following astrological analysis, provide a profession prediction.

ANALYSIS DATA:
- Top Subathuva Planets (highest scoring benefic planets): {profession_data.get('top_subathuva_planets', [])}
- Profession-Determining Planet: {profession_data.get('profession_planet', 'Not determined')}
- Connection Reason: {profession_data.get('connection_reason', 'N/A')}
- 2nd House Lord (Wealth): {profession_data.get('house_2_lord', 'N/A')}
- 10th House Lord (Career): {profession_data.get('house_10_lord', 'N/A')}
- 11th House Lord (Gains): {profession_data.get('house_11_lord', 'N/A')}
- Planets in 2nd and 10th house from Moon: {profession_data.get('moon_related_planets', [])}
- Subathuva Houses (2nd, 10th, 11th): {profession_data.get('subathuva_houses', [])}
- Moon's 2nd House: {profession_data.get('moon_2nd_house', 'N/A')}
- Moon's 10th House: {profession_data.get('moon_10th_house', 'N/A')}

HOUSE CONNECTIVITY LOGIC:
1. The first two subathuva planets (from planet calculation) are considered.
2. If more than one planet is subathuvam, find the planet which is connected (present at, aspects, or house lord) to both 2nd house lord and 10th house lord.
3. If there is no common planet, consider the planet associated with the 10th lord.
4. If no planet with highest subathuvam is connected with 10th house, consider planets associated with 10th house (present at, aspects it, or house lord).
5. Consider planets present from the 2nd and 10th house from MOON as well.
6. Consider 2 or 3 houses subathuvam that coincide with the 2nd, 10th, and 11th house - add profession as per the house lord of that house.

VEDIC ASTROLOGY PROFESSION REFERENCE:
Use the following traditional Vedic astrology profession associations as your primary reference. Select professions ONLY from this list:

{profession_reference}

INSTRUCTIONS:
- Identify the main planet(s) that determine profession based on the connectivity rules above.
- Select 4-6 appropriate professions from the reference list above that match the identified planet(s).
- If multiple planets are identified, combine relevant professions from each planet's list.
- Prioritize professions that align with both the planetary combination and house combination (2nd, 10th, 11th houses).
- Use the exact profession names from the reference list above - do not create new professions.
- Keep the response professional and informative.

RESPONSE FORMAT:
You MUST respond with ONLY a valid JSON object in this exact format (no additional text, no markdown, just pure JSON):
{{
    "planets": ["planet1", "planet2", "planet3"],
    "professions": ["profession1", "profession2", "profession3", "profession4", "profession5", "profession6"]
}}

Example: 
{{
    "planets": ["JUPITER", "VENUS", "MERCURY"],
    "professions": ["Teaching", "Law", "Banking", "Arts", "Business", "Communication"]
}}

IMPORTANT: Return ONLY the JSON object, no markdown code blocks, no explanations, just the JSON.
"""
    
    try:
        response = chain.invoke({"question": prompt_text})
        content = response.content.strip()
        
        # Try to extract JSON from markdown code blocks if present
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
        else:
            # Try to find JSON object - look for opening brace and find matching closing brace
            brace_start = content.find('{')
            if brace_start != -1:
                brace_count = 0
                brace_end = -1
                for i in range(brace_start, len(content)):
                    if content[i] == '{':
                        brace_count += 1
                    elif content[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            brace_end = i + 1
                            break
                if brace_end > brace_start:
                    content = content[brace_start:brace_end]
        
        # Parse JSON
        try:
            profession_data = json.loads(content)
            # Validate structure
            if isinstance(profession_data, dict) and 'planets' in profession_data and 'professions' in profession_data:
                # Ensure planets and professions are lists
                if not isinstance(profession_data['planets'], list):
                    profession_data['planets'] = []
                if not isinstance(profession_data['professions'], list):
                    profession_data['professions'] = []
                # Filter out empty strings and ensure all are strings
                profession_data['planets'] = [str(p).strip().upper() for p in profession_data['planets'] if p and str(p).strip()]
                profession_data['professions'] = [str(p).strip() for p in profession_data['professions'] if p and str(p).strip()]
                return profession_data
            else:
                # Fallback: return empty structure
                return {"planets": [], "professions": []}
        except json.JSONDecodeError as e:
            # If JSON parsing fails, try to extract data manually
            # Fallback: return empty structure
            return {"planets": [], "professions": [], "error": f"JSON parsing error: {str(e)}"}
    except Exception as e:
        return {"planets": [], "professions": [], "error": str(e)}

@ai_bp.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    question = data.get("question", "").strip()
    
    if not question:
        return jsonify({"error": "Missing 'question' in request"}), 400
    
    try:
        response = chain.invoke({"question": question})
        return jsonify({
            "question": question,
            "answer": response.content
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

