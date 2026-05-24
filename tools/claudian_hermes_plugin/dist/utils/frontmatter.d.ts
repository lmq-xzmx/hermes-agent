/**
 * Front Matter Parser - 解析 Obsidian 笔记的 YAML front matter
 */
export interface ParsedFrontMatter {
    title?: string;
    tags?: string[];
    status?: 'draft' | 'published' | 'completed';
    team_space?: string | null;
    aliases?: string[];
    created?: string;
    modified?: string;
    source?: string;
}
export declare function parseFrontMatter(content: string): ParsedFrontMatter | null;
export declare function extractContent(body: string): string;
export declare function extractLinks(content: string): string[];
//# sourceMappingURL=frontmatter.d.ts.map