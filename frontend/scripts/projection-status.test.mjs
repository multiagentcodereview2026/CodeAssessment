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
  assert.match(html, /Preparing revision verification/);
  assert.match(html, /animate-spin/);
  assert.match(html, /aria-busy="true"/);
  assert.doesNotMatch(html, /\/100|Retry score projection/);
});
test('slow processing describes the wait without promising a completion time', () => {
  const html = render({ pending: true }, { slow: true });
  assert.match(html, /This is taking longer/);
  assert.doesNotMatch(html, /\d+ (?:seconds|minutes)|Retry score projection/);
});

test('quota wait is distinguished from running candidate tests', () => {
  const html = render({ pending: true, phase: 'waiting_quota', message: 'Waiting for AI quota.' });
  assert.match(html, /Waiting for AI quota/);
  assert.doesNotMatch(html, /Running candidate tests|\/100|Retry score projection/);
});

test('only a recorded quota deadline produces a countdown', () => {
  const html = render({ pending: true, phase: 'waiting_quota', next_retry_at: new Date(Date.now() + 60000).toISOString() });
  assert.match(html, /Next check in 1:00/);
  const unavailable = render({ pending: false, message: 'AI guide unavailable right now. Try later.' });
  assert.doesNotMatch(unavailable, /Next check in|\d+:\d\d/);
});

test('sandbox recovery offers verification of the saved draft', () => {
  const html = render({ pending: false, resume_saved_draft: true, retry_allowed: true, message: 'The sandbox could not finish.' });
  assert.match(html, /Verify saved draft again/);
  assert.doesNotMatch(html, /\/100/);
});

test('a corrected release rule offers an explicit recheck without a fabricated score', () => {
  const html = render({ pending: false, retry_allowed: true, policy_update_available: true,
    message: 'A corrected release rule is available.' });
  assert.match(html, /Recheck with corrected rule/);
  assert.doesNotMatch(html, /\/100/);
});

test('attempt limit removes retry controls', () => {
  const html = render({ available: false, verified: false, retry_allowed: false,
    status: 'attempt_limit', message: 'Verification stopped after two unsuccessful attempts.' });
  assert.match(html, /Verification stopped after two unsuccessful attempts/);
  assert.doesNotMatch(html, /<button|animate-spin/);
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
