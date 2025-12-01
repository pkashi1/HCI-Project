import { ArrowLeft, Bookmark, Link as LinkIcon, Play, Pause, RotateCcw, Timer, ChefHat, Clock, Camera, X } from "lucide-react";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Checkbox } from "./ui/checkbox";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "./ui/dialog";
import { VoiceCommandButton } from "./VoiceCommandButton";
import { useState, useEffect, useRef } from "react";
import { toast } from "sonner";
import {
  Recipe,
  ingestVideo,
  extractRecipe,
  startSession,
  querySession,
  navigateStep,
  addTimer,
  getSessionState
} from "../src/services/api";

interface RecipeDetailProps {
  recipe: Recipe;
  onBack: () => void;
}

export function RecipeDetail({ recipe, onBack }: RecipeDetailProps) {
  const [isSaved, setIsSaved] = useState(false);
  const [youtubeUrl, setYoutubeUrl] = useState(recipe.video_url || "");
  const [checkedIngredients, setCheckedIngredients] = useState<Set<number>>(
    new Set()
  );

  // Session state
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(1);
  const [totalSteps, setTotalSteps] = useState(0);
  const [isSessionActive, setIsSessionActive] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [activeTimers, setActiveTimers] = useState<Array<{
    id: string;
    label: string;
    seconds_total: number;
    seconds_remaining: number;
    status: string;
    started_at: number;
  }>>([]);

  // Timer state
  const [timerLabel, setTimerLabel] = useState("");
  const [timerDuration, setTimerDuration] = useState("");

  // Camera state
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const handleSave = () => {
    setIsSaved(!isSaved);
    if (!isSaved) {
      toast.success("Recipe Saved", {
        description: "Added to your saved recipes",
      });
    }
  };

  const handlePasteUrl = async () => {
    try {
      const text = await navigator.clipboard.readText();
      setYoutubeUrl(text);
      toast.success("URL Pasted");
    } catch (err) {
      toast.error("Failed to paste from clipboard");
    }
  };

  const toggleIngredient = (index: number) => {
    const newChecked = new Set(checkedIngredients);
    if (newChecked.has(index)) {
      newChecked.delete(index);
    } else {
      newChecked.add(index);
    }
    setCheckedIngredients(newChecked);
  };

  const ingredients = recipe.ingredients || {};

  const getYoutubeEmbedUrl = (url: string) => {
    const videoIdMatch = url.match(
      /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\s]+)/
    );
    return videoIdMatch
      ? `https://www.youtube.com/embed/${videoIdMatch[1]}`
      : undefined;
  };

  const embedUrl = youtubeUrl ? getYoutubeEmbedUrl(youtubeUrl) : null;

  // Start cooking session
  const startCookingSession = async () => {
    try {
      const response = await startSession({ recipe });
      setSessionId(response.session_id);
      setTotalSteps(response.total_steps);
      setCurrentStep(1);
      setIsSessionActive(true);
      toast.success("Cooking session started!");
    } catch (error) {
      toast.error("Failed to start cooking session");
      console.error("Session start error:", error);
    }
  };

  // Handle voice command
  const handleVoiceCommand = async (command: string) => {
    if (!sessionId) return;

    try {
      const response = await querySession({
        session_id: sessionId,
        query: command
      });

      // Update state based on response
      setCurrentStep(response.current_step);
      setTotalSteps(response.total_steps);
      setIsPaused(response.is_paused);
      setActiveTimers(response.active_timers);

      // Show assistant response
      toast.info(response.response);
    } catch (error) {
      toast.error("Failed to process voice command");
      console.error("Voice command error:", error);
    }
  };

  // Navigate steps
  const navigateToStep = async (action: string) => {
    if (!sessionId) return;

    try {
      const response = await navigateStep({
        session_id: sessionId,
        action
      });

      // Update state
      setCurrentStep(response.current_step);
      setTotalSteps(response.total_steps);

      // Show step instruction
      if (response.step_data?.instruction) {
        toast.info(response.step_data.instruction);
      }
    } catch (error) {
      toast.error("Failed to navigate step");
      console.error("Step navigation error:", error);
    }
  };

  // Add timer
  const handleAddTimer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sessionId || !timerLabel || !timerDuration) return;

    try {
      const response = await addTimer({
        session_id: sessionId,
        label: timerLabel,
        duration: timerDuration
      });

      // Reset form
      setTimerLabel("");
      setTimerDuration("");

      toast.success(`Timer set for ${timerLabel}`);

      // Refresh active timers
      if (sessionId) {
        const state = await getSessionState(sessionId);
        setActiveTimers(state.active_timers);
      }
    } catch (error) {
      toast.error("Failed to set timer");
      console.error("Timer error:", error);
    }
  };

  // Toggle pause
  const togglePause = async () => {
    if (!sessionId) return;

    try {
      const command = isPaused ? "resume" : "pause";
      const response = await querySession({
        session_id: sessionId,
        query: command
      });

      setIsPaused(response.is_paused);
      toast.info(response.is_paused ? "Session paused" : "Session resumed");
    } catch (error) {
      toast.error("Failed to toggle pause");
      console.error("Pause error:", error);
    }
  };

  // Analyze image content
  const analyzeImage = async (base64Content: string) => {
    if (!sessionId) return;

    try {
      toast.info("Analyzing image...");
      const response = await querySession({
        session_id: sessionId,
        query: "Does this look correct?",
        image: base64Content
      });

      // Update state
      setCurrentStep(response.current_step);
      setTotalSteps(response.total_steps);
      setIsPaused(response.is_paused);
      setActiveTimers(response.active_timers);

      // Show assistant response
      toast.info(response.response, {
        duration: 5000, // Show for longer
      });
    } catch (error) {
      toast.error("Failed to analyze image");
      console.error("Image analysis error:", error);
    }
  };

  // Handle file upload
  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Reset input value to allow selecting same file again
    e.target.value = '';

    const reader = new FileReader();
    reader.onloadend = async () => {
      const base64String = reader.result as string;
      const base64Content = base64String.split(',')[1];
      await analyzeImage(base64Content);
    };
    reader.readAsDataURL(file);
  };

  // Camera handling
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setIsCameraOpen(true);
    } catch (err) {
      console.error("Error accessing camera:", err);
      toast.error("Could not access camera. Please check permissions.");
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setIsCameraOpen(false);
  };

  const capturePhoto = () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const context = canvas.getContext('2d');

      if (context) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        const dataUrl = canvas.toDataURL('image/jpeg');
        const base64Content = dataUrl.split(',')[1];

        stopCamera();
        analyzeImage(base64Content);
      }
    }
  };

  // Format seconds to MM:SS
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Effect to periodically update timers
  useEffect(() => {
    if (!sessionId || activeTimers.length === 0) return;

    const interval = setInterval(async () => {
      try {
        const state = await getSessionState(sessionId);
        setActiveTimers(state.active_timers);
      } catch (error) {
        console.error("Failed to update timers:", error);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [sessionId, activeTimers.length]);

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header Image */}
      <div className="relative">
        <ImageWithFallback
          src={recipe.image || "https://images.unsplash.com/photo-1711539137930-3fa2ae6cec60?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxkZWxpY2lvdXMlMjBwYXN0YSUyMGRpc2h8ZW58MXx8fHwxNzYyMDYzNDU5fDA&ixlib=rb-4.1.0&q=80&w=1080"}
          alt={recipe.title}
          className="w-full h-72 object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />

        {/* Top Navigation */}
        <div className="absolute top-0 left-0 right-0 flex items-center justify-between p-4">
          <button
            onClick={onBack}
            className="w-10 h-10 rounded-full bg-white/90 backdrop-blur-sm flex items-center justify-center hover:bg-white transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-700" />
          </button>
          <button
            onClick={handleSave}
            className="w-10 h-10 rounded-full bg-white/90 backdrop-blur-sm flex items-center justify-center hover:bg-white transition-colors"
          >
            <Bookmark
              className={`w-5 h-5 ${isSaved ? "fill-orange-600 text-orange-600" : "text-gray-700"
                }`}
            />
          </button>
        </div>
      </div>

      <div className="max-w-md mx-auto">
        {/* Recipe Title */}
        <div className="bg-white px-6 py-5 border-b border-gray-200">
          <h1 className="mb-2">{recipe.title}</h1>
          <p className="text-gray-600 mb-4">{recipe.description}</p>
          <div className="flex flex-wrap gap-2">
            {recipe.tags?.map((tag: string, index: number) => (
              <Badge
                key={index}
                variant="secondary"
                className="bg-orange-50 text-orange-700"
              >
                {tag}
              </Badge>
            ))}
          </div>
        </div>

        {/* YouTube URL Input */}
        <div className="bg-white px-6 py-4 border-b border-gray-200">
          <Label htmlFor="youtube-url" className="mb-2 block">
            Add Video Tutorial
          </Label>
          <div className="flex gap-2">
            <Input
              id="youtube-url"
              type="text"
              placeholder="Paste YouTube URL here..."
              value={youtubeUrl}
              onChange={(e) => setYoutubeUrl(e.target.value)}
              className="flex-1"
            />
            <Button
              variant="outline"
              size="icon"
              onClick={handlePasteUrl}
              className="shrink-0"
            >
              <LinkIcon className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Session Controls */}
        {isSessionActive ? (
          <>
            <div className="bg-white px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between mb-3">
                <span className="font-medium">Cooking Session</span>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={togglePause}
                    className="flex items-center gap-1"
                  >
                    {isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
                    {isPaused ? "Resume" : "Pause"}
                  </Button>

                  <Button
                    size="sm"
                    variant="outline"
                    onClick={startCamera}
                    className="flex items-center gap-1"
                  >
                    <Camera className="w-4 h-4" />
                    Verify
                  </Button>

                  {/* Hidden file input for fallback/gallery upload */}
                  <input
                    type="file"
                    id="image-upload"
                    accept="image/*"
                    className="hidden"
                    onChange={handleImageUpload}
                  />

                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => navigateToStep("repeat")}
                    className="flex items-center gap-1"
                  >
                    <RotateCcw className="w-4 h-4" />
                    Repeat
                  </Button>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">
                  Step {currentStep} of {totalSteps}
                </span>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={currentStep <= 1}
                    onClick={() => navigateToStep("previous")}
                  >
                    Previous
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={currentStep >= totalSteps}
                    onClick={() => navigateToStep("next")}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </div>

            {/* Camera Dialog */}
            <Dialog open={isCameraOpen} onOpenChange={(open) => !open && stopCamera()}>
              <DialogContent className="sm:max-w-md">
                <DialogHeader>
                  <DialogTitle>Verify Step</DialogTitle>
                </DialogHeader>
                <div className="relative aspect-video bg-black rounded-lg overflow-hidden">
                  <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    className="w-full h-full object-cover"
                  />
                  <canvas ref={canvasRef} className="hidden" />
                </div>
                <div className="flex justify-center gap-4 py-4">
                  <Button variant="outline" onClick={() => document.getElementById('image-upload')?.click()}>
                    Upload from Gallery
                  </Button>
                  <Button onClick={capturePhoto}>
                    <Camera className="w-4 h-4 mr-2" />
                    Capture
                  </Button>
                </div>
              </DialogContent>
            </Dialog>

            {/* Active Timers */}
            {activeTimers.length > 0 && (
              <div className="bg-white px-6 py-4 border-b border-gray-200">
                <h3 className="font-medium mb-2 flex items-center gap-2">
                  <Clock className="w-4 h-4" />
                  Active Timers
                </h3>
                <div className="space-y-2">
                  {activeTimers.map((timer) => (
                    <div key={timer.id} className="flex items-center justify-between bg-orange-50 p-2 rounded">
                      <div className="flex items-center gap-2">
                        <span className="text-sm">{timer.label}</span>
                        <span className="font-mono text-orange-700">{formatTime(timer.seconds_remaining)}</span>
                      </div>
                      <div className="flex gap-1">
                        {/* Pause/Resume Button */}
                        <Button size="icon" variant="ghost" onClick={() => {/* TODO: Implement pause/resume timer */ }} title={timer.status === 'paused' ? 'Resume' : 'Pause'}>
                          {timer.status === 'paused' ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
                        </Button>
                        {/* Edit Button */}
                        <Button size="icon" variant="ghost" onClick={() => {/* TODO: Implement edit timer */ }} title="Edit">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M15.232 5.232l3.536 3.536M9 13l6.586-6.586a2 2 0 112.828 2.828L11.828 15.828a4 4 0 01-1.414.828l-4 1a1 1 0 01-1.263-1.263l1-4a4 4 0 01.828-1.414z" /></svg>
                        </Button>
                        {/* Delete Button */}
                        <Button size="icon" variant="ghost" onClick={() => {/* TODO: Implement delete timer */ }} title="Delete">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Add Timer Form */}
            <div className="bg-white px-6 py-4 border-b border-gray-200">
              <h3 className="font-medium mb-2 flex items-center gap-2">
                <Timer className="w-4 h-4" />
                Add Timer
              </h3>
              <form onSubmit={handleAddTimer} className="flex gap-2">
                <Input
                  type="text"
                  placeholder="Timer label"
                  value={timerLabel}
                  onChange={(e) => setTimerLabel(e.target.value)}
                  className="flex-1"
                />
                <Input
                  type="text"
                  placeholder="e.g., 5 minutes"
                  value={timerDuration}
                  onChange={(e) => setTimerDuration(e.target.value)}
                  className="flex-1"
                />
                <Button type="submit" size="sm">
                  Set
                </Button>
              </form>
            </div>
          </>
        ) : (
          <div className="bg-white px-6 py-4 border-b border-gray-200">
            <Button onClick={startCookingSession} className="w-full flex items-center gap-2">
              <ChefHat className="w-4 h-4" />
              Start Cooking Session
            </Button>
          </div>
        )}

        {/* Tabs */}
        <Tabs defaultValue="ingredients" className="bg-white">
          <TabsList className="w-full grid grid-cols-3 h-12 bg-gray-100">
            <TabsTrigger value="ingredients">Ingredients</TabsTrigger>
            <TabsTrigger value="instructions">Instructions</TabsTrigger>
            <TabsTrigger value="video">Video</TabsTrigger>
          </TabsList>

          <TabsContent value="ingredients" className="px-6 py-5">
            <div className="space-y-4">
              {Object.entries(recipe.ingredients || {}).map(([category, items], categoryIndex) => (
                <div key={categoryIndex}>
                  <h3 className="font-medium mb-2 capitalize">{category.replace(/_/g, ' ')}</h3>
                  {items.map((ingredient, index) => (
                    <div key={`${categoryIndex}-${index}`} className="flex items-start gap-3 mb-2">
                      <Checkbox
                        id={`ingredient-${categoryIndex}-${index}`}
                        checked={checkedIngredients.has(categoryIndex * 100 + index)}
                        onCheckedChange={() => toggleIngredient(categoryIndex * 100 + index)}
                        className="mt-1"
                      />
                      <label
                        htmlFor={`ingredient-${categoryIndex}-${index}`}
                        className={`flex-1 cursor-pointer ${checkedIngredients.has(categoryIndex * 100 + index)
                          ? "line-through text-gray-400"
                          : "text-gray-700"
                          }`}
                      >
                        {ingredient}
                      </label>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="instructions" className="px-6 py-5">
            <div className="space-y-6">
              {recipe.steps?.map((step, index) => (
                <div
                  key={index}
                  className={`flex gap-4 p-3 rounded-lg ${currentStep === step.step_number ? "bg-orange-50 border border-orange-200" : ""
                    }`}
                >
                  <div className="shrink-0 w-8 h-8 rounded-full bg-orange-100 text-orange-700 flex items-center justify-center">
                    {step.step_number}
                  </div>
                  <p className="flex-1 text-gray-700 pt-1">{step.instruction}</p>
                </div>
              )) || (
                  <p>No instructions available</p>
                )}
            </div>
          </TabsContent>

          <TabsContent value="video" className="px-6 py-5">
            {/* Show YouTube video if URL is available in recipe */}
            {recipe.video_url || youtubeUrl ? (
              <>
                <div className="aspect-video w-full rounded-lg overflow-hidden mb-2">
                  <iframe
                    src={getYoutubeEmbedUrl(recipe.video_url || youtubeUrl || "")}
                    className="w-full h-full"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                    title="Recipe Video Tutorial"
                  />
                </div>
                <div className="text-xs text-gray-500 break-all">
                  <span className="font-medium">YouTube URL: </span>
                  <a href={recipe.video_url || youtubeUrl} target="_blank" rel="noopener noreferrer" className="underline text-blue-600">
                    {recipe.video_url || youtubeUrl}
                  </a>
                </div>
              </>
            ) : (
              <div className="aspect-video w-full rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center bg-gray-50">
                <div className="text-center px-6">
                  <LinkIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-600">No video added yet</p>
                  <p className="text-sm text-gray-500 mt-1">
                    Add a YouTube URL above to see the tutorial
                  </p>
                </div>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>

      {/* Voice Command Button */}
      <VoiceCommandButton
        sessionId={sessionId}
        onCommand={handleVoiceCommand}
      />
    </div>
  );
}