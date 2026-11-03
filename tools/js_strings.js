// Modified from Fizgig-Korean-Translated-Ver (Apache-2.0, Copyright 2026 ssain3d-lgtm and contributors).
// Extracts, via the AST, strings from JS sources such as app.js that may appear on screen.
//   node tools/js_strings.js <file.js>   ->  stdout: [{s, kind, line, ctx}, ...]
//
// - Concatenated strings like 'a ' + x + ' b' are extracted as one concatenated result "a {0} b", not as pieces
//   (because what actually appears on screen is the concatenated result). Expressions become {0} {1} ... placeholders.
// - `a ${x} b` template literals use the same format.
// - Strings that are not operands of a concatenation (e.g. branches of a conditional) are extracted separately.
// - ctx is where the string is used (prop:text, arg:querySelector, cmp, case ...), a clue for judging whether it is UI text.
"use strict";
const fs = require("fs");
const path = require("path");
let acorn, walk;
try {
  acorn = require("acorn"); walk = require("acorn-walk");
} catch (e) {
  const here = path.join(__dirname, "node_modules");
  acorn = require(path.join(here, "acorn")); walk = require(path.join(here, "acorn-walk"));
}

const src = fs.readFileSync(process.argv[2], "utf8");
const ast = acorn.parse(src, {ecmaVersion: "latest", locations: true, allowHashBang: true});
const out = [];
const emit = (s, kind, node, ctx, plural) => out.push({s, kind, line: node.loc.start.line, ctx, plural: plural || []});

const isStr = (n) => n && n.type === "Literal" && typeof n.value === "string";
const isConcat = (n) => n && n.type === "BinaryExpression" && n.operator === "+" && hasText(n);
// a + chain is string concatenation only when some operand is text (otherwise it is arithmetic)
function hasText(n) {
  if (isStr(n) || (n && n.type === "TemplateLiteral")) return true;
  if (n && n.type === "BinaryExpression" && n.operator === "+") return hasText(n.left) || hasText(n.right);
  return false;
}

// `cond ? "" : "s"`, `cond ? " has" : "s have"`: English number agreement. The Korean has no use for it.
const AGREEMENT = new Set(["", "s", "es", "ies", "y", " has", "s have", " is", "s are", " was", "s were", " it",
                           " them", "'s"]);
function isPlural(e) {
  if (!e || e.type !== "ConditionalExpression" || !isStr(e.consequent) || !isStr(e.alternate)) return false;
  const v = [e.consequent.value, e.alternate.value];
  return v.every((x) => AGREEMENT.has(x)) && v[0] !== v[1];
}

// Fold an operand into text with {n} placeholders. `st.n` counts them, `st.plural` collects the plural ones.
function fold(n, st) {
  if (isStr(n)) return n.value;
  if (n.type === "TemplateLiteral") {
    let s = "";
    n.quasis.forEach((q, i) => {
      s += q.value.cooked;
      if (i < n.expressions.length) { if (isPlural(n.expressions[i])) st.plural.push(st.n); s += "{" + (st.n++) + "}"; }
    });
    return s;
  }
  if (isConcat(n)) return fold(n.left, st) + fold(n.right, st);
  if (isPlural(n)) st.plural.push(st.n);
  return "{" + (st.n++) + "}";
}

function ctxOf(node, parent) {
  if (!parent) return "";
  switch (parent.type) {
    case "Property":
      if (parent.key === node) return "key";
      return "prop:" + (parent.key.name || parent.key.value);
    case "CallExpression": case "NewExpression": {
      const c = parent.callee;
      const name = c.type === "Identifier" ? c.name : (c.property && (c.property.name || c.property.value)) || "";
      const pos = parent.arguments.indexOf(node);
      return "arg" + (pos >= 0 ? pos : "") + ":" + name;
    }
    case "AssignmentExpression": {
      const l = parent.left;
      return "assign:" + (l.type === "MemberExpression" ? (l.property.name || l.property.value || "") : l.name || "");
    }
    case "BinaryExpression": return "cmp:" + parent.operator;
    case "SwitchCase": return "case";
    case "ConditionalExpression": return "cond";
    case "ReturnStatement": return "return";
    case "ArrayExpression": return "array";
    case "VariableDeclarator": return "var:" + (parent.id && parent.id.name || "");
    default: return parent.type;
  }
}

const claimed = new Set();   // nodes already emitted as part of a folded chain

walk.fullAncestor(ast, (node, _st, anc) => {
  const parent = anc.length > 1 ? anc[anc.length - 2] : null;
  if (claimed.has(node)) return;
  if (isConcat(node) && !(isConcat(parent) && parent.operator === "+" && hasText(parent))) {
    // the top of a concatenation chain: fold it, and claim every literal operand that went into it
    const st = {n: 0, plural: []};
    const s = fold(node, st);
    (function mark(n) {
      if (isStr(n) || n.type === "TemplateLiteral") claimed.add(n);
      else if (isConcat(n)) { claimed.add(n); mark(n.left); mark(n.right); }
    })(node);
    emit(s, "cat", node, ctxOf(node, parent), st.plural);
    return;
  }
  if (isStr(node)) emit(node.value, "str", node, ctxOf(node, parent));
  else if (node.type === "TemplateLiteral") {
    const st = {n: 0, plural: []};
    emit(fold(node, st), "tpl", node, ctxOf(node, parent), st.plural);
  }
});
// object keys are not visited by acorn-walk (Literal keys): label maps like {"Style+Comp": ...}
walk.simple(ast, {
  Property(p) { if (!p.computed && isStr(p.key)) emit(p.key.value, "str", p.key, "key"); },
});
process.stdout.write(JSON.stringify(out));
