const fs = require('fs');
const newQ = JSON.parse(fs.readFileSync('/Users/lucien/ZCodeProject/clean_new_questions.json', 'utf8'));
const html = fs.readFileSync('/Users/lucien/ZCodeProject/chinese-history-quiz.html', 'utf8');

// First, undo any previous bad insertions: restore original if needed
// Check if file already has JSON-style "q": entries (bad format)
const hasJsonQ = html.includes('{"q":');
if (hasJsonQ) {
  console.log('File has bad JSON-style entries from previous run, need clean original');
  console.log('Please restore original file first');
  process.exit(1);
}

const marker = 'const allQuestions=[';
const startIdx = html.indexOf(marker);
if (startIdx === -1) throw new Error('Cannot find allQuestions');

let depth = 0, inStr = false, strCh = '';
let endIdx = -1;
for (let i = startIdx + marker.length - 1; i < html.length; i++) {
  const c = html[i];
  if (inStr) {
    if (c === '\\') { i++; continue; }
    if (c === strCh) inStr = false;
    continue;
  }
  if (c === '"' || c === "'") { inStr = true; strCh = c; continue; }
  if (c === '[') depth++;
  if (c === ']') {
    depth--;
    if (depth === 0) { endIdx = i; break; }
  }
}
if (endIdx === -1) throw new Error('Cannot find end of allQuestions');

const existingContent = html.substring(startIdx + marker.length, endIdx).trim();
const existingCount = (existingContent.match(/\{q:/g) || []).length;
console.log('Existing questions:', existingCount);

// Convert new questions to match existing format: {q:"...",o:[...],a:N,e:"...",ei:"...",t:"..."}
// Without spaces around colons, compact arrays
const newLines = newQ.map(q => {
  const opts = q.o.map(o => '"' + o.replace(/\\/g, '\\\\').replace(/"/g, '\\"') + '"').join(',');
  const txt = q.t.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
  return `{q:"${q.q.replace(/\\/g, '\\\\').replace(/"/g, '\\"')}",o:[${opts}],a:${q.a},e:"${q.e}",ei:"${q.ei}",t:"${txt}"}`;
});

console.log('New questions:', newLines.length);
console.log('Sample:', newLines[0].substring(0, 100));

// Combine
const combined = existingContent + ',\n' + newLines.join(',\n') + '\n';
const beforeArray = html.substring(0, startIdx + marker.length);
const afterArray = html.substring(endIdx); // include the ] character

const newHtml = beforeArray + '\n' + combined + afterArray;

// Verify
const finalOld = (newHtml.match(/\{q:/g) || []).length;
const finalJson = (newHtml.match(/\{"q":/g) || []).length;
console.log('Final old-style questions:', finalOld);
console.log('Final JSON-style questions:', finalJson);
console.log('Total:', finalOld + finalJson);

fs.writeFileSync('/Users/lucien/ZCodeProject/chinese-history-quiz.html', newHtml);
console.log('File written. Lines:', newHtml.split('\n').length);
