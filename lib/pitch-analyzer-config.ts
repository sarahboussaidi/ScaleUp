// API Configuration for Pitch Analyzer

export const API_CONFIG = {
  // Backend API URL
  BASE_URL: process.env.NEXT_PUBLIC_PITCH_API_URL || "http://localhost:5000",

  // Endpoints
  ENDPOINTS: {
    HEALTH: "/api/health",
    ANALYZE_EMOTION: "/api/analyze/emotion",
    ANALYZE_STRESS: "/api/analyze/stress",
    ANALYZE_POSTURE: "/api/analyze/posture",
    ANALYZE_VOICE_EMOTION: "/api/analyze/voice-emotion",
  },

  // Timeouts (in ms)
  TIMEOUTS: {
    HEALTH_CHECK: 5000,
    ANALYSIS: 10000,
  },

  // Camera settings
  CAMERA: {
    WIDTH: 640,
    HEIGHT: 480,
    FRAME_RATE: 30,
  },
};

// Helper function to make API calls
export async function analyzeFrame(
  endpoint: string,
  frameBase64: string,
  timeout: number = API_CONFIG.TIMEOUTS.ANALYSIS
): Promise<any> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(`${API_CONFIG.BASE_URL}${endpoint}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ frame: frameBase64 }),
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  } finally {
    clearTimeout(timeoutId);
  }
}

// Check if backend is available
export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.HEALTH}`, {
      method: "GET",
    });
    return response.ok;
  } catch {
    return false;
  }
}

// Analyze audio for voice emotion
export async function analyzeVoiceEmotion(
  audioBlob: Blob,
  timeout: number = API_CONFIG.TIMEOUTS.ANALYSIS
): Promise<any> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const reader = new FileReader();
    
    return new Promise((resolve, reject) => {
      reader.onload = async () => {
        try {
          const audioBase64 = reader.result as string;
          
          const response = await fetch(
            `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.ANALYZE_VOICE_EMOTION}`,
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({ audio: audioBase64 }),
              signal: controller.signal,
            }
          );

          if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
          }

          const result = await response.json();
          resolve(result);
        } catch (error) {
          reject(error);
        }
      };
      
      reader.onerror = () => {
        reject(new Error("Failed to read audio blob"));
      };
      
      reader.readAsDataURL(audioBlob);
    });
  } finally {
    clearTimeout(timeoutId);
  }
}
