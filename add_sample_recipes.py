#!/usr/bin/env python3
"""
Script to add sample recipes to the database for demonstration purposes.
"""

import sys
import os
import requests
import json

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

BASE_URL = "http://localhost:8000"

def add_sample_recipe(title, description, recipe_data):
    """Add a sample recipe to the database."""
    print(f"Adding recipe: {title}")
    try:
        response = requests.post(
            f"{BASE_URL}/recipes",
            json={
                "title": title,
                "description": description,
                "recipe": recipe_data
            }
        )
        
        if response.status_code == 200:
            saved_recipe = response.json()
            print(f"✓ Recipe saved with ID: {saved_recipe['id']}")
            return saved_recipe
        else:
            print(f"✗ Failed to save recipe: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Error saving recipe: {e}")
        return None

def main():
    """Main function to add sample recipes."""
    print("=" * 60)
    print("ADDING SAMPLE RECIPES TO DATABASE")
    print("=" * 60)
    
    # Check if API is running
    try:
        response = requests.get(BASE_URL)
        if response.status_code != 200:
            print("✗ API is not running. Please start the backend server:")
            print("  cd backend && uvicorn app:app --reload --port 8000")
            return
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to API. Please start the backend server:")
        print("  cd backend && uvicorn app:app --reload --port 8000")
        return
    
    # Sample recipes data
    sample_recipes = [
        {
            "title": "Fluffy Blueberry Pancakes",
            "description": "Delicious fluffy pancakes with fresh blueberries",
            "recipe": {
                "title": "Fluffy Blueberry Pancakes",
                "servings": "4 servings",
                "total_time": "20 minutes",
                "ingredients": {
                    "dry_ingredients": [
                        "2 cups all-purpose flour",
                        "2 tablespoons sugar",
                        "2 teaspoons baking powder",
                        "1 teaspoon salt"
                    ],
                    "wet_ingredients": [
                        "2 eggs",
                        "1 3/4 cups milk",
                        "1/4 cup melted butter",
                        "1 teaspoon vanilla extract"
                    ],
                    "add_ins": [
                        "1 cup fresh blueberries"
                    ]
                },
                "kitchen_tools_and_dishes": [
                    "Mixing bowls",
                    "Whisk",
                    "Measuring cups",
                    "Non-stick pan or griddle",
                    "Spatula"
                ],
                "steps": [
                    {
                        "step_number": 1,
                        "instruction": "In a large bowl, whisk together flour, sugar, baking powder, and salt."
                    },
                    {
                        "step_number": 2,
                        "instruction": "In another bowl, beat eggs, then add milk, melted butter, and vanilla extract."
                    },
                    {
                        "step_number": 3,
                        "instruction": "Pour wet ingredients into dry ingredients and stir until just combined. Do not overmix."
                    },
                    {
                        "step_number": 4,
                        "instruction": "Gently fold in blueberries."
                    },
                    {
                        "step_number": 5,
                        "instruction": "Heat griddle or pan over medium heat and lightly grease with butter."
                    },
                    {
                        "step_number": 6,
                        "instruction": "Pour 1/4 cup batter for each pancake onto the griddle."
                    },
                    {
                        "step_number": 7,
                        "instruction": "Cook until bubbles form on surface, then flip and cook until golden brown."
                    },
                    {
                        "step_number": 8,
                        "instruction": "Serve warm with maple syrup and extra blueberries."
                    }
                ]
            }
        },
        {
            "title": "Gordon's Quick Pasta",
            "description": "Simple and quick pasta recipe inspired by Gordon Ramsay",
            "recipe": {
                "title": "Gordon's Quick Pasta",
                "servings": "2 servings",
                "total_time": "15 minutes",
                "ingredients": {
                    "pasta": [
                        "200g spaghetti or linguine"
                    ],
                    "sauce": [
                        "3 cloves garlic, minced",
                        "1/4 cup olive oil",
                        "1/4 teaspoon red pepper flakes",
                        "1/4 cup fresh parsley, chopped",
                        "Salt and black pepper to taste",
                        "Parmesan cheese for serving"
                    ]
                },
                "kitchen_tools_and_dishes": [
                    "Large pot",
                    "Colander",
                    "Large skillet or pan",
                    "Wooden spoon",
                    "Grater for Parmesan"
                ],
                "steps": [
                    {
                        "step_number": 1,
                        "instruction": "Bring a large pot of salted water to boil and cook pasta according to package directions."
                    },
                    {
                        "step_number": 2,
                        "instruction": "While pasta cooks, heat olive oil in a large skillet over medium heat."
                    },
                    {
                        "step_number": 3,
                        "instruction": "Add minced garlic and red pepper flakes, sauté for about 1 minute until fragrant."
                    },
                    {
                        "step_number": 4,
                        "instruction": "Reserve 1/2 cup pasta water before draining pasta."
                    },
                    {
                        "step_number": 5,
                        "instruction": "Add drained pasta to the skillet with garlic oil."
                    },
                    {
                        "step_number": 6,
                        "instruction": "Add a splash of reserved pasta water and toss to combine."
                    },
                    {
                        "step_number": 7,
                        "instruction": "Season with salt and black pepper to taste."
                    },
                    {
                        "step_number": 8,
                        "instruction": "Stir in fresh parsley and serve immediately with grated Parmesan cheese."
                    }
                ]
            }
        }
    ]
    
    saved_recipes = []
    
    for i, recipe_data in enumerate(sample_recipes, 1):
        print(f"\n[{i}/{len(sample_recipes)}] Adding: {recipe_data['title']}")
        
        saved_recipe = add_sample_recipe(
            recipe_data["title"],
            recipe_data["description"],
            recipe_data["recipe"]
        )
        
        if saved_recipe:
            saved_recipes.append(saved_recipe)
    
    print("\n" + "=" * 60)
    if saved_recipes:
        print(f"✓ Successfully saved {len(saved_recipes)} recipes to database")
        print("\nSaved recipes:")
        for recipe in saved_recipes:
            print(f"  - {recipe['title']} (ID: {recipe['id']})")
    else:
        print("✗ No recipes were saved")
    print("=" * 60)

if __name__ == "__main__":
    main()