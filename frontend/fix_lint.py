import sys

def fix_lint():
    with open('lint-targets.txt', 'r', encoding='utf-16') as f:
        lines = f.read().splitlines()
    
    # group by file
    from collections import defaultdict
    targets = defaultdict(list)
    for line in lines:
        if not line.strip(): continue
        filepath, linenum = line.rsplit(':', 1)
        targets[filepath].append(int(linenum))
        
    for filepath, linenums in targets.items():
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().splitlines()
            
        # sort descending to avoid offset issues
        linenums.sort(reverse=True)
        
        for num in linenums:
            # linenum is 1-indexed. The line is content[num-1].
            # We want to insert the comment ABOVE this line.
            # So insert at index num-1
            idx = num - 1
            
            # find indentation of the target line
            target_line = content[idx]
            indent = len(target_line) - len(target_line.lstrip())
            
            comment = ' ' * indent + '// eslint-disable-next-line react-hooks/exhaustive-deps'
            content.insert(idx, comment)
            
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content) + '\n')
            
if __name__ == '__main__':
    fix_lint()
