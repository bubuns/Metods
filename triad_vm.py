"""Независимое исполнение триад для проверки генератора."""
import json
def execute(triads, name='main', args=()):
    funcs={t[1]:i for i,t in enumerate(triads) if t[0]=='FUNC'}
    labels={t[1]:i for i,t in enumerate(triads) if t[0]=='LABEL'}
    values={};refs={};pending=[];pc=funcs[name]+1;steps=0
    def val(x):
        if x.startswith('^'):return refs[int(x[1:])]
        if x in values:return values[x]
        if x=='true':return True
        if x=='false':return False
        if x.startswith('"'):return json.loads(x)
        if '.' in x:return float(x)
        return int(x)
    while True:
        steps+=1
        
        if steps >= 10000:
            raise RuntimeError('Превышен лимит 10000 шагов')
        op,a,b=triads[pc];number=pc+1;pc+=1
        if op=='ARG':values[a]=args[int(b)]
        elif op==':=':values[a]=val(b)
        elif op=='LABEL':pass
        elif op=='JMP':pc=labels[a[1:]]
        elif op in {'JF','JT'}:
            if bool(val(a))==(op=='JT'):pc=labels[b[1:]]
        elif op=='PARAM':pending.append(val(a))
        elif op=='CALL':refs[number]=execute(triads,a,tuple(pending));pending=[]
        elif op=='RET':return val(a)
        elif op in {'I2D','NEG','POS','NOT'}:
            x=val(a);refs[number]={'I2D':lambda:float(x),'NEG':lambda:-x,
                'POS':lambda:+x,'NOT':lambda:not x}[op]()
        else:
            x,y=val(a),val(b)
            refs[number]={'+':lambda:x+y,'-':lambda:x-y,'*':lambda:x*y,
                '/':lambda:((abs(x)//abs(y)) * (-1 if (x<0)!=(y<0) else 1)) if type(x)==type(y)==int else x/y,
                '<':lambda:x<y,'<=':lambda:x<=y,'>':lambda:x>y,
                '>=':lambda:x>=y,'==':lambda:x==y,'!=':lambda:x!=y}[op]()


if __name__ == '__main__':
    import argparse
    from pathlib import Path
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('file', type=Path)
    a = p.parse_args()
    result = execute(json.loads(a.file.read_text(encoding='utf-8')))
    print(f'Результат main: {result}')
