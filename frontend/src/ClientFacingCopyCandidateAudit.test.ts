import { readdirSync, readFileSync } from 'node:fs';
import { basename, relative, resolve } from 'node:path';
import ts from 'typescript';
import { describe, expect, it } from 'vitest';

const SRC_ROOT = resolve(process.cwd(), 'src');

const TECHNICAL_COPY_PATTERNS = [
  { label: 'agentic/internal AI terminology', re: /\b(?:agentique|agentic)\b/i },
  { label: 'legacy terminology', re: /\blegacy\b/i },
  { label: 'snapshot implementation terminology', re: /\bsnapshot\b/i },
  { label: 'runtime implementation terminology', re: /\bruntime\b/i },
  { label: 'backend/frontend implementation terminology', re: /\b(?:backend|frontend)\b/i },
  { label: 'pipeline implementation terminology', re: /\bpipeline\b/i },
  { label: 'fail-closed implementation terminology', re: /\bfail[ -]?closed\b/i },
  { label: 'feature-flag implementation terminology', re: /\bfeature[ -]?flag\b/i },
  { label: 'endpoint implementation terminology', re: /\bendpoint\b/i },
  { label: 'internal engine terminology', re: /\bmoteur\s+(?:local|safety|clinique|de\s+s[ée]curit[ée])\b/i },
  { label: 'internal lot/version rule terminology', re: /\b(?:lot\s+[A-Z]?\d+|r[èe]gle\s+V\d+)\b/i },
  { label: 'internal blocked-state wording', re: /\b(?:suggestion\s+clinique|contr[oô]le\s+clinique\s+automatique)\s+bloqu[ée]e?\b/i },
  { label: 'implementation materialization wording', re: /\bnon\s+mat[ée]rialis[ée]\b/i },
  { label: 'internal product version in prescription UI', re: /\bPrescription\s+Intelligence\s+V\d+\b/i },
  { label: 'AI implementation label', re: /\bSuggestion\s+IA\b/i },
  { label: 'implementation-centric form wording', re: /\bArchitecture\s+de\s+la\s+Forme\b/i },
  { label: 'unsupported AI action claim', re: /\b(?:Lancer|R[ée]g[ée]n[ée]rer)\s+Analyse\s+IA\b/i },
  { label: 'technical certification claim', re: /\bIA\s+certifi[ée]e?\b/i },
];

const USER_COPY_ATTRIBUTES = new Set([
  'alt',
  'aria-label',
  'aria-description',
  'placeholder',
  'title',
]);

const USER_COPY_PROPERTIES = new Set([
  'label',
  'title',
  'subtitle',
  'description',
  'message',
  'caption',
  'helperText',
  'emptyText',
  'placeholder',
]);

const USER_NOTICE_METHODS = new Set(['alert', 'confirm', 'error', 'success', 'loading']);

type Finding = {
  file: string;
  line: number;
  source: string;
  reason: string;
  text: string;
};

const isSourceFile = (name: string) => /\.(?:ts|tsx)$/.test(name)
  && !/\.(?:test|spec)\.(?:ts|tsx)$/.test(name)
  && !name.endsWith('.d.ts');

const collectSourceFiles = (dir: string): string[] => {
  const result: string[] = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === 'node_modules' || entry.name === 'dist' || entry.name === '__tests__') continue;
    const fullPath = resolve(dir, entry.name);
    if (entry.isDirectory()) result.push(...collectSourceFiles(fullPath));
    else if (entry.isFile() && isSourceFile(entry.name)) result.push(fullPath);
  }
  return result;
};

const literalText = (node: ts.Node | undefined): string | null => {
  if (!node) return null;
  if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) return node.text;
  return null;
};

const propertyName = (node: ts.PropertyName): string | null => {
  if (ts.isIdentifier(node) || ts.isStringLiteral(node)) return node.text;
  return null;
};

const lineFor = (sourceFile: ts.SourceFile, node: ts.Node) =>
  sourceFile.getLineAndCharacterOfPosition(node.getStart(sourceFile)).line + 1;

