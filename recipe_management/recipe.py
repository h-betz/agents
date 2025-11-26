import asyncio
import json
import httpx
import sys
from claude_agent_sdk import query, ClaudeAgentOptions


options = ClaudeAgentOptions(
    system_prompt="You are a helpful assistant tasked with helping me manage my recipes.",
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


def add_recipe(recipe):
    """
    Calls the Google Docs API and uploads a document with the
    recipe details in there
    """
    pass


async def fetch_html_content(recipe_url):
    """Fetch HTML content from the recipe URL."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(recipe_url, headers=headers)
        return response.text


def create_temp_file(html_content):
    """Save HTML content to a temporary file and return the file path."""
    import tempfile

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False
    ) as temp_file:
        temp_file.write(html_content)
        return temp_file.name


def create_extraction_prompt(temp_file_path):
    """Create the prompt for Claude to extract recipe information."""
    return f"""
    Please read the HTML file at {temp_file_path} and extract recipe information from it.
    
    If the file is too large, read it in chunks using offset and limit parameters to find the recipe content.
    Look for sections containing ingredients, instructions, prep time, cook time, etc.
    
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


async def process_claude_response(prompt):
    """Process Claude's response and extract text content."""
    result_text = ""
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
    import os

    try:
        os.unlink(temp_file_path)
    except OSError:
        print(f"Warning: Could not delete temporary file: {temp_file_path}")


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
    temp_file_path = None

    try:
        # Fetch HTML content
        html_content = await fetch_html_content(recipe_url)

        # Create temporary file
        temp_file_path = create_temp_file(html_content)

        # Create prompt and query Claude
        prompt = create_extraction_prompt(temp_file_path)
        result_text = await process_claude_response(prompt)

        # Parse the JSON response
        recipe_data = json.loads(result_text)
        print(
            f"Successfully extracted recipe: {recipe_data.get('recipe_name', 'Unknown')}"
        )
        return recipe_data

    except json.JSONDecodeError as e:
        print(f"Error parsing Claude's response as JSON: {e}")
        return None
    except Exception as e:
        print(f"Error extracting recipe: {e}")
        return None
    finally:
        # Clean up the temporary file
        if temp_file_path:
            cleanup_temp_file(temp_file_path)


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


if __name__ == "__main__":
    asyncio.run(main())
