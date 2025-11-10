"""
Recipe extraction from video transcripts using LLM.
Converts raw transcript text into structured recipe JSON.
"""
import json
import re
from typing import Dict, Optional
from nlp_prompts import get_extraction_prompt, get_json_fix_prompt
from llm import chat, extract_json_from_response, get_client


class RecipeExtractor:
    """Extracts structured recipes from video transcripts."""
    
    def __init__(self, model: str = "gemma3:1b", max_retries: int = 2):
        """
        Initialize recipe extractor.
        
        Args:
            model: LLM model to use
            max_retries: Maximum attempts to get valid JSON
        """
        self.model = self._get_available_model(model)
        self.max_retries = max_retries
    
    def _get_available_model(self, preferred_model: str) -> str:
        """
        Get available model, falling back if preferred is not available.
        
        Args:
            preferred_model: Preferred model name
            
        Returns:
            Available model name
        """
        client = get_client()
        available_models = client.list_models()
        
        if not available_models:
            print("⚠ No models available! Make sure Ollama is running and has models.")
            return preferred_model
        
        # Check exact match or prefix match (e.g., phi4 matches phi4:latest)
        for model in available_models:
            if model == preferred_model or model.startswith(f"{preferred_model}:"):
                print(f"✓ Using model: {model}")
                return model
        
        # Fallback logic
        fallback_order = ["gemma3:1b", "llama3.2:3b-instruct", "llama3.2:1b"]
        
        for fallback in fallback_order:
            for model in available_models:
                if model == fallback or model.startswith(f"{fallback}:"):
                    print(f"⚠ {preferred_model} not found, using fallback: {model}")
                    return model
        
        # Use first available model
        fallback_model = available_models[0]
        print(f"⚠ {preferred_model} not found, using first available: {fallback_model}")
        return fallback_model
    
    def extract(self, transcript: str) -> Optional[Dict]:
        """
        Extract recipe from transcript.
        
        Args:
            transcript: Raw transcript text
            
        Returns:
            Structured recipe dict or None if extraction fails
        """
        print("Extracting recipe from transcript...")
        print(f"Transcript length: {len(transcript)} characters")
        
        # Get extraction prompt
        messages = get_extraction_prompt(transcript)
        
        # Try extraction with retries
        for attempt in range(self.max_retries + 1):
            try:
                print(f"\nAttempt {attempt + 1}/{self.max_retries + 1}...")
                
                # Call LLM (reduced max_tokens for faster generation)
                from llm import get_client
                client = get_client()
                response = client.chat(messages, model=self.model, temperature=0.3, max_tokens=2000)
                
                # Clean response
                json_text = extract_json_from_response(response)
                
                # Parse JSON
                recipe = json.loads(json_text)
                
                # Validate structure
                if self._validate_recipe(recipe):
                    print("✓ Successfully extracted recipe!")
                    return recipe
                else:
                    print("⚠ Recipe validation failed, retrying...")
                    
            except json.JSONDecodeError as e:
                print(f"✗ JSON parsing error: {e}")
                
                if attempt < self.max_retries:
                    # Try to fix JSON
                    print("Attempting to repair JSON...")
                    response = self._fix_json(response)
                    
                    try:
                        json_text = extract_json_from_response(response)
                        recipe = json.loads(json_text)
                        
                        if self._validate_recipe(recipe):
                            print("✓ Successfully extracted recipe after repair!")
                            return recipe
                    except:
                        print("✗ Repair failed")
                        
            except Exception as e:
                print(f"✗ Extraction error: {e}")
        
        print("\n✗ Failed to extract recipe after all attempts")
        return None
    
    def _validate_recipe(self, recipe: Dict) -> bool:
        """
        Validate recipe structure.
        
        Args:
            recipe: Parsed recipe dict
            
        Returns:
            True if valid
        """
        required_keys = ["ingredients", "kitchen_tools_and_dishes", "steps"]
        
        # Check required keys exist
        for key in required_keys:
            if key not in recipe:
                print(f"Missing required key: {key}")
                return False
        
        # Validate ingredients
        if not isinstance(recipe["ingredients"], dict):
            print("ingredients must be a dict")
            return False
        
        # Validate tools
        if not isinstance(recipe["kitchen_tools_and_dishes"], list):
            print("kitchen_tools_and_dishes must be a list")
            return False
        
        # Validate steps
        steps = recipe["steps"]
        if not isinstance(steps, list) or len(steps) == 0:
            print("steps must be a non-empty list")
            return False
        
        # Check step structure
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                print(f"Step {i} is not a dict")
                return False
            
            if "step_number" not in step or "instruction" not in step:
                print(f"Step {i} missing required fields")
                return False
        
        return True
    
    def _fix_json(self, malformed_json: str) -> str:
        """
        Attempt to fix malformed JSON using LLM.
        
        Args:
            malformed_json: Broken JSON string
            
        Returns:
            Fixed JSON string
        """
        messages = get_json_fix_prompt(malformed_json)
        return chat(messages, model=self.model, temperature=0.1)


def extract_recipe(transcript: str, model: str = "gemma3:1b") -> Optional[Dict]:
    """
    Convenience function to extract recipe.
    
    Args:
        transcript: Video transcript text
        model: LLM model to use
        
    Returns:
        Structured recipe dict or None
    """
    extractor = RecipeExtractor(model=model)
    return extractor.extract(transcript)


def print_recipe_summary(recipe: Dict):
    """
    Pretty print recipe summary.
    
    Args:
        recipe: Structured recipe dict
    """
    print("\n" + "="*60)
    print(f"RECIPE: {recipe.get('title', 'Untitled')}")
    print("="*60)
    
    # Servings and time
    if "servings" in recipe:
        print(f"\nServings: {recipe['servings']}")
    if "total_time" in recipe:
        print(f"Total Time: {recipe['total_time']}")
    
    # Ingredients
    print(f"\n--- INGREDIENTS ---")
    ingredients = recipe["ingredients"]
    for category, items in ingredients.items():
        if items:
            print(f"\n{category.replace('_', ' ').title()}:")
            for item in items:
                print(f"  • {item}")
    
    # Tools
    print(f"\n--- TOOLS & EQUIPMENT ---")
    for tool in recipe["kitchen_tools_and_dishes"]:
        print(f"  • {tool}")
    
    # Steps
    print(f"\n--- STEPS ---")
    for step in recipe["steps"]:
        step_num = step["step_number"]
        instruction = step["instruction"]
        time_str = f" ({step['estimated_time']})" if "estimated_time" in step else ""
        print(f"\n{step_num}. {instruction}{time_str}")
    
    print("\n" + "="*60)


# CLI test
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python extractors.py <transcript_file>")
        print("Example: python extractors.py 'Easy Pasta Dough Recipe_transcript.txt'")
        sys.exit(1)
    
    # Read transcript
    transcript_file = sys.argv[1]
    try:
        with open(transcript_file, 'r', encoding='utf-8') as f:
            transcript = f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {transcript_file}")
        sys.exit(1)
    
    # Extract recipe
    recipe = extract_recipe(transcript)
    
    if recipe:
        print_recipe_summary(recipe)
        
        # Save JSON
        output_file = transcript_file.replace('_transcript.txt', '_recipe.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(recipe, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Saved recipe to: {output_file}")
    else:
        print("\n✗ Failed to extract recipe")
        sys.exit(1)