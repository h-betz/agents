import asyncio
import httpx
import json
import os
import re
import sys
from bs4 import BeautifulSoup
from claude_agent_sdk import query, ClaudeAgentOptions
from google_integrations.google_docs import GoogleDocsManager


options = ClaudeAgentOptions(
    system_prompt="""
    You are a helpful assistant tasked with helping me manage my recipes.
    """,
    permission_mode="bypassPermissions",
)
# We'll use httpx async client instead

RECIPE_SCHEMA = {
    "recipe_name": "",
    "ingredients": [],
    "steps": [],
    "notes": [],
    "cook_time": "",
    "prep_time": "",
    "total_time": "",
}


async def fetch_html_content(recipe_url):
    """Fetch HTML content from the recipe URL."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(recipe_url, headers=headers)
        print(f"Reponse [{response.status_code}]")
        return response.text


def extract_recipe_content(html_content):
    """Extract recipe-relevant content from HTML using BeautifulSoup."""
    soup = BeautifulSoup(html_content, "html.parser")
    extracted_parts = []

    # Strategy 1: Try to find JSON-LD structured data (most reliable)
    json_ld_scripts = soup.find_all("script", type="application/ld+json")
    for script in json_ld_scripts:
        if script.string and "recipe" in script.string.lower():
            extracted_parts.append(f"JSON-LD Recipe Data:\n{script.string}\n")

    # Strategy 2: Search for common recipe-related elements
    # Look for ingredients
    ingredient_patterns = re.compile(r"ingredient|recipe-ingredient", re.I)
    ingredient_sections = soup.find_all(
        ["ul", "ol", "div", "section"], class_=ingredient_patterns
    )
    for section in ingredient_sections[:3]:  # Limit to first 3 matches
        extracted_parts.append(f"Ingredients Section:\n{section.get_text()}\n")

    # Look for instructions/steps
    instruction_patterns = re.compile(
        r"instruction|step|direction|method|preparation", re.I
    )
    instruction_sections = soup.find_all(
        ["ol", "ul", "div", "section"], class_=instruction_patterns
    )
    for section in instruction_sections[:3]:  # Limit to first 3 matches
        extracted_parts.append(f"Instructions Section:\n{section.get_text()}\n")

    # Look for recipe metadata (times, servings, etc.)
    meta_patterns = re.compile(r"time|serving|yield|difficulty", re.I)
    meta_sections = soup.find_all(["div", "span", "p"], class_=meta_patterns)
    for section in meta_sections[:5]:  # Limit to first 5 matches
        extracted_parts.append(f"Metadata:\n{section.get_text()}\n")

    # Look for recipe title/name
    title = soup.find("h1")
    if title:
        extracted_parts.insert(0, f"Recipe Title:\n{title.get_text()}\n")

    # If we found content, return it; otherwise return truncated HTML
    if extracted_parts:
        content = "\n".join(extracted_parts)
        print(f"Extracted {len(content)} characters of recipe content")
        return content
    else:
        # Fallback: return first 150KB of HTML
        print("No specific recipe sections found, using truncated HTML")
        return html_content[:150000]


def create_extraction_prompt(recipe_content):
    """Create the prompt for Claude to extract recipe information."""
    return f"""
    Please extract recipe information from the following content.
    This content has been extracted from a recipe webpage and may contain
    ingredients, instructions, prep time, cook time, and other recipe details.

    Content:
    {recipe_content}

    Return the information in JSON format matching this exact schema:

    {{
        "recipe_name": "string",
        "ingredients": ["list", "of", "ingredients"],
        "steps": ["list", "of", "cooking", "steps"],
        "notes": ["any", "additional", "notes"],
        "cook_time": "string (e.g., '30 minutes')",
        "prep_time": "string (e.g., '15 minutes')",
        "total_time": "string (e.g., '45 minutes')"
    }}

    Please return ONLY the JSON object, no other text.
    """


def extract_json_from_markdown(text):
    """Extract JSON from markdown code blocks."""
    # Remove ```json and ``` markers
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]  # Remove ```json
    elif text.startswith("```"):
        text = text[3:]  # Remove ```

    if text.endswith("```"):
        text = text[:-3]  # Remove trailing ```

    return text.strip()


async def process_claude_response(prompt):
    """Process Claude's response and extract text content."""
    result_text = ""
    print("Claude processing response...")
    async for message in query(prompt=prompt, options=options):
        # Handle different content types
        if hasattr(message, "content") and message.content:
            if isinstance(message.content, str):
                result_text += message.content
            elif isinstance(message.content, list):
                # If content is a list, join the parts
                for part in message.content:
                    if isinstance(part, str):
                        result_text += part
                    elif hasattr(part, "text"):
                        result_text += str(part.text)
                    elif hasattr(part, "content"):
                        result_text += str(part.content)
        elif hasattr(message, "text") and message.text:
            result_text += str(message.text)

    return result_text.strip()


