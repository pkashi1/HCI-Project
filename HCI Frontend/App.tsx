import { useState, useEffect } from "react";
import { HomePage } from "./components/HomePage";
import { RecipeDetail } from "./components/RecipeDetail";
import { BottomNavigation } from "./components/BottomNavigation";
import { Toaster } from "./components/ui/sonner";
import { listRecipes } from "./src/services/api";

interface HomeRecipe {
  id: number;
  title: string;
  description: string;
  image: string;
  time: string;
  difficulty: string;
  tags: string[];
}

interface Recipe {
  id?: number;
  title: string;
  description?: string;
  image?: string;
  time?: string;
  difficulty?: string;
  tags?: string[];
  ingredients: Record<string, string[]>;
  kitchen_tools_and_dishes: string[];
  steps: Array<{
    step_number: number;
    instruction: string;
    estimated_time?: string;
  }>;
  servings?: string;
  total_time?: string;
  [key: string]: any;
}

export default function App() {
  const [currentScreen, setCurrentScreen] = useState<"home" | "detail">("home");
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const [activeTab, setActiveTab] = useState("home");
  const [recipes, setRecipes] = useState<HomeRecipe[]>([]);
  const [featuredRecipes, setFeaturedRecipes] = useState<HomeRecipe[]>([]);
  const [loading, setLoading] = useState(true);

  // Fetch recipes from backend
  useEffect(() => {
    const fetchRecipes = async () => {
      try {
        const savedRecipes = await listRecipes();
        
        // Convert saved recipes to HomeRecipe format
        const homeRecipes: HomeRecipe[] = savedRecipes.map(savedRecipe => ({
          id: savedRecipe.id,
          title: savedRecipe.title,
          description: savedRecipe.description || "",
          image: "https://images.unsplash.com/photo-1711539137930-3fa2ae6cec60?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxkZWxpY2lvdXMlMjBwYXN0YSUyMGRpc2h8ZW58MXx8fHwxNzYyMDYzNDU5fDA&ixlib=rb-4.1.0&q=80&w=1080", // Default image
          time: savedRecipe.recipe.total_time || "N/A",
          difficulty: "Medium", // Default difficulty
          tags: ["Saved Recipe"] // Default tags
        }));
        
        setRecipes(homeRecipes);
        setFeaturedRecipes(homeRecipes.slice(0, 3)); // First 3 as featured
        setLoading(false);
      } catch (error) {
        console.error("Failed to fetch recipes:", error);
        // Fallback to hardcoded recipes if backend fails
        /*
        const fallbackRecipes: HomeRecipe[] = [
          {
            id: 1,
            title: "Creamy Garlic Pasta",
            description: "A quick and delicious weeknight dinner with rich flavors",
            image:
              "https://images.unsplash.com/photo-1711539137930-3fa2ae6cec60?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxkZWxpY2lvdXMlMjBwYXN0YSUyMGRpc2h8ZW58MXx8fHwxNzYyMDYzNDU5fDA&ixlib=rb-4.1.0&q=80&w=1080",
            time: "25 min",
            difficulty: "Easy",
            tags: ["Vegetarian", "Italian", "Quick"],
          },
          {
            id: 2,
            title: "Fresh Garden Salad Bowl",
            description: "Crisp vegetables with a tangy vinaigrette dressing",
            image:
              "https://images.unsplash.com/photo-1620019989479-d52fcedd99fe?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxmcmVzaCUyMHNhbGFkJTIwYm93bHxlbnwxfHx8fDE3NjIwNjM4NzZ8MA&ixlib=rb-4.1.0&q=80&w=1080",
            time: "15 min",
            difficulty: "Easy",
            tags: ["Healthy", "Vegan", "Gluten-Free"],
          },
          {
            id: 3,
            title: "Herb Grilled Chicken",
            description: "Juicy chicken breast marinated in aromatic herbs",
            image:
              "https://images.unsplash.com/photo-1682423187670-4817da9a1b23?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxncmlsbGVkJTIwY2hpY2tlbiUyMG1lYWx8ZW58MXx8fHwxNzYyMDg5MDY3fDA&ixlib=rb-4.1.0&q=80&w=1080",
            time: "35 min",
            difficulty: "Medium",
            tags: ["High-Protein", "Paleo", "Gluten-Free"],
          },
          {
            id: 4,
            title: "Decadent Chocolate Cake",
            description: "Rich, moist chocolate cake with ganache frosting",
            image:
              "https://images.unsplash.com/photo-1736840334919-aac2d5af73e4?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxjaG9jb2xhdGUlMjBkZXNzZXJ0JTIwY2FrZXxlbnwxfHx8fDE3NjIxMjg3NDB8MA&ixlib=rb-4.1.0&q=80&w=1080",
            time: "60 min",
            difficulty: "Hard",
            tags: ["Dessert", "Vegetarian", "Special"],
          },
          {
            id: 5,
            title: "Fluffy Blueberry Pancakes",
            description: "Perfect breakfast stack with fresh berries",
            image:
              "https://images.unsplash.com/photo-1636743713732-125909a35dcc?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxicmVha2Zhc3QlMjBwYW5jYWtlc3xlbnwxfHx8fDE3NjIxMDMxMzV8MA&ixlib=rb-4.1.0&q=80&w=1080",
            time: "20 min",
            difficulty: "Easy",
            tags: ["Breakfast", "Vegetarian", "Kid-Friendly"],
          },
        ];
        */
        
        // setRecipes(fallbackRecipes);
        // setFeaturedRecipes(fallbackRecipes.slice(0, 3));
        setLoading(false);
      }
    };

    fetchRecipes();
  }, []);

  const handleRecipeClick = (recipe: any) => {
    // If the recipe already has ingredients/steps, use them directly
    const fullRecipe: Recipe = {
      id: recipe.id,
      title: recipe.title,
      description: recipe.description,
      image: recipe.image,
      time: recipe.time,
      difficulty: recipe.difficulty,
      tags: recipe.tags,
      ingredients: recipe.ingredients || {},
      kitchen_tools_and_dishes: recipe.kitchen_tools_and_dishes || [],
      steps: recipe.steps || [],
      servings: recipe.servings,
      total_time: recipe.total_time,
      // Spread any other fields
      ...recipe
    };
    setSelectedRecipe(fullRecipe);
    setCurrentScreen("detail");
  };

  const handleBack = () => {
    setCurrentScreen("home");
    setSelectedRecipe(null);
  };

  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    if (tab === "home") {
      setCurrentScreen("home");
      setSelectedRecipe(null);
    }
  };

  if (loading) {
    return (
      <div className="max-w-md mx-auto bg-white min-h-screen flex items-center justify-center">
        <p>Loading recipes...</p>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto bg-white min-h-screen">
      {currentScreen === "home" ? (
        <HomePage
          recipes={recipes}
          featuredRecipes={featuredRecipes}
          onRecipeClick={handleRecipeClick}
        />
      ) : (
        selectedRecipe && (
          <RecipeDetail recipe={selectedRecipe} onBack={handleBack} />
        )
      )}

      <BottomNavigation activeTab={activeTab} onTabChange={handleTabChange} />
      <Toaster />
    </div>
  );
}