import { useState, useEffect } from "react";
import { HomePage } from "./components/HomePage";
import { RecipeDetail } from "./components/RecipeDetail";
import { BottomNavigation } from "./components/BottomNavigation";
import { Toaster } from "./components/ui/sonner";
import { listRecipes, saveRecipe } from "./src/services/api";
import { toast } from "sonner";

interface HomeRecipe {
  id: number;
  title: string;
  description: string;
  image: string;
  time: string;
  difficulty: string;
  tags: string[];
  video_url?: string;
  ingredients?: Record<string, string[]>;
  steps?: Array<{
    step_number: number;
    instruction: string;
    estimated_time?: string;
  }>;
  kitchen_tools_and_dishes?: string[];
  isSaved?: boolean;
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
  video_url?: string;
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
        let homeRecipes: HomeRecipe[] = [];

        if (savedRecipes.length > 0) {
          try {
            // Convert saved recipes to HomeRecipe format
            homeRecipes = savedRecipes.map(savedRecipe => ({
              id: savedRecipe.id,
              title: savedRecipe.title,
              description: savedRecipe.description || "",
              image: savedRecipe.recipe.image || "https://images.unsplash.com/photo-1711539137930-3fa2ae6cec60?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxkZWxpY2lvdXMlMjBwYXN0YSUyMGRpc2h8ZW58MXx8fHwxNzYyMDYzNDU5fDA&ixlib=rb-4.1.0&q=80&w=1080",
              time: savedRecipe.recipe.total_time || "N/A",
              difficulty: "Medium", // Default difficulty
              tags: [], // Removed "Saved Recipe" tag
              video_url: savedRecipe.recipe.video_url,
              ingredients: savedRecipe.recipe.ingredients,
              steps: savedRecipe.recipe.steps,
              kitchen_tools_and_dishes: savedRecipe.recipe.kitchen_tools_and_dishes,
              isSaved: true
            }));
          } catch (mapError) {
            console.error("Error mapping recipes:", mapError);
            toast.error("Error processing saved recipes");
          }
        }

        setRecipes(homeRecipes);
        setFeaturedRecipes(homeRecipes.slice(0, 3));
        setLoading(false);
      } catch (error: any) {
        console.error("Failed to fetch recipes:", error);
        toast.error("Failed to load recipes: " + (error.message || "Unknown error"));
        setRecipes([]);
        setFeaturedRecipes([]);
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
    if (tab === "home" || tab === "search" || tab === "saved") {
      setCurrentScreen("home");
      setSelectedRecipe(null);
    }
  };

  const handleToggleSave = async (recipe: any) => {
    if (recipe.isSaved) {
      // Unsave: Just update local state to isSaved: false
      // Note: This doesn't delete from DB, so it will reappear on reload.
      // To properly delete, we'd need a delete endpoint.
      setRecipes(prev => prev.map(r =>
        r.id === recipe.id ? { ...r, isSaved: false } : r
      ));
      toast.success("Recipe removed from saved");
    } else {
      // Save: Call API and update list
      try {
        await saveRecipe(recipe.title, recipe.description || "", {
          ...recipe,
          ingredients: recipe.ingredients || {},
          steps: recipe.steps || [],
          kitchen_tools_and_dishes: recipe.kitchen_tools_and_dishes || []
        });

        setRecipes(prev => prev.map(r =>
          r.id === recipe.id ? { ...r, isSaved: true } : r
        ));
        toast.success("Recipe saved!");
      } catch (error) {
        toast.error("Failed to save recipe");
        console.error(error);
      }
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
          activeTab={activeTab}
          onToggleSave={handleToggleSave}
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