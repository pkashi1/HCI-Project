import { Bookmark, Clock, ChefHat } from "lucide-react";
import { Card } from "./ui/card";
import { Badge } from "./ui/badge";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import { useState } from "react";

interface RecipeCardProps {
  id: number;
  title: string;
  description: string;
  image: string;
  time: string;
  difficulty: string;
  tags: string[];
  onClick: () => void;
  isSaved?: boolean;
  onToggleSave?: () => void;
}

export function RecipeCard({
  title,
  description,
  image,
  time,
  difficulty,
  tags,
  onClick,
  isSaved = false,
  onToggleSave,
}: RecipeCardProps) {

  const handleSave = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onToggleSave) {
      onToggleSave();
    }
  };

  return (
    <Card
      className="overflow-hidden cursor-pointer hover:shadow-lg transition-shadow bg-white"
      onClick={onClick}
    >
      <div className="relative aspect-[16/9]">
        <ImageWithFallback
          src={image}
          alt={title}
          className="w-full h-full object-cover"
        />
        <button
          onClick={handleSave}
          className="absolute top-3 right-3 w-10 h-10 rounded-full bg-white/90 backdrop-blur-sm flex items-center justify-center hover:bg-white transition-colors"
        >
          <Bookmark
            className={`w-5 h-5 ${isSaved ? "fill-orange-600 text-orange-600" : "text-gray-700"
              }`}
          />
        </button>
      </div>
      <div className="p-3">
        <h3 className="mb-1.5">{title}</h3>
        <p className="text-gray-600 text-sm mb-2.5 line-clamp-1">{description}</p>
        <div className="flex items-center gap-4 mb-2.5 text-sm text-gray-600">
          <div className="flex items-center gap-1">
            <Clock className="w-4 h-4" />
            <span>{time}</span>
          </div>
          <div className="flex items-center gap-1">
            <ChefHat className="w-4 h-4" />
            <span>{difficulty}</span>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {tags.map((tag, index) => (
            <Badge
              key={index}
              variant="secondary"
              className="bg-orange-50 text-orange-700 hover:bg-orange-100"
            >
              {tag}
            </Badge>
          ))}
        </div>
      </div>
    </Card>
  );
}