"""An instance rendered: X across the SFO, dated, with the framework carried.

No evidence, no correspondence, no selection. Every key of the SFO appears,
whether or not anything was ever found near it in any instance.
"""

from __future__ import annotations

from fractions import Fraction as F
from pathlib import Path

from .core import date_of, expression, tnldy, year_of, ztp_of
from .sfo import SFO

WEB = Path(__file__).resolve().parent.parent / "web"


def esc(text) -> str:
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def build(y="0", title: str | None = None, out: str | Path | None = None) -> Path:
    sfo = SFO()
    name = title or f"Y = {y}"
    rows = []
    for x in sfo.order:
        key = sfo.keys[x]
        when = date_of(y, x)
        t = tnldy(y, x)
        nxt = sfo.default_edge(x)
        rows.append(
            '<article class="row">'
            f'<div class="rail"><span class="x">{x}</span>'
            f'<span class="d">{when.date().isoformat()}</span>'
            f'<span class="t">TNLDY {float(t):,.0f}</span></div>'
            '<div class="body">'
            + ("".join(f'<span class="s">{esc(p)}</span>' for p in key.strands)
               if key.strands else
               ("".join(f'<span class="s c">{esc(p)}</span>' for p in key.carried)
                + f'<span class="cf">carried from {key.carried_from}'
                  f' · {key.gap_to_carrier:+g} in position</span>'
                if key.carried else
                '<span class="none">no framework at or before this key</span>'))
            + (f'<span class="n">→ {nxt.target}'
               + ('' if nxt.stated else ' · not written down') + '</span>'
               if nxt else '<span class="n">sink</span>')
            + "</div></article>"
        )
    lo, hi = sfo.span
    html = f"""<title>REVOTT {esc(name)}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500&display=swap">
<style>
:root{{--g:#f2f3f1;--s:#fff;--i:#15181a;--i2:#525a60;--i3:#848d93;--r:#dadedc;--a:#356b4f;
 --m:'IBM Plex Mono',ui-monospace,monospace;--f:'IBM Plex Sans',system-ui,sans-serif}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--g:#0e1211;--s:#141917;
 --i:#e7ebe8;--i2:#a0aaa4;--i3:#6f7a75;--r:#242c29;--a:#6fd3a0}}}}
:root[data-theme="dark"]{{--g:#0e1211;--s:#141917;--i:#e7ebe8;--i2:#a0aaa4;--i3:#6f7a75;
 --r:#242c29;--a:#6fd3a0}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--g);color:var(--i);font-family:var(--f);font-size:15px}}
.w{{max-width:800px;margin:0 auto;padding-inline:16px;padding-block:34px 60px}}
h1{{font-family:var(--m);font-weight:500;font-size:clamp(19px,4.6vw,27px);margin:0 0 5px}}
.sub{{font-family:var(--m);font-size:11.5px;letter-spacing:.05em;text-transform:uppercase;
 color:var(--i3);margin-bottom:20px}}
.box{{background:var(--s);border:1px solid var(--r);border-radius:4px;padding:13px 14px;
 font-family:var(--m);font-size:11.5px;color:var(--i2);line-height:1.8;overflow-x:auto}}
.box b{{color:var(--a);font-weight:500}}
.box .e{{display:block;white-space:nowrap;color:var(--i);margin-bottom:7px}}
.f{{display:flex;flex-wrap:wrap;border:1px solid var(--r);border-radius:4px;background:var(--s);
 margin-top:16px;overflow:hidden}}
.f>div{{flex:1 1 118px;padding:11px 13px;border-right:1px solid var(--r)}}
.f>div:last-child{{border-right:0}}
.f b{{display:block;font-family:var(--m);font-size:16px;font-weight:500;font-variant-numeric:tabular-nums}}
.f span{{font-size:11px;color:var(--i3)}}
input{{width:100%;margin-top:20px;font-family:var(--m);font-size:14px;color:var(--i);
 background:var(--s);border:1px solid var(--r);border-radius:3px;padding:9px 11px}}
.c{{font-family:var(--m);font-size:11.5px;color:var(--i3);margin:9px 0 3px}}
.rows{{border-top:1px solid var(--r)}}
.row{{display:grid;grid-template-columns:104px 1fr;border-bottom:1px solid var(--r)}}
.rail{{padding:9px 12px 9px 0;text-align:right;font-family:var(--m);font-size:11.5px;
 font-variant-numeric:tabular-nums;line-height:1.5}}
.rail .x{{display:block;color:var(--i);font-weight:500;font-size:12.5px}}
.rail .d{{display:block;color:var(--i2)}}
.rail .t{{display:block;color:var(--i3);font-size:10px}}
.body{{padding:9px 0 9px 14px;border-left:1px solid var(--r);min-width:0}}
.s{{display:block;font-size:13.5px;line-height:1.5}}
.s+.s{{color:var(--i2);margin-top:2px}}
.none{{display:block;font-size:13px;color:var(--i3);font-style:italic}}
.s.c{{color:var(--i3)}}
.cf{{display:block;font-family:var(--m);font-size:10px;color:var(--i3);margin-top:3px;
 letter-spacing:.03em}}
.n{{display:block;font-family:var(--m);font-size:10.5px;color:var(--a);margin-top:5px}}
.row.zero{{background:var(--s)}}
.row.zero .rail .x{{color:var(--a)}}
footer{{margin-top:24px;color:var(--i3);font-size:12px;line-height:1.65;max-width:66ch}}
</style>
<div class="w">
<h1>REVOTT · {esc(name)}</h1>
<div class="sub">{len(sfo)} keys · X across the SFO · nothing checked</div>
<div class="box">
  <span class="e">{expression(y, 0)}</span>
  TNLDY = 14160 + 100·Y + 100·X &nbsp;·&nbsp; Y = <b>{esc(y)}</b> &nbsp;·&nbsp;
  Ztp = <b>{float(ztp_of(y)):,.0f}</b> TNLDY = <b>{date_of(y, 0).date()}</b><br>
  year = TNLDY × 23/8400 + 1969 + 391/420 &nbsp;·&nbsp; 1 year = 8400/23 = 365.2174 days
</div>
<div class="f">
  <div><b>{len(sfo)}</b><span>keys</span></div>
  <div><b>{date_of(y, lo).date().year}</b><span>first, X {lo}</span></div>
  <div><b>{date_of(y, hi).date().year}</b><span>last, X {hi}</span></div>
  <div><b>{float(ztp_of(y)):,.0f}</b><span>Ztp in TNLDY</span></div>
</div>
<input type="search" id="q" placeholder="filter by X, date, TNLDY or framework text…" autocomplete="off">
<div class="c" id="c"></div>
<div class="rows" id="rows">
{chr(10).join(rows)}
</div>
<footer>
The text on each key is the framework the SFO carries, written in several strands at once. Where a
key carries none of its own, the framework of the last preceding key that does is shown greyed and
marked <em>carried from</em>: that is what stands at the position, and it is never presented as
owned. X is free and continuous; these 400 keys are the structure standing on it, not a list X is confined to.
Y shifts the whole instance by 100 TNLDY per unit off REVOTT's own zero at 14160.<br><br>
No evidence, correspondence or selection is applied here. Every key appears, whether or not
anything was ever found near it in any instance, and nothing on this page claims that anything
happened on any of these days.
</footer>
</div>
<script>
(function(){{
 var rows=[].slice.call(document.querySelectorAll('#rows .row')),c=document.getElementById('c');
 rows.forEach(function(r){{if(r.querySelector('.x').textContent.trim()==='0.0')r.classList.add('zero');}});
 function t(n){{c.textContent=n+' of '+rows.length+' keys';}}
 t(rows.length);
 document.getElementById('q').addEventListener('input',function(){{
  var q=this.value.trim().toLowerCase(),n=0;
  rows.forEach(function(r){{var h=!q||r.textContent.toLowerCase().indexOf(q)!==-1;r.hidden=!h;if(h)n++;}});
  t(n);
 }});
}})();
</script>
"""
    path = Path(out) if out else WEB / f"revott-Y{str(y).replace('.', 'p')}.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path