def cleanup_temp_file(temp_file_path):
    """Clean up the temporary file."""
    try:
        os.unlink(temp_file_path)
    except OSError:
        print(f"Warning: Could not delete temporary file: {temp_file_path}")


def format_to_google_doc(recipe_data):
    """
    Takes recipe data and formats it so it can be
    used to create a google doc
    """
    sections = []
    for ingredient in recipe_data.get("ingredients"):
        sections.append({"text": ingredient, "style": "bullet"})

    for step in recipe_data.get("steps"):
        sections.append(
            {
                "text": step,
                "style": "numbered",
            }
        )

    return {"sections": sections}


async def extract_recipe_from_url(recipe_url):
    """
    Extracts a recipe from a url:
    - ingredients
    - steps
    - recipe_name
    - cook time
    - prep time
    - total time
    """
    try:
        # Fetch HTML content
        html_content = await fetch_html_content(recipe_url)

        # Extract recipe-specific content
        recipe_content = extract_recipe_content(html_content)

        # Create prompt and query Claude
        prompt = create_extraction_prompt(recipe_content)
        result_text = await process_claude_response(prompt)

        # Parse the JSON response
        if not result_text:
            print("Error: Claude returned an empty response")
            return None

        # Debug: print the raw response
        print(f"Raw Claude response (first 200 chars): {result_text[:200]}")

        # Extract JSON from markdown code blocks if present
        cleaned_text = extract_json_from_markdown(result_text)

        recipe_data = json.loads(cleaned_text)
        recipe_name = recipe_data.get("recipe_name", "Unknown")
        print(f"Successfully extracted recipe: {recipe_name}")
        return recipe_data
    except json.JSONDecodeError as e:
        print(f"Error parsing Claude's response as JSON: {e}")
        print(f"Response content: {result_text[:500] if result_text else 'None'}")
        return None
    except Exception as e:
        print(f"Error extracting recipe: {e}")
        return None


async def run(recipe_url):
    print(f"Extracting recipe from: {recipe_url}")
    recipe_data = await extract_recipe_from_url(recipe_url)
    return recipe_data


async def main():
    if len(sys.argv) > 1:
        recipe_url = sys.argv[1]
    else:
        recipe_url = "https://www.thegunnysack.com/easy-pecan-pie-without-corn-syrup/"

    recipe_data = await run(recipe_url)
    if not recipe_data:
        return

    if recipe_data:
        print("\n=== EXTRACTED RECIPE ===")
        print(f"Name: {recipe_data.get('recipe_name', 'N/A')}")
        print(f"Prep Time: {recipe_data.get('prep_time', 'N/A')}")
        print(f"Cook Time: {recipe_data.get('cook_time', 'N/A')}")
        print(f"Total Time: {recipe_data.get('total_time', 'N/A')}")

        print("\nIngredients:")
        for ingredient in recipe_data.get("ingredients", []):
            print(f"  - {ingredient}")

        print("\nSteps:")
        for i, step in enumerate(recipe_data.get("steps", []), 1):
            print(f"  {i}. {step}")

        if recipe_data.get("notes"):
            print("\nNotes:")
            for note in recipe_data.get("notes", []):
                print(f"  - {note}")
    else:
        print("Failed to extract recipe data")

    file_metadata = {
        "name": recipe_data.get("recipe_name"),
        "parents": ["0B022n6oV2lhRc2pFY18yVnFLaDA"],
    }
    file_content = format_to_google_doc(recipe_data)
    with GoogleDocsManager() as google_docs:
        print("Exporting to Google Docs")
        google_docs.create(file_metadata, file_content)


if __name__ == "__main__":
    asyncio.run(main())
