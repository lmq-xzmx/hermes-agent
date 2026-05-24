/**
 * 测试 Sensitive Content Scanner
 */

import { scanContent, formatScanReport, SensitiveType } from '../sensitive_scan.js';

describe('Sensitive Content Scanner', () => {
  describe('scanContent', () => {
    test('detects password patterns', () => {
      const content = 'password: "my_secret_password"';
      const result = scanContent(content, '/test.md');

      expect(result.safe).toBe(false);
      const passwordMatches = result.matches.filter(m => m.type === SensitiveType.PASSWORD);
      expect(passwordMatches.length).toBeGreaterThan(0);
    });

    test('detects API keys', () => {
      const content = 'api_key: sk-1234567890abcdefghijklmnopqrstuvwxyz';
      const result = scanContent(content, '/test.md');

      expect(result.safe).toBe(false);
      const apiKeyMatches = result.matches.filter(m => m.type === SensitiveType.API_KEY);
      expect(apiKeyMatches.length).toBeGreaterThan(0);
    });

    test('detects AWS keys', () => {
      const content = 'AWS_ACCESS_KEY=AKIA1234567890ABCDEF';
      const result = scanContent(content, '/test.md');

      expect(result.safe).toBe(false);
      const awsMatches = result.matches.filter(m => m.type === SensitiveType.AWS_KEY);
      expect(awsMatches.length).toBeGreaterThan(0);
    });

    test('detects credit card numbers', () => {
      const content = 'Card: 1234-5678-9012-3456';
      const result = scanContent(content, '/test.md');

      expect(result.safe).toBe(false);
      const ccMatches = result.matches.filter(m => m.type === SensitiveType.CREDIT_CARD);
      expect(ccMatches.length).toBeGreaterThan(0);
    });

    test('detects internal secrets', () => {
      const content = 'confidential: "internal only information"';
      const result = scanContent(content, '/test.md');

      // Internal secrets are medium severity, so may not make it unsafe
      expect(result.matches.length).toBeGreaterThan(0);
    });

    test('clean content is safe', () => {
      const content = `
# Test Document

This is a normal document with no sensitive content.
It talks about software architecture and best practices.

## Section 1

More normal content here.
      `;
      const result = scanContent(content, '/test.md');

      // Clean content should have no high severity matches
      const highSeverity = result.matches.filter(m => m.severity === 'high');
      expect(highSeverity.length).toBe(0);
    });

    test('returns scan duration', () => {
      const content = 'Normal content';
      const result = scanContent(content, '/test.md');

      expect(result.scanDuration).toBeGreaterThanOrEqual(0);
    });

    test('includes file path in matches', () => {
      const content = 'password: "secret"';
      const result = scanContent(content, '/my/vault/secret.md');

      for (const match of result.matches) {
        expect(match.path).toBe('/my/vault/secret.md');
      }
    });

    test('includes line numbers in matches', () => {
      const content = 'Line 1\npassword: "secret"\nLine 3';
      const result = scanContent(content, '/test.md');

      const passwordMatch = result.matches.find(m => m.type === SensitiveType.PASSWORD);
      expect(passwordMatch).toBeDefined();
      expect(passwordMatch!.line).toBe(2);  // password is on line 2
    });
  });

  describe('formatScanReport', () => {
    test('formats clean result', () => {
      const result = {
        safe: true,
        matches: [],
        scanDuration: 10,
      };

      const report = formatScanReport(result);
      expect(report).toContain('未发现敏感内容');
    });

    test('formats result with matches', () => {
      const result = {
        safe: false,
        matches: [
          { type: SensitiveType.PASSWORD, path: '/test.md', line: 1, snippet: 'password:', severity: 'high' as const },
          { type: SensitiveType.API_KEY, path: '/test.md', line: 2, snippet: 'sk-', severity: 'high' as const },
        ],
        scanDuration: 15,
      };

      const report = formatScanReport(result);
      expect(report).toContain('可疑内容');
      expect(report).toContain('高危');
    });
  });
});