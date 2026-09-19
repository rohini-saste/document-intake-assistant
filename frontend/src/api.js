const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';

export const chatWithAssistant = async (message, currentState) => {
  const response = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message, state: currentState }),
  });
  if (!response.ok) {
    throw new Error('Failed to communicate with the server');
  }
  return response.json();
};

export const resetSession = async () => {
  const response = await fetch(`${API_URL}/reset`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  if (!response.ok) {
    throw new Error('Failed to reset the server session');
  }
  return response.json();
};
