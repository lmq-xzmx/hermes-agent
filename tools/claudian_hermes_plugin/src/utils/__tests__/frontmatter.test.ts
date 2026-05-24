/**
 * 测试 Front Matter Parser
 */

import { parseFrontMatter, extractContent, extractLinks } from '../frontmatter.js';

describe('FrontMatter Parser', () => {
  describe('parseFrontMatter', () => {
    test('parses basic front matter', () => {
      const content = `---
title: Test Document
tags: [tech, project]
status: published
---
Content here`;

      const result = parseFrontMatter(content);

      expect(result).not.toBeNull();
      expect(result!.title).toBe('Test Document');
      expect(result!.tags).toEqual(['tech', 'project']);
      expect(result!.status).toBe('published');
    });

    test('returns null for content without front matter', () => {
      const content = 'Just plain content without front matter';
      const result = parseFrontMatter(content);
      expect(result).toBeNull();
    });

    test('handles empty tags', () => {
      const content = `---
title: Empty Tags Test
tags: []
---
Content`;

      const result = parseFrontMatter(content);
      expect(result!.tags).toEqual([]);
    });

    test('parses team_space null', () => {
      const content = `---
title: Private Note
team_space: null
---
Content`;

      const result = parseFrontMatter(content);
      expect(result!.team_space).toBeNull();
    });

    test('handles quoted values', () => {
      const content = `---
title: "Quoted Title"
---
Content`;

      const result = parseFrontMatter(content);
      expect(result!.title).toBe('Quoted Title');
    });
  });

  describe('extractContent', () => {
    test('removes front matter and returns body', () => {
      const content = `---
title: Test
---
This is the body`;

      const body = extractContent(content);
      expect(body).toBe('This is the body');
    });

    test('returns original if no front matter', () => {
      const content = 'Plain content';
      const body = extractContent(content);
      expect(body).toBe('Plain content');
    });
  });

  describe('extractLinks', () => {
    test('extracts wiki links', () => {
      const content = 'This links to [[Page One]] and [[Page Two|alias]]';
      const links = extractLinks(content);
      expect(links).toContain('Page One');
      expect(links).toContain('Page Two');
    });

    test('returns empty array for no links', () => {
      const content = 'No wiki links here';
      const links = extractLinks(content);
      expect(links).toEqual([]);
    });
  });
});