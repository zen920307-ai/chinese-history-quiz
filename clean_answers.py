# -*- coding: utf-8 -*-
"""
清洗历史问答题库的"明显答案"问题：
1. 去除选项中的括号注释，保持4个选项公平（避免正确答案独有注释暴露答案）
2. 长度均衡：剥离正确答案中比其他选项明显冗余的修饰
原则：只动选项文本和解释字段，不改变正确答案 a 所指内容。
"""
import re

SRC = '/Users/lucien/ZCodeProject/chinese-history-quiz.html'

with open(SRC, 'r', encoding='utf-8') as f:
    content = f.read()

# 题目对象正则：匹配 {q:"...",o:[...],a:N,e:"...",ei:"...",t:"..."}
Q_RE = re.compile(
    r'\{q:"((?:[^"\\]|\\.)*)",o:\[((?:[^\[\]]|\[[^\]]*\])*)\],a:(\d),e:"((?:[^"\\]|\\.)*)",ei:"((?:[^"\\]|\\.)*)",t:"((?:[^"\\]|\\.)*)"\}'
)
OPT_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')
# 匹配中文/英文括号注释：核心名（注释内容）
PAREN_RE = re.compile(r'[（(]([^（()）]*?)[）)]')

stats = {'paren_cleaned': 0, 'length_balanced': 0, 'total': 0}
samples = []

def clean_opts(opts_str, ans_idx, tip):
    """清洗选项数组，返回 (new_opts_str, new_tip, changed, reasons)"""
    opts = OPT_RE.findall(opts_str)
    if len(opts) != 4:
        return opts_str, tip, False, []
    ans = int(ans_idx)
    reasons = []
    new_opts = list(opts)
    new_tip = tip
    changed = False

    # ---- 步骤1: 括号注释处理 ----
    # 找出哪些选项有括号注释
    has_paren = [bool(PAREN_RE.search(o)) for o in new_opts]
    paren_count = sum(has_paren)
    if paren_count > 0 and paren_count < 4:
        # 只有部分选项有括号注释 -> 这会暴露答案，统一去除括号
        # 收集被移除的注释，追加到解释字段
        removed_notes = []
        for i in range(4):
            if has_paren[i]:
                m = PAREN_RE.search(new_opts[i])
                if m:
                    note = m.group(1).strip()
                    # 只保留有意义的注释（非纯年代数字等会被保留）
                    removed_notes.append(new_opts[i] + '：' + note)
                new_opts[i] = PAREN_RE.sub('', new_opts[i]).strip()
        if removed_notes and ans_idx is not None:
            # 把注释信息追加到解释
            note_text = '；'.join(removed_notes[:2])  # 最多保留2条避免解释过长
            if note_text and note_text not in new_tip:
                new_tip = new_tip.rstrip('。') + '。（参考：' + note_text + '）'
            reasons.append('paren')
            changed = True

    # ---- 步骤2: 长度均衡 ----
    # 只针对正确答案明显最长的情况
    correct = new_opts[ans]
    others = [new_opts[i] for i in range(4) if i != ans]
    other_lens = [len(o) for o in others]
    max_other = max(other_lens) if other_lens else 0
    # 再次检查括号（步骤1可能已处理）
    correct = PAREN_RE.sub('', correct).strip()
    new_opts[ans] = correct

    if len(correct) - max_other >= 3:
        # 正确答案明显更长，尝试精简常见冗余后缀/修饰
        # 规则：去掉末尾的冗余说明性词，如"（即XX）""，亦称XX"等已在括号处理
        # 再处理：剥离结尾"朝""国""帝"等如果其他选项都没有这类后缀且不影响识别
        # 但为安全起见，这里只处理明显的引号内补充说明
        m2 = re.search(r'[，,、].*$', correct)
        if m2 and (len(correct) - len(m2.group(0)) + 1) >= max_other - 1:
            # 去掉逗号后的补充说明
            note_extra = m2.group(0).lstrip('，,、')
            new_opts[ans] = correct[:m2.start()]
            if note_extra and note_extra not in new_tip:
                new_tip = new_tip.rstrip('。') + '。' + note_extra
            reasons.append('length_comma')
            changed = True

    # 重新构建 opts_str
    if changed:
        new_opts_str = '","'.join(new_opts)
        new_opts_str = '"' + new_opts_str + '"'
        return new_opts_str, new_tip, True, reasons
    return opts_str, tip, False, []

def repl(match):
    q_text, opts_str, ans_idx, era, era_id, tip = match.groups()
    stats['total'] += 1
    new_opts_str, new_tip, changed, reasons = clean_opts(opts_str, ans_idx, tip)
    if changed:
        if 'paren' in reasons:
            stats['paren_cleaned'] += 1
        if 'length_comma' in reasons:
            stats['length_balanced'] += 1
        if len(samples) < 12:
            old_opts = OPT_RE.findall(opts_str)
            samples.append({
                'q': q_text[:30],
                'ans': int(ans_idx),
                'old': old_opts,
                'new': OPT_RE.findall(new_opts_str),
                'reasons': reasons,
            })
        return ('{q:"' + q_text + '",o:[' + new_opts_str + '],a:' + ans_idx +
                ',e:"' + era + '",ei:"' + era_id + '",t:"' + new_tip + '"}')
    return match.group(0)

new_content = Q_RE.sub(repl, content)

with open(SRC, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("=== 清洗完成 ===")
print(f"总题目数: {stats['total']}")
print(f"处理括号注释: {stats['paren_cleaned']} 题")
print(f"处理长度冗余: {stats['length_balanced']} 题")
print(f"\n样例（前12个）:")
for i, s in enumerate(samples):
    print(f"\n[{i+1}] {s['q']}... (正确索引{s['ans']}, {','.join(s['reasons'])})")
    print(f"  旧: {s['old']}")
    print(f"  新: {s['new']}")
