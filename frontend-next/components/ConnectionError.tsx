'use client';

interface ConnectionErrorProps {
  apiUrl: string;
}

export function ConnectionError({ apiUrl }: ConnectionErrorProps) {
  const isHttp = apiUrl.startsWith('http://');
  const isHttps = apiUrl.startsWith('https://');

  if (!isHttp) return null; // Only show if using HTTP

  return (
    <div className="fixed bottom-4 right-4 max-w-md bg-red-900/90 border-2 border-red-500 rounded-lg p-4 z-50 backdrop-blur-sm">
      <div className="flex items-start gap-3">
        <div className="text-2xl">⚠️</div>
        <div className="flex-1">
          <h3 className="font-bold text-red-200 mb-1">Mixed Content Error</h3>
          <p className="text-sm text-red-100 mb-2">
            Vercel serves over HTTPS, but your backend is HTTP. Browsers block this for security.
          </p>
          <div className="text-xs text-red-200/80 space-y-1">
            <p><strong>Quick Fix:</strong> Set up HTTPS for your backend:</p>
            <ul className="list-disc list-inside ml-2 space-y-0.5">
              <li>Use nginx reverse proxy with Let's Encrypt</li>
              <li>Or use Cloudflare Tunnel (free)</li>
              <li>Or set <code className="bg-black/30 px-1 rounded">NEXT_PUBLIC_API_URL</code> to HTTPS endpoint</li>
            </ul>
          </div>
          <div className="mt-3 pt-3 border-t border-red-500/30">
            <p className="text-xs text-red-200/60">
              Current API: <code className="bg-black/30 px-1 rounded">{apiUrl}</code>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
