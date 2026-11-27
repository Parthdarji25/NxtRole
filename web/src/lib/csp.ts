/**
 * The content security policy: the browser's list of what a page may load and run.
 * Scripts need the one-time "nonce" of this request, so injected scripts cannot run.
 */
export function buildContentSecurityPolicy(options: {
  nonce: string;
  isDevelopment: boolean;
  isHttps: boolean;
}): string {
  const { nonce, isDevelopment, isHttps } = options;
  const directives = [
    "default-src 'self'",
    // 'unsafe-eval' is needed by React's debugging tools in development only.
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${isDevelopment ? " 'unsafe-eval'" : ""}`,
    // Style attributes are used by React and the UI primitives; they cannot run code.
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' blob: data:",
    "font-src 'self'",
    "connect-src 'self'",
    "worker-src 'self'",
    "manifest-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
    // Only on HTTPS: on a local http address it would break loading.
    ...(isHttps ? ["upgrade-insecure-requests"] : []),
  ];
  return directives.join("; ");
}
