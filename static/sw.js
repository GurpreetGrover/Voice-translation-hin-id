// A minimal service worker to satisfy PWA install requirements
const CACHE_NAME = 'translator-v1';

// Install event - caches the basic UI shell
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll([
                '/',
                '/index.html',
                '/manifest.json'
                // Add your CSS and JS file names here if you have them, e.g., '/style.css', '/app.js'
            ]);
        })
    );
    self.skipWaiting();
});

// Fetch event - network-first approach so your API calls don't get stuck
self.addEventListener('fetch', (event) => {
    event.respondWith(
        fetch(event.request).catch(() => {
            return caches.match(event.request);
        })
    );
});