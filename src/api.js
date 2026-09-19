const defaultApiUrl = import.meta.env.DEV ? "http://localhost:8000" : window.location.origin;
const API_URL = (__FLIGHT_API_URL__ || defaultApiUrl).replace(/\/$/, "");

async function request(path) {
  const response = await fetch(`${API_URL}${path}`);
  if (!response.ok) throw new Error(`API request failed (${response.status})`);
  return response.json();
}

export function getFlights() {
  return request("/flights?limit=1000");
}

export function getAircraft() {
  return request("/aircraft");
}

export function getAirports() {
  return request("/airports");
}

export function getRegistration(registration) {
  return request(`/registrations/${encodeURIComponent(registration)}`);
}