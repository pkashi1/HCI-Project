import { Menu, Search } from "lucide-react";
import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "./ui/dialog";
import { Input } from "./ui/input";
import { toast } from "sonner";
import { ingestVideo, extractRecipe, saveRecipe } from "../src/services/api";
import { Button } from "./ui/button";
import { RecipeCard } from "./RecipeCard";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from "./ui/carousel";

interface Recipe {
  id: number;
  title: string;
  description: string;
  image: string;
  time: string;
  difficulty: string;
  tags: string[];
}

interface HomePageProps {
  onRecipeClick: (recipe: Recipe) => void;
  recipes: Recipe[];
  featuredRecipes: Recipe[];
}

export function HomePage({
  onRecipeClick,
  recipes,
  featuredRecipes,
}: HomePageProps) {

  const [showLookup, setShowLookup] = useState(false);
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Recently watched (extracted) recipes
  const [recentlyWatched, setRecentlyWatched] = useState<any[]>([]);

  // Add extracted recipe to feed and recently watched
  const [extractedRecipe, setExtractedRecipe] = useState<any>(null);

  // Hardcoded YouTube URL for demo (commented for future dynamic input)
  // const HARDCODED_URL = "https://www.youtube.com/watch?v=-fMcKbeqX4g&pp=ygUZRmx1ZmZ5IEJsdWViZXJyeSBQYW5jYWtlcw%3D%3D";
  const handleExtractRecipe = async () => {
    setIsLoading(true);
    try {
      // Use hardcoded URL for now (commented for future dynamic input)
      // const url = HARDCODED_URL;
      const url = youtubeUrl;
      if (!url) {
        toast.error("Please enter a YouTube URL");
        setIsLoading(false);
        return;
      }
      // 1. Ingest video to get transcript
      const ingestRes = await ingestVideo({ youtube_url: url });
      // 2. Extract recipe from transcript
      const extractRes = await extractRecipe({ transcript: ingestRes.transcript });
      // 3. Add to feed (top)
      const newRecipe = {
        id: Date.now(),
        title: ingestRes.title,
        description: "Extracted from YouTube video.",
        image: `https://img.youtube.com/vi/${ingestRes.video_id}/hqdefault.jpg`,
        time: extractRes.recipe.total_time || "N/A",
        difficulty: "AI-generated",
        tags: ["YouTube", "Extracted"],
        youtubeUrl: url, // Save the YouTube URL with the recipe
        ...extractRes.recipe,
      };
      // Save to backend database
      try {
        await saveRecipe(newRecipe.title, newRecipe.description, {
          ...extractRes.recipe,
          youtubeUrl: url,
        });
      } catch (e) {
        toast.error("Failed to save recipe to database");
      }
      setExtractedRecipe(newRecipe);
      setRecentlyWatched((prev) => [newRecipe, ...prev.filter(r => r.youtubeUrl !== url)].slice(0, 5));
      toast.success("Recipe extracted!");
      setShowLookup(false);
      setYoutubeUrl("");
    } catch (err: any) {
      toast.error("Failed to extract recipe");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-30">
        <div className="max-w-md mx-auto px-4 py-4 flex items-center justify-between">
          <button className="p-2 -ml-2 hover:bg-gray-100 rounded-lg transition-colors">
            <Menu className="w-6 h-6 text-gray-700" />
          </button>
          <h1 className="text-orange-600">FlavorVoice</h1>
          <Button
            variant="ghost"
            size="icon"
            className="p-2 -mr-2 hover:bg-gray-100 rounded-lg transition-colors"
            onClick={() => setShowLookup(true)}
            aria-label="Lookup YouTube Recipe"
          >
            <Search className="w-6 h-6 text-gray-700" />
          </Button>
        </div>
      </header>

      {/* Lookup Dialog for YouTube Recipe Extraction */}
      <Dialog open={showLookup} onOpenChange={setShowLookup}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Extract Recipe from YouTube</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <Input
              placeholder="Paste YouTube URL here..."
              value={youtubeUrl}
              onChange={e => setYoutubeUrl(e.target.value)}
              // defaultValue={HARDCODED_URL} // Uncomment for demo
            />
            <Button
              onClick={handleExtractRecipe}
              disabled={isLoading}
              className="w-full"
            >
              {isLoading ? "Extracting..." : "Extract Recipe"}
            </Button>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setShowLookup(false)}>
              Cancel
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <div className="max-w-md mx-auto">
        {/* Recently Watched Section */}
        {recentlyWatched.length > 0 && (
          <section className="px-4 pt-6">
            <h2 className="mb-3 text-lg font-semibold">Recently Watched</h2>
            <div className="space-y-3">
              {recentlyWatched.map((recipe) => (
                <RecipeCard
                  key={recipe.id}
                  {...recipe}
                  onClick={() => onRecipeClick(recipe)}
                />
              ))}
            </div>
          </section>
        )}

        {/* Hero Section */}
        <section className="relative">
          <Carousel className="w-full">
            <CarouselContent>
              {featuredRecipes.map((recipe) => (
                <CarouselItem key={recipe.id}>
                  <div
                    className="relative h-64 cursor-pointer"
                    onClick={() => onRecipeClick(recipe)}
                  >
                    <ImageWithFallback
                      src={recipe.image}
                      alt={recipe.title}
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/30 to-transparent" />
                    <div className="absolute bottom-0 left-0 right-0 p-6 text-white">
                      <h2 className="mb-2 text-white">
                        Cook Smarter with Voice-Guided Recipes
                      </h2>
                      <p className="text-sm text-white/90">
                        Hands-free cooking made simple
                      </p>
                    </div>
                  </div>
                </CarouselItem>
              ))}
            </CarouselContent>
            <CarouselPrevious className="left-2" />
            <CarouselNext className="right-2" />
          </Carousel>
        </section>

        {/* Recipe Feed */}
        <section className="px-4 py-6">
          <h2 className="mb-4">Popular Recipes</h2>
          <div className="space-y-4">
            {/* Show extracted recipe card at the top if available */}
            {extractedRecipe && (
              <RecipeCard
                key={extractedRecipe.id}
                {...extractedRecipe}
                onClick={() => onRecipeClick(extractedRecipe)}
              />
            )}
            {recipes.map((recipe) => (
              <RecipeCard
                key={recipe.id}
                {...recipe}
                onClick={() => onRecipeClick(recipe)}
              />
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
