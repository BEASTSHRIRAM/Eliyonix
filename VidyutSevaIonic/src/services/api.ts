/**
 * VidyutSeva API Service
 * Handles communication with FastAPI backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

interface SensorData {
  voltage: number;
  current: number;
  temperature: number;
  inverter_id?: string;
  village_id?: string;
}

interface BrandSelectionResponse {
  status: string;
  message: string;
  brand: string;
  farmerId: string;
}

interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

interface AgentStatusResponse {
  status: string;
  agents?: {
    fault_detector: string;
    load_forecaster: string;
    alert_dispatcher: string;
  };
  error?: string;
}

interface SensorDataResponse {
  execution_id: string;
  should_alert: boolean;
  alert_message: string;
  fault_detected: boolean;
  anomaly_score: number;
  fault_type: string;
  is_demand_spike: boolean;
  demand_forecast: unknown;
  errors?: string[];
  error?: string;
}

/**
 * Submit solar brand selection from mobile app
 */
export async function submitBrandSelection(
  brand: string,
  farmerId: string = 'farmer_001'
): Promise<BrandSelectionResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/solar-selection`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        brand,
        farmerId,
      }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error submitting brand selection:', error);
    throw error;
  }
}

/**
 * Send sensor data to backend for processing
 */
export async function sendSensorData(sensorData: SensorData): Promise<SensorDataResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/invocations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        sensor_data: sensorData,
      }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error sending sensor data:', error);
    throw error;
  }
}

/**
 * Check backend health
 */
export async function healthCheck(): Promise<HealthResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error checking health:', error);
    throw error;
  }
}

/**
 * Get current agent status
 */
export async function getAgentStatus(): Promise<AgentStatusResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/agent/status`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to get agent status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error getting agent status:', error);
    throw error;
  }
}

/**
 * Get demand forecast
 */
export async function getDemandForecast(): Promise<unknown> {
  try {
    const response = await fetch(`${API_BASE_URL}/forecast`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to get forecast: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error getting forecast:', error);
    throw error;
  }
}
