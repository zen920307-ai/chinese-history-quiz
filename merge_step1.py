#!/usr/bin/env python3
"""Step 1: Extract questions from batch files, clean, rebalance"""
import re, json, random, subprocess

random.seed(42)

extract_js = """
const fs = require('fs');
const allQ = [];
for (let i = 1; i <= 5; i++) {
    const code = fs.readFileSync(`/Users/lucien/ZCodeProject/gen_batch${i}.js`, 'utf8');
    const fn = new Function(code + `
        const arr = [];
        if(typeof gen_preqin !== 'undefined') arr.push(...gen_preqin);
        if(typeof gen_qinhan !== 'undefined') arr.push(...gen_qinhan);
        if(typeof gen_threej !== 'undefined') arr.push(...gen_threej);
        if(typeof gen_suitang !== 'undefined') arr.push(...gen_suitang);
        if(typeof gen_song !== 'undefined') arr.push(...gen_song);
        if(typeof gen_yuan !== 'undefined') arr.push(...gen_yuan);
        if(typeof gen_ming !== 'undefined') arr.push(...gen_ming);
        if(typeof gen_qing !== 'undefined') arr.push(...gen_qing);
        if(typeof gen_modern !== 'undefined') arr.push(...gen_modern);
        return arr;
    `);
    allQ.push(...fn());
}
console.log(JSON.stringify(allQ));
"""

result = subprocess.run(['node', '-e', extract_js], capture_output=True, text=True)
all_new = json.loads(result.stdout)
print(f"Extracted: {len(all_new)} new questions")

# Clean options
def clean_option(opt):
    opt = re.sub(r'[（(][^）)]*[）)]', '', opt)
    opt = re.sub(r'参考[:：][^，。]*', '', opt)
    return opt.strip() or opt

for q in all_new:
    q['o'] = [clean_option(o) for o in q['o']]

# Rebalance by era
from collections import defaultdict
by_era = defaultdict(list)
for q in all_new:
    by_era[q['ei']].append(q)

for era, qs in by_era.items():
    n = len(qs)
    assignment = []
    for a in range(4):
        assignment.extend([a] * (n // 4 + (1 if a < n % 4 else 0)))
    random.shuffle(assignment)
    for idx, q in enumerate(qs):
        old_a, new_a = q['a'], assignment[idx]
        if old_a != new_a:
            q['o'][old_a], q['o'][new_a] = q['o'][new_a], q['o'][old_a]
            q['a'] = new_a

dist = [0,0,0,0]
for q in all_new: dist[q['a']] += 1
print(f"Distribution: A={dist[0]} B={dist[1]} C={dist[2]} D={dist[3]}")

# Save cleaned questions
with open('/Users/lucien/ZCodeProject/clean_new_questions.json', 'w') as f:
    json.dump(all_new, f, ensure_ascii=False)
print("Saved cleaned questions to clean_new_questions.json")
