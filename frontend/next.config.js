const securityHeaders = [
  {
    key: 'Strict-Transport-Security',
    value: 'max-age=63072000; includeSubDomains; preload'
  }
]

module.exports = {
  reactStrictMode: true,
  env: {
    API_URL: 'https://ergopad.io/api',
    FORM_EMAIL: 'ergopad.marketing@gmail.com',
  },
  async headers() {
    return [
      {
        // Apply these headers to all routes in your application.
        source: '/(.*)',
        headers: securityHeaders,
      },
    ]
  },
}
