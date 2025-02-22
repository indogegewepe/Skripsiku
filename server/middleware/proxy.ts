export default defineEventHandler(async (event) => {
    if (event.node.req.url?.startsWith('/api/')) {
      return proxyRequest(event, 'http://127.0.0.1:8000', { fetch: $fetch });
    }
  });
