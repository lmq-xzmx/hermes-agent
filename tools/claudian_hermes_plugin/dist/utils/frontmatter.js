/**
 * Front Matter Parser - 解析 Obsidian 笔记的 YAML front matter
 */
const FRONT_MATTER_REGEX = /^---\n([\s\S]*?)\n---\n/;
export function parseFrontMatter(content) {
    const match = content.match(FRONT_MATTER_REGEX);
    if (!match) {
        return null;
    }
    const yamlStr = match[1];
    const result = {};
    for (const line of yamlStr.split('\n')) {
        const colonIndex = line.indexOf(':');
        if (colonIndex === -1)
            continue;
        const key = line.slice(0, colonIndex).trim();
        let value = line.slice(colonIndex + 1).trim();
        // 移除引号
        if ((value.startsWith('"') && value.endsWith('"')) ||
            (value.startsWith("'") && value.endsWith("'"))) {
            value = value.slice(1, -1);
        }
        switch (key) {
            case 'title':
                result.title = value;
                break;
            case 'tags':
                // 解析数组格式: [tag1, tag2] 或 - tag1\n - tag2
                if (value.startsWith('[')) {
                    try {
                        result.tags = JSON.parse(value);
                    }
                    catch {
                        result.tags = value.replace(/[\[\]]/g, '').split(',').map(t => t.trim());
                    }
                }
                else {
                    result.tags = value.split(',').map(t => t.trim());
                }
                break;
            case 'status':
                if (['draft', 'published', 'completed'].includes(value)) {
                    result.status = value;
                }
                break;
            case 'team_space':
                result.team_space = value === '' || value === 'null' ? null : value;
                break;
            case 'aliases':
                if (value.startsWith('[')) {
                    try {
                        result.aliases = JSON.parse(value);
                    }
                    catch {
                        result.aliases = [];
                    }
                }
                else {
                    result.aliases = [value];
                }
                break;
            case 'created':
                result.created = value;
                break;
            case 'modified':
                result.modified = value;
                break;
            case 'source':
                result.source = value;
                break;
        }
    }
    return result;
}
export function extractContent(body) {
    // 移除 front matter 后返回正文
    return body.replace(FRONT_MATTER_REGEX, '');
}
export function extractLinks(content) {
    // 简单的 wiki link 提取 [[link]]
    const wikiLinkRegex = /\[\[([^\]|]+)(?:\|[^\]]+)?\]\]/g;
    const links = [];
    let match;
    while ((match = wikiLinkRegex.exec(content)) !== null) {
        links.push(match[1]);
    }
    return links;
}
//# sourceMappingURL=frontmatter.js.map