const inspectText = (
  findings: Finding[],
  sourceFile: ts.SourceFile,
  node: ts.Node,
  source: string,
  rawText: string,
) => {
  const text = rawText.replace(/\s+/g, ' ').trim();
  if (!text) return;
  for (const pattern of TECHNICAL_COPY_PATTERNS) {
    if (pattern.re.test(text)) {
      findings.push({
        file: relative(SRC_ROOT, sourceFile.fileName),
        line: lineFor(sourceFile, node),
        source,
        reason: pattern.label,
        text,
      });
    }
  }
};

const inspectExpressionLiterals = (
  findings: Finding[],
  sourceFile: ts.SourceFile,
  expression: ts.Expression | undefined,
  source: string,
) => {
  if (!expression) return;
  const visit = (node: ts.Node) => {
    const text = literalText(node);
    if (text !== null) inspectText(findings, sourceFile, node, source, text);
    ts.forEachChild(node, visit);
  };
  visit(expression);
};

const isUserNoticeCall = (node: ts.CallExpression): boolean => {
  const expression = node.expression;
  if (ts.isIdentifier(expression)) return USER_NOTICE_METHODS.has(expression.text);
  if (!ts.isPropertyAccessExpression(expression)) return false;
  const owner = expression.expression.getText();
  const method = expression.name.text;
  return (owner === 'toast' && USER_NOTICE_METHODS.has(method))
    || (owner === 'window' && (method === 'alert' || method === 'confirm'));
};

const auditFile = (file: string): Finding[] => {
  const text = readFileSync(file, 'utf8');
  const sourceFile = ts.createSourceFile(
    file,
    text,
    ts.ScriptTarget.Latest,
    true,
    file.endsWith('.tsx') ? ts.ScriptKind.TSX : ts.ScriptKind.TS,
  );
  const findings: Finding[] = [];

  const visit = (node: ts.Node) => {
    if (ts.isJsxText(node)) {
      inspectText(findings, sourceFile, node, 'jsx-text', node.getText(sourceFile));
      return;
    }

    if (ts.isJsxAttribute(node)) {
      const name = node.name.getText(sourceFile);
      if (USER_COPY_ATTRIBUTES.has(name)) {
        if (node.initializer && ts.isStringLiteral(node.initializer)) {
          inspectText(findings, sourceFile, node.initializer, `attribute:${name}`, node.initializer.text);
        } else if (node.initializer && ts.isJsxExpression(node.initializer)) {
          inspectExpressionLiterals(findings, sourceFile, node.initializer.expression, `attribute:${name}`);
        }
      }
      return;
    }

    if (ts.isJsxExpression(node)
      && (ts.isJsxElement(node.parent) || ts.isJsxFragment(node.parent) || ts.isJsxSelfClosingElement(node.parent))) {
      inspectExpressionLiterals(findings, sourceFile, node.expression, 'jsx-expression');
      return;
    }

    if (ts.isPropertyAssignment(node)) {
      const name = propertyName(node.name);
      if (name && USER_COPY_PROPERTIES.has(name)) {
        const textValue = literalText(node.initializer);
        if (textValue !== null) inspectText(findings, sourceFile, node.initializer, `copy-property:${name}`, textValue);
      }
    }

    if (ts.isCallExpression(node) && isUserNoticeCall(node)) {
      const textValue = literalText(node.arguments[0]);
      if (textValue !== null) inspectText(findings, sourceFile, node.arguments[0], 'user-notice', textValue);
    }

    ts.forEachChild(node, visit);
  };

  visit(sourceFile);
  return findings;
};

describe('client-facing copy candidate audit', () => {
  it('reports implementation language that can leak into rendered practitioner copy', () => {
    const findings = collectSourceFiles(SRC_ROOT).flatMap(auditFile);
    const report = findings
      .sort((a, b) => a.file.localeCompare(b.file) || a.line - b.line)
      .map(finding => `${finding.file}:${finding.line} [${finding.source}] ${finding.reason}: ${finding.text}`);

    if (report.length > 0) {
      console.error(`CLIENT_FACING_COPY_CANDIDATES=${report.length}\n${report.join('\n')}`);
    }

    expect(report, `Technical/internal wording candidates:\n${report.join('\n')}`).toEqual([]);
  });
});
