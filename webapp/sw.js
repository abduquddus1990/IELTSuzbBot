// Minimal service worker: makes the browser version installable (PWA). Network-first, no offline exam.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (event) => event.waitUntil(self.clients.claim()));
self.addEventListener('fetch', () => {});
