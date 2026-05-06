/**
 * VidyutSeva API Service
 * Handles all communication with the backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

// Types for sensor data
export const SensorDataTypes = {
  SOLAR_INVERTER: 'solar_inverter',
  GRID_MONITOR: 'grid_monitor',
  WEATHER: 'weather',
};

/**
 * Send sensor data to the backend
 * @param {Object} sensorData - Sensor data object
 * @returns {Promise<Object>} - Response from backend
 */
export const sendSensorData = async (sensorData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/invocations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        input: sensorData,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error sending sensor data:', error);
    throw error;
  }
};

/**
 * Get fault detection results
 * @param {number} voltage - Voltage reading (volts)
 * @param {number} current - Current reading (amps)
 * @param {number} temperature - Temperature (celsius)
 * @returns {Promise<Object>} - Fault detection results
 */
export const detectFaults = async (voltage, current, temperature) => {
  const sensorData = {
    voltage,
    current,
    temperature,
    timestamp: new Date().toISOString(),
    location: 'farm_001', // Can be customized
  };

  return sendSensorData(sensorData);
};

/**
 * Get demand forecast
 * @returns {Promise<Object>} - Demand forecast data
 */
export const getDemandForecast = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/forecast`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error getting forecast:', error);
    throw error;
  }
};

/**
 * Get agent status
 * @returns {Promise<Object>} - Agent status
 */
export const getAgentStatus = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/agent/status`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error getting agent status:', error);
    throw error;
  }
};

/**
 * Health check - verify backend is running
 * @returns {Promise<boolean>} - true if backend is healthy
 */
export const healthCheck = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    return response.ok;
  } catch (error) {
    console.warn('Backend health check failed:', error);
    return false;
  }
};

/**
 * Send solar brand selection from mobile app
 * @param {string} brand - Selected brand
 * @param {string} farmerId - Farmer ID
 * @returns {Promise<Object>} - Confirmation response
 */
export const selectSolarBrand = async (brand, farmerId = 'farmer_001') => {
  try {
    const response = await fetch(`${API_BASE_URL}/solar-selection`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        brand,
        farmerId,
        timestamp: new Date().toISOString(),
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error selecting solar brand:', error);
    throw error;
  }
};

export default {
  sendSensorData,
  detectFaults,
  getDemandForecast,
  getAgentStatus,
  healthCheck,
  selectSolarBrand,
};
