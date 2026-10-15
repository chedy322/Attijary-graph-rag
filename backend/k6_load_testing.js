import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 2 }, // Ramp up to 5 VUs
    { duration: '2m', target: 2 },  // Hold at 5 VUs
    { duration: '30s', target: 0 }, // Ramp down
  ],
  thresholds: {
    http_req_failed: ['rate<0.05'],     // Max 5% failures allowed
    http_req_duration: ['p(90)<10000'], // 90% of requests must be under 10s
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:3000'; // Make sure this matches your Flask/Gunicorn port

export default function () {
  // Step 1: Chats request
  const chatsRes = http.get(`${BASE_URL}/api/v1/agent/chats`);
  check(chatsRes, {
    'chats status is 200': (r) => r.status === 200,
  });

  // Pause 2 seconds between sync and query
  sleep(2);

  // Step 2: Agent Query request
  const payload = JSON.stringify({ query: 'Test query for GraphRAG' });
  const params = { headers: { 'Content-Type': 'application/json' } };

  const queryRes = http.post(`${BASE_URL}/api/v1/agent/query`, payload, params);
  check(queryRes, {
    'query status is 200': (r) => r.status === 200,
  });

  // CRITICAL: 10-second human think time so VUs do not flood the 3 threads continuously
  sleep(10);
}