/**
 * 测试 Tag Filter - 标签过滤
 */

import { shouldSyncByTags, filterByTags, TagFilterMode } from '../tag_filter.js';

describe('Tag Filter', () => {
  describe('shouldSyncByTags - Selective Mode', () => {
    test('allows published status', () => {
      const content = `---
status: published
---
Content`;
      const result = shouldSyncByTags(content, TagFilterMode.SELECTIVE);
      expect(result.shouldSync).toBe(true);
    });

    test('allows completed status', () => {
      const content = `---
status: completed
---
Content`;
      const result = shouldSyncByTags(content, TagFilterMode.SELECTIVE);
      expect(result.shouldSync).toBe(true);
    });

    test('blocks personal tag', () => {
      const content = `---
tags: [personal]
---
Content`;
      const result = shouldSyncByTags(content, TagFilterMode.SELECTIVE);
      expect(result.shouldSync).toBe(false);
      expect(result.reason).toContain('blocked tag');
    });

    test('blocks draft tag', () => {
      const content = `---
tags: [draft]
---
Content`;
      const result = shouldSyncByTags(content, TagFilterMode.SELECTIVE);
      expect(result.shouldSync).toBe(false);
    });

    test('blocks missing front matter in selective mode', () => {
      const content = 'Just content without front matter';
      const result = shouldSyncByTags(content, TagFilterMode.SELECTIVE);
      expect(result.shouldSync).toBe(false);
    });
  });

  describe('shouldSyncByTags - Full Mode', () => {
    test('allows content without front matter', () => {
      const content = 'Plain content in full mode';
      const result = shouldSyncByTags(content, TagFilterMode.FULL);
      expect(result.shouldSync).toBe(true);
    });

    test('still blocks personal tag', () => {
      const content = `---
tags: [personal]
---
Content`;
      const result = shouldSyncByTags(content, TagFilterMode.FULL);
      expect(result.shouldSync).toBe(false);
    });

    test('still blocks draft tag', () => {
      const content = `---
tags: [draft]
---
Content`;
      const result = shouldSyncByTags(content, TagFilterMode.FULL);
      expect(result.shouldSync).toBe(false);
    });

    test('allows published tag', () => {
      const content = `---
tags: [published]
---
Content`;
      const result = shouldSyncByTags(content, TagFilterMode.FULL);
      expect(result.shouldSync).toBe(true);
    });
  });

  describe('filterByTags', () => {
    test('filters multiple files correctly', () => {
      const files = [
        { path: '/publish.md', content: '---\nstatus: published\n---\nContent' },
        { path: '/draft.md', content: '---\nstatus: draft\n---\nContent' },
        { path: '/personal.md', content: '---\ntags: [personal]\n---\nContent' },
      ];

      const results = filterByTags(files, TagFilterMode.SELECTIVE);

      expect(results.length).toBe(1);
      expect(results[0].path).toBe('/publish.md');
    });

    test('returns all files in full mode (except blocked)', () => {
      const files = [
        { path: '/a.md', content: 'Content A' },
        { path: '/b.md', content: '---\nstatus: draft\n---\nContent' },
      ];

      const results = filterByTags(files, TagFilterMode.FULL);

      expect(results.length).toBe(1);
      expect(results[0].path).toBe('/a.md');
    });
  });
});