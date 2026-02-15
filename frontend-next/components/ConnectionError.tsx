'use client';

interface ConnectionErrorProps {
  apiUrl: string;
}

export function ConnectionError({ apiUrl }: ConnectionErrorProps) {
  const isHttp = apiUrl.startsWith('http://');
  const isHttps = typeof window !== 'undefined' && window.location.protocol === 'https:';

  if (!isHttp || !isHttps) return null;

  return (
    <div className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50 max-w-2xl mx-4">
      <div className="bg-red-900/90 border-2 border-red-500 p-4 rounded-lg shadow-lg">
        <div className="flex items-start gap-3">
          <div className="text-2xl">⚠️</div>
          <div className="flex-1">
            <h3 className="font-bold text-red-200 mb-2">Mixed Content Error</h3>
            <p className="text-sm text-red-100 mb-3">
              Your frontend is served over HTTPS, but the backend is HTTP. Browsers block this for security.
            </p>
            <div className="bg-black/30 p-3 rounded text-xs font-mono text-red-200 mb-3">
              Backend: <span className="text-red-400">{apiUrl}</span>
            </div>
            <div className="text-xs text-red-200 space-y-1">
              <p><strong>Solutions:</strong></p>
              <ul className="list-disc list-inside ml-2 space-y-1">
                <li>Set up HTTPS for your backend (SSL certificate)</li>
                <li>Use a reverse proxy (nginx, Caddy) with SSL</li>
                <li>Use Cloudflare Tunnel or ngrok for HTTPS</li>
                <li>Set <code className="bg-black/50 px-1 rounded">NEXT_PUBLIC_API_URL</code> to HTTPS endpoint</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
