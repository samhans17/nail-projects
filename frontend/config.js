// API Configuration
// Auto-detects if running locally or on RunPod

function getApiBaseUrl() {
    // Check if we're on RunPod (they typically use their domain)
    const hostname = window.location.hostname;

    // If localhost or 127.0.0.1, use local backend
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return 'http://localhost:8000';
    }

    // If on RunPod or remote, use same origin
    // RunPod exposes everything on the same port
    return window.location.origin;
}

const API_BASE_URL = getApiBaseUrl();
const API_URL = `${API_BASE_URL}/api/nails/segment`;
const API_URL_PROFESSIONAL = `${API_BASE_URL}/api/nails/render-professional`;
const API_MATERIALS_URL = `${API_BASE_URL}/api/materials`;

console.log('🔧 API Configuration:', {
    hostname: window.location.hostname,
    baseUrl: API_BASE_URL,
    segmentEndpoint: API_URL,
    professionalEndpoint: API_URL_PROFESSIONAL
});
