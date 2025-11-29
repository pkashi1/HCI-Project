import { Mic, MicOff } from "lucide-react";
import { motion } from "framer-motion";
import { useState, useEffect, useRef } from "react";
import { toast } from "sonner";

interface VoiceCommandButtonProps {
  onCommand?: (command: string) => void;
  sessionId?: string | null;
}

export function VoiceCommandButton({ onCommand, sessionId }: VoiceCommandButtonProps) {
  const [isActive, setIsActive] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    // Initialize speech recognition
    if (typeof window !== 'undefined') {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        
        recognition.onresult = (event: any) => {
          const transcript = event.results[0][0].transcript;
          console.log('Recognized:', transcript);
          setIsListening(false);
          
          if (onCommand) {
            onCommand(transcript);
          } else {
            // Default handling
            toast.info(`You said: ${transcript}`);
          }
        };
        
        recognition.onerror = (event: any) => {
          console.error('Speech recognition error', event.error);
          setIsListening(false);
          setIsActive(false);
          toast.error('Speech recognition error occurred');
        };
        
        recognition.onend = () => {
          setIsListening(false);
          if (isActive) {
            // Auto-restart if still active
            setTimeout(() => {
              if (isActive && recognitionRef.current) {
                recognitionRef.current.start();
                setIsListening(true);
              }
            }, 100);
          }
        };
        
        recognitionRef.current = recognition;
      } else {
        console.warn('Speech recognition not supported in this browser');
      }
    }
    
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [onCommand]);

  const toggleVoice = () => {
    if (!recognitionRef.current) {
      toast.error('Speech recognition not supported in this browser');
      return;
    }
    
    if (isActive) {
      // Stop listening
      recognitionRef.current.stop();
      setIsActive(false);
      setIsListening(false);
    } else {
      // Start listening
      try {
        recognitionRef.current.start();
        setIsActive(true);
        setIsListening(true);
        toast.info('Listening... Speak now');
      } catch (error) {
        console.error('Error starting speech recognition', error);
        toast.error('Failed to start voice recognition');
      }
    }
  };

  return (
    <div className="fixed bottom-24 right-4 z-40">
      <motion.button
        onClick={toggleVoice}
        className={`w-16 h-16 rounded-full flex items-center justify-center shadow-lg transition-colors ${
          isActive
            ? isListening 
              ? "bg-orange-600 text-white" 
              : "bg-orange-500 text-white"
            : "bg-white text-orange-600 border-2 border-orange-600"
        }`}
        whileTap={{ scale: 0.95 }}
      >
        <motion.div
          animate={
            isListening
              ? {
                  scale: [1, 1.2, 1],
                  opacity: [1, 0.8, 1],
                }
              : {}
          }
          transition={{
            duration: 1.5,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        >
          {isActive ? <Mic className="w-7 h-7" /> : <MicOff className="w-7 h-7" />}
        </motion.div>
      </motion.button>
      {isActive && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute bottom-20 right-0 bg-white px-3 py-2 rounded-lg shadow-md whitespace-nowrap text-sm"
        >
          {isListening ? "Listening..." : "Voice Active"}
        </motion.div>
      )}
    </div>
  );
}