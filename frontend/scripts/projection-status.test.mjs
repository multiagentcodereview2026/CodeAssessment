import assert from 'node:assert/strict';
import { after, test } from 'node:test';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { createServer } from 'vite';

// Render the production component without introducing another test dependency.
const server = await createServer({ configFile: false, server: { middlewareMode: true }, appType: 'custom' });
const { ProjectionStatusCard } = await server.ssrLoadModule('/src/components/student/ProjectionStatusCard.tsx');
after(() => server.close());
const render = (projection, overrides = {}) => renderToStaticMarkup(React.createElement(ProjectionStatusCard, {
  projection, slow: false, paused: false, connectionLost: false, retrying: false, error: '',
  onCheckAgain() {}, onRetry() {}, ...overrides,
}));

test('pending shows activity without a fabricated number or countdown', () => {
  const html = render({ pending: true });
  assert.match(html, /Calculating projected score/);
  assert.match(html, /animate-spin/);
  assert.match(html, /aria-busy="true"/);
  assert.doesNotMatch(html, /\/100|Retry score projection/);
});
test('slow processing keeps guidance usable and promises no time estimate', () => {
  assert.match(render({ pending: true }, { slow: true }), /Still checking your projected score/);
});
test('paused polling offers checking status instead of creating another candidate', () => {
  const html = render({ pending: true }, { paused: true });
  assert.match(html, /Automatic checking paused/);
  assert.match(html, /Check again/);
  assert.doesNotMatch(html, /animate-spin|Retry score projection/);
});
test('connection interruptions are distinguished from verification failure', () => {
  assert.match(render({ pending: true }, { connectionLost: true }), /connection was interrupted/);
});
test('verified improvement displays saved weights and weighted contributions', () => {
  const html = render({ available: true, verified: true, current_score: 86, projected_score: 100, expected_improvement: 14,
    comparison: { time: { current: { score: 60, weighted: 21 }, candidate: { score: 100, weight: .35, weighted: 35 } } },
    message: 'Your own implementation must be assessed separately.', alignment_review: 'ai_reviewed' });
  assert.match(html, /86 → 100\/100/);
  assert.match(html, /\+14/);
  assert.match(html, /35%/);
  assert.match(html, /21 → 35/);
  assert.match(html, /reviewed by AI/);
});
test('completed zero or negative gains are not verification errors', () => {
  for (const delta of [0, -2]) {
    const html = render({ available: true, verified: true, status: 'no_gain', current_score: 86,
      projected_score: 86 + delta, expected_improvement: delta });
    assert.match(html, /no score increase/);
    assert.doesNotMatch(html, /Retry score projection|Score projection unavailable/);
  }
});
test('unverified numeric scores are never presented as measured', () => {
  const html = render({ available: true, verified: false, projected_score: 100, message: 'Verification unavailable.' });
  assert.doesNotMatch(html, /100\/100|Measured candidate score/);
  assert.match(html, /Retry score projection/);
});
test('unavailable verification supports a disabled retry and visible errors', () => {
  const html = render({ available: false, message: 'Judge unavailable.' }, { retrying: true, error: 'Network error' });
  assert.match(html, /disabled/);
  assert.match(html, /Requesting verification/);
  assert.match(html, /role="alert"/);
});
test('older saved projections can request current guidance and alignment review', () => {
  const html = render({ available: true, verified: true, current_score: 86, projected_score: 100, expected_improvement: 14 });
  assert.match(html, /no guidance alignment review/);
  assert.match(html, /Recheck with current guidance/);
  assert.doesNotMatch(html, /Guidance alignment was reviewed by AI/);
});
