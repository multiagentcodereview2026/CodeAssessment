import assert from 'node:assert/strict';
import { after, test } from 'node:test';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { createServer } from 'vite';

const server = await createServer({ configFile: false, server: { middlewareMode: true }, appType: 'custom' });
const { RouteFailureScreen } = await server.ssrLoadModule('/src/components/common/RouteFailureScreen.tsx');
after(() => server.close());
test('page-load recovery works for either role without claiming a submission was saved', () => {
  const html = renderToStaticMarkup(React.createElement(RouteFailureScreen, { onReload() {} }));
  assert.match(html, /role="alert"/);
  assert.match(html, /Reload page/);
  assert.match(html, /href="\/"/);
  assert.doesNotMatch(html, /submission was saved|\/submissions/);
});
