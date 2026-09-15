import { readdirSync, readFileSync } from 'node:fs';
import { relative, resolve } from 'node:path';
import ts from 'typescript';
import { describe, expect, it } from 'vitest';

// Permanent regression gate: practitioner-facing copy must stay free of implementation terminology.
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
  { label: 'internal engine terminology', re: /\bmoteur\s+(?:local|safety|clinique|de\s+s[ée]curit[ée]|d[ée]terministe)\b/i },
  { label: 'deterministic implementation terminology', re: /\bd[ée]terministe(?:ment)?\b/i },
  { label: 'model-quality implementation jargon', re: /\bSOTA\b|z[ée]ro[- ]hallucination/i },
  { label: 'internal panoramic engine brand', re: /\bLoki[- ]Silvres(?:\s+V\d+)?\b/i },
  { label: 'internal lot/version terminology', re: /\b(?:lot\s+[A-Z]?\d+|r[èe]gle\s+V\d+|R(?:11|12|13|14|15))\b/i },
  { label: 'internal blocked-state wording', re: /\b(?:suggestion\s+clinique|contr[oô]le\s+clinique\s+automatique)\s+bloqu[ée]e?\b/i },
  { label: 'implementation materialization wording', re: /\bnon\s+mat[ée]rialis[ée]\b/i },
  { label: 'internal prescription version', re: /\bPrescription\s+Intelligence\s+V\d+\b/i },
  { label: 'AI implementation label', re: /\bSuggestion\s+IA\b/i },
  { label: 'LLM implementation label', re: /\bLLM\b/i },
  { label: 'internal brand/nickname', re: /\bGhost(?:\s+(?:Brain|Treasury|Intelligence|Elite))?\b/i },
  { label: 'internal studio label', re: /\b(?:Studio\s+(?:Agenda|Prescriptions?|C[ée]phalom[ée]trique|Panoramique|Documentaire|de\s+Design)|Quick\s+Document\s+Studio)\b/i },
  { label: 'internal science label', re: /\bElite\s+Science\s+Hub\b/i },
  { label: 'english marketplace label', re: /\bMarketplace\b/i },
  { label: 'english analytics label', re: /\bAnalytics(?:\s*&\s*Intelligence)?\b/i },
  { label: 'english frontdesk label', re: /\bFrontdesk\b/i },
  { label: 'roadmap exposed to user', re: /^(?:Bient[oô]t(?:\s+disponible)?|en\s+cours\s+de\s+finalisation)[.!]?$/i },
  { label: 'security implementation jargon', re: /\b(?:ECDH|LAN)\b/ },
  { label: 'internal control-plane terminology', re: /\bcontrol[- ]plane\b/i },
  { label: 'authentication implementation jargon', re: /\b(?:WebAuthn|JWT|session\s+UV)\b/i },
  { label: 'synchronization implementation jargon', re: /\b(?:backoff|Force\s+sync|Mode\s+sync|incident\s+sync)\b/i },
  { label: 'transport implementation jargon', re: /\b(?:HTTP|HTTPS)\b(?!:\/\/)|\bidempotence\b/i },
  { label: 'supply implementation jargon', re: /\b(?:Procurement|Backorder|Dispatch|Outcome)\b/i },
  { label: 'internal tenancy/version jargon', re: /\bTenant\b|\bP10\b/i },
  { label: 'raw internal workflow status', re: /\b(?:DRAFT|SENT_TO_PARTNER|MODIFIED_AFTER_SEND|CONFIRMED|FULFILLED|CANCELLED|WAITING_INVOICE|AMOUNT_MISMATCH|SUCCEEDED|DEGRADED|APPLIED)\b/ },
  { label: 'integration field jargon', re: /\b(?:URL\s+API|Mode\s+sync)\b/i },
];

const USER_COPY_ATTRIBUTES = new Set(['alt', 'aria-label', 'aria-description', 'placeholder', 'title', 'engineName', 'label', 'eyebrow', 'subtitle', 'description', 'message', 'caption', 'helperText', 'emptyText']);
const USER_COPY_PROPERTIES = new Set(['label', 'title', 'subtitle', 'description', 'message', 'body', 'caption', 'helperText', 'emptyText', 'placeholder']);
const USER_NOTICE_METHODS = new Set(['alert', 'confirm', 'error', 'success', 'loading']);

type Finding = { file: string; line: number; source: string; reason: string; text: string };

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

const propertyName = (node: ts.PropertyName): string | null =>
  ts.isIdentifier(node) || ts.isStringLiteral(node) ? node.text : null;

const lineFor = (sourceFile: ts.SourceFile, node: ts.Node) =>
  sourceFile.getLineAndCharacterOfPosition(node.getStart(sourceFile)).line + 1;

const inspectText = (findings: Finding[], sourceFile: ts.SourceFile, node: ts.Node, source: string, rawText: string) => {
  const text = rawText.replace(/\s+/g, ' ').trim();
  if (!text) return;
  for (const pattern of TECHNICAL_COPY_PATTERNS) {
    if (pattern.re.test(text)) {
      findings.push({ file: relative(SRC_ROOT, sourceFile.fileName), line: lineFor(sourceFile, node), source, reason: pattern.label, text });
    }
  }
};

const inspectRenderableExpression = (
  findings: Finding[],
  sourceFile: ts.SourceFile,
  expression: ts.Expression | undefined,
  source: string,
) => {
  if (!expression) return;
  const text = literalText(expression);
  if (text !== null) {
    inspectText(findings, sourceFile, expression, source, text);
    return;
  }
  if (ts.isParenthesizedExpression(expression)) {
    inspectRenderableExpression(findings, sourceFile, expression.expression, source);
    return;
  }
  if (ts.isConditionalExpression(expression)) {
    inspectRenderableExpression(findings, sourceFile, expression.whenTrue, source);
    inspectRenderableExpression(findings, sourceFile, expression.whenFalse, source);
  }
};

const isStyleExpression = (node: ts.JsxExpression) => {
  const parent = node.parent;
  return ts.isJsxElement(parent) && parent.openingElement.tagName.getText() === 'style';
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
  const sourceFile = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true, file.endsWith('.tsx') ? ts.ScriptKind.TSX : ts.ScriptKind.TS);
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
          inspectRenderableExpression(findings, sourceFile, node.initializer.expression, `attribute:${name}`);
        }
      }
      return;
    }
    if (ts.isJsxExpression(node) && !isStyleExpression(node)
      && (ts.isJsxElement(node.parent) || ts.isJsxFragment(node.parent))) {
      inspectRenderableExpression(findings, sourceFile, node.expression, 'jsx-expression');
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
  it('blocks implementation language from rendered practitioner copy', () => {
    const findings = collectSourceFiles(SRC_ROOT).flatMap(auditFile);
    const report = findings
      .sort((a, b) => a.file.localeCompare(b.file) || a.line - b.line)
      .map(f => `${f.file}:${f.line} [${f.source}] ${f.reason}: ${f.text}`);
    if (report.length > 0) console.error(`CLIENT_FACING_COPY_CANDIDATES=${report.length}\n${report.join('\n')}`);
    expect(report, `Technical/internal wording candidates:\n${report.join('\n')}`).toEqual([]);
  });
});
